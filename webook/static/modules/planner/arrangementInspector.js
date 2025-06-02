import { CollisionsUtil } from "./collisions_util.js";
import { convertObjToFormData } from "./commonLib.js";
import { Dialog, DialogManager } from "./dialog_manager/dialogManager.js";
import { PopulateCreateEventDialogFromCollisionResolution, PopulateCreateSerieDialogFromManifest } from "./form_populating_routines.js";
import { QueryStore } from "./querystore.js";


const MANAGER_NAME = "arrangementInspector"


export class ArrangementInspector {
    constructor () {
        this.dialogManager = this._createDialogManager();
    }

    async inspect( arrangement ) {
        this.dialogManager.setContext({ arrangement: arrangement });
        this.dialogManager.openDialog( "mainDialog" );
    }

    async _getRecurringInfo(arrangementPk) {
        return await fetch(`/arrangement/arrangement/${arrangementPk}/detail`).then( response => response.json() );
    }

    _listenToOrderRoomForSingleEventBtnClick() {
        $('.orderRoomForSingleEventBtn').on('click', (e) => {
            this.dialogManager.setContext({ arrangement: this.dialogManager.context.arrangement, event: { pk: e.currentTarget.value } });
            this.dialogManager.openDialog( "orderRoomForOneEventDialog" );
        })
    }

    _listenToOrderPersonForSingleEventeBtnClick() {
        $('.orderPersonForSingleEventBtn').on('click', (e) => {
            this.dialogManager.setContext({ arrangement: this.dialogManager.context.arrangement, event: { pk: e.currentTarget.value } });
            this.dialogManager.openDialog( "orderPersonForOneEventDialog" );
        })
    }

    _listenToOrderRoomForSerieBtnClick() {
        $('.orderRoomBtn').on('click', (e) => {
            this.dialogManager.setContext({ arrangement: this.dialogManager.context.arrangement, serie: { guid: e.currentTarget.value } });
            this.dialogManager.openDialog( "orderRoomDialog" );
        })
    }

    _listenToOrderPersonForSerieBtnClick() {
        $('.orderPersonBtn').on('click', (e) => {
            this.dialogManager.setContext({ arrangement: this.dialogManager.context.arrangement, serie: { guid: e.currentTarget.value } });
            this.dialogManager.openDialog( "orderPersonDialog" );
        })
    }

    async saveSerieWithCollisionResolutions (serie, csrf_token, arrangement_pk, collision_resolution_map, collision_resolution_behaviour=undefined) {
        if (collision_resolution_behaviour === undefined)
            collision_resolution_behaviour = 0;

        serie.collision_resolution_behaviour = collision_resolution_behaviour;

        debugger;

        let solutionEventFormDatas = [];

        for (let entry of collision_resolution_map) {
            let solution = entry[1].solution;

            if (solution === undefined)
                continue;

            solutionEventFormDatas.push(solution);
        }

        return await Promise.all([
            QueryStore.SaveSerie(serie, csrf_token, arrangement_pk),
            QueryStore.SaveEvents(solutionEventFormDatas, csrf_token),
        ])
    }

    _createDialogManager () {
        return new DialogManager({
            managerName: MANAGER_NAME,
            dialogs: [
                [
                    "mainDialog",
                    new Dialog({
                        dialogElementId: "mainDialog",
                        triggerElementId: "_mainDialog",
                        htmlFabricator: async (context) => {
                            return await this.dialogManager.loadDialogHtml({
                                url: '/arrangement/planner/dialogs/arrangement_information/' + context.arrangement.slug,
                                managerName: MANAGER_NAME,
                                dialogId: 'mainDialog',
                            });
                        },
                        onPreRefresh: (dialog) => {
                            dialog._active_tab = dialog.internalDialogData.currentlyActiveTab;
                        },
                        onDestroy: () => {
                            this.dialogManager.closeAllDialogs(false);
                        },
                        onRenderedCallback: (dialog) => {
                            if (dialog._active_tab !== undefined) {
                                document.getElementById(dialog._active_tab).click();
                                dialog._active_tab = undefined;
                            }

                            this.dialogManager._makeAware();
                            this._listenToOrderPersonForSerieBtnClick();
                            this._listenToOrderRoomForSerieBtnClick();
                            this._listenToOrderRoomForSingleEventBtnClick();
                            this._listenToOrderPersonForSingleEventeBtnClick();

                            document.querySelectorAll('.form-outline').forEach((formOutline) => {
                                new mdb.Input(formOutline).init();
                            });
                        },
                        onSubmit: async (context, details) => {
                            await fetch("/arrangement/planner/dialogs/arrangement_information/" + context.arrangement.slug + "?managerName=arrangementInspector&dialogId=mainDialog", {
                                method: 'POST',
                                body: details.formData,
                                credentials: 'same-origin',
                                headers: {
                                    "X-CSRFToken": details.formData.get("csrfmiddlewaretoken")
                                }
                            })
                            .then(response => response.text())
                            .then(a => {
                                this.dialogManager.reloadDialog("mainDialog");
                            });
                        },
                        onUpdatedCallback: () => { },
                        dialogOptions: { 
                            width: "70%", 
                            height: "100%",
                            // position: "top right",
                            // maxHeight: "",
                            modal: true,
                            dialogClass: 'no-titlebar',
                            // position: "center center",
                        }
                    }),
                ],
                [
                    "selectPlannersDialog",
                    new Dialog({
                        dialogElementId: "selectPlannersDialog",
                        triggerElementId: undefined,
                        triggerByEvent: true,
                        htmlFabricator: async (context) => {
                            let multiple = context.lastTriggererDetails.multiple;
                            if (multiple === undefined)
                                multiple = true
                                
                            return await this.dialogManager.loadDialogHtml({
                                url: '/arrangement/planner/dialogs/order_person',
                                managerName: 'arrangementInspector',
                                dialogId: 'selectPlannersDialog',
                                customParameters: {
                                    multiple: multiple,
                                    recipientDialogId: context.lastTriggererDetails.sendTo,
                                },
                            });
                        },
                        onRenderedCallback: () => { },
                        dialogOptions: { 
                            width: 500,
                            dialogClass: 'no-titlebar',
                        },
                        onUpdatedCallback: ( ) => {
                            this.dialogManager.reloadDialog("mainDialog");
                            this.dialogManager.closeDialog("selectPlannersDialog");
                            toastr.success("Planlegger(e) har blitt lagt til")
                        },
                        onSubmit: (context, details, dialogManager, dialog) => {
                            let formData = new FormData();

                            formData.append("planner_ids", details.selectedBundle.allSelectedEntityIds.map( (x) => x.id ) );
                            formData.append("arrangement_slug", dialog.data.arrangementSlug);

                            fetch('/arrangement/planner/add_planners', {
                                method: 'POST',
                                body: formData,
                                headers: {
                                    "X-CSRFToken": details.csrf_token
                                }
                            });
                        }
                    })
                ],
                [
                    "uploadFilesToArrangementDialog",
                    new Dialog({
                        dialogElementId: "uploadFilesToArrangementDialog",
                        triggerElementId: "mainDialog__uploadFilesBtn",
                        triggerByEvent: true,
                        htmlFabricator: async (context) => {
                            return this.dialogManager.loadDialogHtml({
                                url: '/arrangement/planner/dialogs/upload_files_dialog',
                                managerName: 'arrangementInspector',
                                dialogId: 'uploadFilesToArrangementDialog'
                            });
                        },
                        onRenderedCallback: () => {},
                        onUpdatedCallback: async () => { 
                            this.dialogManager.closeDialog("uploadFilesToArrangementDialog"); 
                            await this.dialogManager.reloadDialog("mainDialog"); 
                            window.MessagesFacility.send( "mainDialog", { tab: "arrangementInfoDialog_tabs_files" }, "moveToTab" );
                        },
                        onSubmit: async (context, details) => {
                            details.formData.append("slug", context.arrangement.slug);
                            await fetch(`/arrangement/arrangement/files/upload`, {
                                method: 'POST',
                                body: details.formData,
                                headers: {
                                    'X-CSRFToken': details.csrf_token
                                }
                            });
                        },
                        dialogOptions: { 
                            width: 400,
                            dialogClass: 'no-titlebar',
                        }
                    })
                ],
                [
                    "uploadFilesToEventSerieDialog",
                    new Dialog({
                        dialogElementId: "uploadFilesToEventSerieDialog",
                        triggerElementId: undefined,
                        triggerByEvent: true,
                        htmlFabricator: async (context) => {
                            return await this.dialogManager.loadDialogHtml({
                                url: '/arrangement/planner/dialogs/upload_files_dialog',
                                managerName: 'arrangementInspector',
                                dialogId: 'uploadFilesToEventSerieDialog',
                            });
                        },
                        onRenderedCallback: () => { console.info("Upload files to event serie dialog rendered") },
                        onUpdatedCallback: async () => { 
                            this.dialogManager.closeDialog("uploadFilesToEventSerieDialog");
                            await this.dialogManager.reloadDialog("mainDialog");

                            window.MessagesFacility.send( "mainDialog", { tab: "arrangementInfoDialog_tabs_files" }, "moveToTab" );
                        },
                        onSubmit: async (context, details) => {
                            details.formData.append("pk", context.lastTriggererDetails.event_serie_pk);
                            await fetch(`/arrangement/eventSerie/${context.lastTriggererDetails.event_serie_pk}/files/upload`, {
                                method: 'POST',
                                body: details.formData,
                                headers: {
                                    'X-CSRFToken': details.csrf_token
                                }
                            });
                        },
                        dialogOptions: { 
                            width: 400,
                            dialogClass: 'no-titlebar',
                        },
                    })
                ],
                [
                    "newTimePlanDialog",
                    new Dialog({
                        triggerElementId: "mainPlannerDialog__newTimePlan",
                        dialogElementId: "newTimePlanDialog",
                        triggerByEvent: true,
                        htmlFabricator: async (context) => {
                            return await this.dialogManager.loadDialogHtml({
                                url: '/arrangement/planner/dialogs/create_serie',
                                dialogId: 'newTimePlanDialog',
                                managerName: 'arrangementInspector',
                                customParameters: {
                                    slug: context.arrangement.slug,
                                    orderRoomDialog: "nestedOrderRoomDialog",
                                    orderPersonDialog: "nestedOrderPersonDialog",
                                }
                            })
                        },
                        onRenderedCallback: async (dialogManager, context) => {
                            let info = await this._getRecurringInfo( context.arrangement.arrangement_pk );

                            let $newTimePlanDialog = this.dialogManager.$getDialogElement("newTimePlanDialog");
                            [
                                { targetSelector: '#countySelect', value: info.county },
                                { targetSelector: '#initialSchoolValue', value: info.school },
                                { targetSelector: '#serie_title', value: info.title },
                                { targetSelector: '#serie_title_en', value: info.title_en },
                                { targetSelector: '#serie_ticket_code', value: info.ticket_code },
                                { targetSelector: '#serie_expected_visitors', value: info.expected_visitors },
                                { targetSelector: '#_backingAudienceId', value: info.audience_id },
                                { targetSelector: '#_backingArrangementTypeId', value: info.arrangement_type_id },
                                { targetSelector: '#id_status', value: info.status_id },
                                { targetSelector: '#id_display_text', value: info.display_text },
                                { targetSelector: '#id_display_text_en', value: info.display_text_en },
                                { targetSelector: '#id_responsible', value: info.responsible_id },
                                { targetSelector: '#id_meeting_place', value: info.meeting_place     },
                                { targetSelector: '#id_meeting_place_en', value: info.meeting_place_en },
                            ].forEach( (mapping) => {
                                $newTimePlanDialog.find( mapping.targetSelector ).val( mapping.value );
                            } );

                            window.MessagesFacility.send("newTimePlanDialog", info.arrangement_type_id, "setArrangementTypeFromParent")
                            window.MessagesFacility.send("newTimePlanDialog", info.audience_id, "setAudienceFromParent");
                            window.MessagesFacility.send("newTimePlanDialog", info.status_id, "setStatusFromParent");
                            window.MessagesFacility.send("newTimePlanDialog", info.responsible, "setPlanner");
                            window.MessagesFacility.send("newTimePlanDialog", info.school, "setSchoolFromParent");
                            window.MessagesFacility.send("newTimePlanDialog", info.county, "setCountyFromParent");

                            info.display_layouts.forEach(display_layout => {
                                $newTimePlanDialog.find('#id_display_layouts_serie_planner_' + ( display_layout - 1))
                                    .prop( "checked", true );
                            });

                            document.querySelectorAll('.form-outline').forEach((formOutline) => {
                                new mdb.Input(formOutline).init();
                            });
                        },
                        onUpdatedCallback: async () => {
                            this.dialogManager.closeDialog("newTimePlanDialog");

                            await this.dialogManager.reloadDialog("mainDialog");
                            window.MessagesFacility.send( "mainDialog", { tab: "arrangementInfoDialog_tabs_timeslots" }, "moveToTab" );
                        },
                        dialogOptions: { 
                            width: 700,
                            dialogClass: 'no-titlebar',
                        },
                        onSubmit: async (context, details) => {
                            details.serie._uuid = crypto.randomUUID();

                            context.serie = details.serie;
                            context.collision_resolution = new Map();

                            let isInCollisionResolutionState = await CollisionsUtil.FireCollisionsSwal(
                                details.serie,
                                context.collision_resolution,
                                details.csrf_token,
                                "arrangementInspector.breakOutActivityDialog.trigger",
                                context.arrangement.arrangement_pk,
                                this.saveSerieWithCollisionResolutions,
                                () => { this.dialogManager.closeDialog("newTimePlanDialog") }
                            );

                            if (isInCollisionResolutionState) {
                                context.active_collision_route_parent_dialog_id = "newTimePlanDialog";
                                return false;
                            }

                            QueryStore.SaveSerie(details.serie, details.csrf_token, context.arrangement.arrangement_pk).then(_ => {
                                document.dispatchEvent(new Event("plannerCalendar.refreshNeeded"));
                            });
                        }
                    })
                ],
                [
                    "breakOutActivityDialog",
                    new Dialog({
                        dialogElementId: "breakOutActivityDialog",
                        triggerElementId: "breakOutActivityDialog",
                        triggerByEvent: true,
                        htmlFabricator: async (context) => {
                            return this.dialogManager.loadDialogHtml({
                                url: "/arrangement/planner/dialogs/create_simple_event",
                                managerName: "arrangementInspector",
                                dialogId: "breakOutActivityDialog",
                                customParameters: {
                                    slug: 0,
                                    orderPersonDialog: "orderPersonDialog",
                                    orderRoomDialog: "orderRoomForLocalEventDialog",
                                }
                            });
                        },
                        onRenderedCallback: (dialogManager, context) => {
                            /*
                                LastTriggererDetails is set when the dialog is called for, and not available
                                in the subsequent callbacks versions of the context. We need to access this in
                                the OnSubmit callback so we set it as such. It might be more correct in the long
                                run to make this remembered for the entire lifetime of the dialog instance, as to avoid
                                these kinds of things.
                            */
                            context._lastTriggererDetails = context.lastTriggererDetails;
                            context._lastTriggererDetails.serie = context.serie;
                            let serie = context.serie;

                            let collision_uuid = context._lastTriggererDetails.collision_uuid;
                            let resolution_bundle = context.collision_resolution.get(collision_uuid);
                            let collision_record = resolution_bundle.collision;
                            
                            let $breakOutActivityDialog = this.dialogManager.$getDialogElement("breakOutActivityDialog");

                            PopulateCreateEventDialogFromCollisionResolution(
                                $breakOutActivityDialog,
                                "breakOutActivityDialog",
                                collision_record,
                                serie
                            );

                            $breakOutActivityDialog.find('#event_uuid').val(crypto.randomUUID());
                            document.querySelectorAll('.form-outline').forEach((formOutline) => {
                                new mdb.Input(formOutline).init();
                            });

                            this.dialogManager.setTitle("breakOutActivityDialog", "Bryt ut aktivitet");
                        },
                        onUpdatedCallback: async (context) => {
                        },
                        onSubmit: async (context, details) => {
                            context.csrf_token = details.csrf_token;

                            if (context.events === undefined) {
                                context.events = new Map();
                            }
                            if (details.event._uuid === undefined) {
                                details.event._uuid = crypto.randomUUID();
                            }

                            details.event.is_resolution = true;
                            details.event.associated_serie_internal_uuid = context._lastTriggererDetails.serie._uuid;

                            let collision_state = context.collision_resolution.get(context._lastTriggererDetails.collision_uuid);

                            details.event.fromDate = new Date(details.event.start).toISOString();
                            details.event.toDate = new Date(details.event.end).toISOString();
                            details.event.arrangement = context.arrangement.arrangement_pk;

                            let formData = new FormData();
                            for (let key in details.event) {
                                formData.append(key, details.event[key])
                            }

                            let collisions_on_solution = await CollisionsUtil.GetCollisionsForEvent(formData, details.csrf_token);

                            if (collisions_on_solution.length > 0) {
                                CollisionsUtil.FireOneToOneCollisionWarningSwal(collisions_on_solution[0])
                                    .then(async (_) => {
                                        await CollisionsUtil.FireCollisionsSwal(
                                            context.serie,
                                            context.collision_resolution,
                                            context.csrf_token,
                                            "arrangementInspector.breakOutActivityDialog.trigger",
                                            context.arrangement.arrangement_pk,
                                            this.saveSerieWithCollisionResolutions,
                                            () => { this.dialogManager.closeDialog(context.active_collision_route_parent_dialog_id); }
                                        )
                                        this.dialogManager.closeDialog("breakOutActivityDialog");
                                    });

                                return false;
                            }

                            collision_state.collision.is_resolved = true;
                            collision_state.solution = details.event;

                            await CollisionsUtil.FireCollisionsSwal(
                                context.serie,
                                context.collision_resolution,
                                context.csrf_token,
                                "arrangementInspector.breakOutActivityDialog.trigger",
                                context.arrangement.arrangement_pk,
                                this.saveSerieWithCollisionResolutions,
                                () => { this.dialogManager.closeDialog(context.active_collision_route_parent_dialog_id); }
                            )

                            this.dialogManager.closeDialog("breakOutActivityDialog");

                            document.dispatchEvent(new CustomEvent(this.dialogManager.managerName + ".contextUpdated", { detail: { context: context } }))
                        },
                        dialogOptions: { width: 700, dialogClass: 'no-titlebar' }
                    })
                ],
                [
                    "newSimpleActivityDialog",
                    new Dialog({
                        dialogElementId: "newSimpleActivityDialog",
                        triggerElementId: "mainPlannerDialog__newSimpleActivity",
                        triggerByEvent: true,
                        htmlFabricator: async (context) => {
                            return this.dialogManager.loadDialogHtml({
                                url: "/arrangement/planner/dialogs/create_simple_event",
                                dialogId: "newSimpleActivityDialog",
                                managerName: "arrangementInspector",
                                customParameters: {
                                    slug: context.arrangement.slug,
                                    orderRoomDialog: "nestedOrderRoomDialog",
                                    orderPersonDialog: "nestedOrderPersonDialog",
                                }
                            });
                        },
                        onRenderedCallback: async (dialogManager, context) => {
                            let info = await this._getRecurringInfo( context.arrangement.arrangement_pk );
                            const dialogId = "newSimpleActivityDialog";
                            this.dialogManager.setTitle("newSimpleActivityDialog", "Opprett aktivitet");
                            let $newSimpleActivityDialog = this.dialogManager.$getDialogElement("newSimpleActivityDialog");

                            [
                                { targetSelector: '#countySelect', value: info.county },
                                { targetSelector: '#initialSchoolValue', value: info.school },
                                { targetSelector: '#title', value: info.title },
                                { targetSelector: '#title_en', value: info.title_en },
                                { targetSelector: '#ticket_code', value: info.ticket_code },
                                { targetSelector: '#expected_visitors', value: info.expected_visitors },
                                { targetSelector: '#id_display_text', value: info.display_text },
                                { targetSelector: '#id_display_text_en', value: info.display_text_en },
                                { targetSelector: '#id_responsible', value: info.responsible_id },
                                { targetSelector: '#id_meeting_place', value: info.meeting_place },
                                { targetSelector: '#id_meeting_place_en', value: info.meeting_place_en },
                                { targetSelector: '#_statusTypeId', value: info.status_id },
                                { targetSelector: '#_backingAudienceId', value: info.audience_id },
                                { targetSelector: '#_backingArrangementTypeId', value: info.arrangement_type_id },

                            ].forEach( (mapping) => {
                                $newSimpleActivityDialog.find( mapping.targetSelector ).val( mapping.value );
                            } );

                            window.MessagesFacility.send(dialogId, info.arrangement_type_id, "setArrangementTypeFromParent")
                            window.MessagesFacility.send(dialogId, info.audience_id, "setAudienceFromParent");
                            window.MessagesFacility.send(dialogId, info.status_id, "setStatusFromParent");
                            window.MessagesFacility.send(dialogId, info.responsible, "setPlanner");
                            window.MessagesFacility.send(dialogId, info.county, "setCountyFromParent");
                            window.MessagesFacility.send(dialogId, info.school, "setSchoolFromParent");

                            info.display_layouts.forEach(display_layout => {
                                $newSimpleActivityDialog.find('#' + display_layout + "_dlcheck")
                                    .prop("checked", true).change();
                            });

                            document.querySelectorAll('.form-outline').forEach((formOutline) => {
                                new mdb.Input(formOutline).init();
                            });
                        },
                        onUpdatedCallback: async () => {
                            this.dialogManager.closeDialog("newSimpleActivityDialog");

                            await this.dialogManager.reloadDialog("mainDialog");
                            window.MessagesFacility.send( "mainDialog", { tab: "arrangementInfoDialog_tabs_timeslots" }, "moveToTab" );
                        },
                        dialogOptions: { width: "30%", dialogClass: 'no-titlebar', modal: true },
                        onSubmit: async (context, details) => {
                            details.event.startDate = (new Date(details.event.start)).toISOString();
                            details.event.endDate = (new Date(details.event.end)).toISOString();
                            details.event.fromDate = details.event.startDate;
                            details.event.toDate = details.event.endDate;
                            details.event.arrangement = context.arrangement.arrangement_pk;
                            details.event.id = 0;

                            details.event.collisions = await CollisionsUtil.GetCollisionsForEvent(convertObjToFormData(details.event), details.csrf_token);

                            if (details.event.collisions.length > 0) {
                                CollisionsUtil.FireOneToOneCollisionWarningSwal(details.event.collisions[0]);
                                return false;
                            }

                            QueryStore.SaveEvents([ details.event ], details.csrf_token).then(_ => {
                                document.dispatchEvent(new Event("plannerCalendar.refreshNeeded"));
                            })
                        }
                    })
                ],
                [
                    "editEventSerieDialog",
                    new Dialog({
                        dialogElementId: "editEventSerieDialog",
                        customTriggerName: "editEventSerieDialog",
                        triggerElementId: undefined,
                        triggerByEvent: true,
                        htmlFabricator: async (context) => {
                            return this.dialogManager.loadDialogHtml({
                                url: '/arrangement/planner/dialogs/create_serie',
                                managerName: "arrangementInspector",
                                dialogId: 'editEventSerieDialog',
                                customParameters: {
                                    orderRoomDialog: 'nestedOrderRoomDialog',
                                    orderPersonDialog: 'nestedOrderPersonDialog',
                                    serieId: context.lastTriggererDetails.event_serie_pk,
                                }
                            });
                        },
                        onRenderedCallback: async (dialogManager, context) => {
                            context.editing_serie_pk = context.lastTriggererDetails.event_serie_pk

                            let $dialogElement = $(this.dialogManager.$getDialogElement("editEventSerieDialog"));
                            let manifest = await QueryStore.GetSerieManifest(context.editing_serie_pk);
                            
                            PopulateCreateSerieDialogFromManifest(manifest, context.editing_serie_pk, $dialogElement, "editEventSerieDialog");

                            document.querySelectorAll('.form-outline').forEach((formOutline) => {
                                new mdb.Input(formOutline).init();
                            });
                        },
                        onUpdatedCallback: async () => {
                            this.dialogManager.closeDialog("editEventSerieDialog");

                            await this.dialogManager.reloadDialog("mainDialog");
                            window.MessagesFacility.send( "mainDialog", { tab: "arrangementInfoDialog_tabs_timeslots" }, "moveToTab" );                            
                        },
                        onSubmit: async (context, details) => {
                            details.serie.event_serie_pk = context.editing_serie_pk;

                            context.serie = details.serie;
                            context.collision_resolution = new Map();

                            let isInCollisionResolutionState = await CollisionsUtil.FireCollisionsSwal(
                                details.serie,
                                context.collision_resolution,
                                details.csrf_token,
                                "arrangementInspector.breakOutActivityDialog.trigger",
                                context.arrangement.arrangement_pk,
                                this.saveSerieWithCollisionResolutions,
                                () => { this.dialogManager.closeDialog("editEventSerieDialog"); },
                            );

                            if (isInCollisionResolutionState) {
                                context.active_collision_route_parent_dialog_id = "editEventSerieDialog";
                                return false;
                            }

                            return QueryStore.SaveSerie(details.serie, details.csrf_token, context.arrangement.arrangement_pk).then(_ => {
                                document.dispatchEvent(new Event("plannerCalendar.refreshNeeded"));
                            });
                        },
                        dialogOptions: { 
                            width: 700,
                            dialogClass: 'no-titlebar',
                        }
                    })
                ],
                [
                    "calendarFormDialog",
                    new Dialog({
                        dialogElementId: "calendarFormDialog",
                        triggerElementId: "mainPlannerDialog__showInCalendarForm",
                        htmlFabricator: async (context) => {
                            return await fetch('/arrangement/planner/dialogs/arrangement_calendar_planner/' + context.arrangement.slug + "&managerName=" + MANAGER_NAME)
                                    .then(response => response.text())
                        },
                        onRenderedCallback: () => { console.info("Rendered") },
                        onUpdatedCallback: () => { return false; },
                        dialogOptions: { width: 1200, height: 700 }
                    })
                ],
                [
                    "promotePlannerDialog",
                    new Dialog({
                        dialogElementId: "promotePlannerDialog",
                        triggerElementId: "mainPlannerDialog__promotePlannerBtn",
                        htmlFabricator: async (context) => {
                            return await this.dialogManager.loadDialogHtml({
                                url: '/arrangement/planner/dialogs/promote_main_planner',
                                managerName: 'arrangementInspector',
                                dialogId: 'promotePlannerDialog',
                                customParameters: {
                                    slug: context.arrangement.slug,
                                }
                            });
                        },
                        onRenderedCallback: () => { console.info("Rendered") },
                        onUpdatedCallback: () => {
                            this.dialogManager.reloadDialog("mainDialog");
                            this.dialogManager.closeDialog("promotePlannerDialog");
                        },
                        onSubmit: async (context, details) => {
                            await fetch("/arrangement/arrangement/promote_to_main", {
                                method: 'POST',
                                body: Utils.convertObjToFormData(details),
                                credentials: 'same-origin',
                                headers: {
                                    'X-CSRFToken': details.csrf_token
                                }
                            });
                        },
                        dialogOptions: { width: 500, dialogClass: 'no-titlebar'  },
                    })
                ],
                [
                    "newNoteDialog",
                    new Dialog({
                        dialogElementId: "newNoteDialog",
                        triggerElementId: "mainPlannerDialog__newNoteBtn",
                        triggerByEvent: true,
                        htmlFabricator: async (context) => {
                            return await this.dialogManager.loadDialogHtml(
                                {
                                    url: '/arrangement/planner/dialogs/new_note',
                                    managerName: 'arrangementInspector',
                                    dialogId: 'newNoteDialog',
                                    customParameters: {
                                        slug: context.arrangement.slug,
                                        entityType: 'arrangement',
                                    }
                                }
                            )
                        },
                        onRenderedCallback: () => { console.info("Rendered") },
                        onUpdatedCallback: async () => {
                            this.dialogManager.closeDialog("newNoteDialog");
                            await this.dialogManager.reloadDialog("mainDialog");
                            
                            window.MessagesFacility.send( "mainDialog", { tab: "arrangementInfoDialog_tabs_notes" }, "moveToTab" );
                        },
                        onSubmit: async (context, details) => {
                            await fetch('/arrangement/note/post', {
                                method: 'POST',
                                body: Utils.convertObjToFormData(details),
                                credentials: 'same-origin',
                                headers: {
                                    "X-CSRFToken": details.csrf_token
                                }
                            }).then(response => {
                                if (!response.ok) {
                                    toast.error("Noe gikk galt, prøv igjen senere");
                                }
                            })
                        },
                        dialogOptions: { width: 500, dialogClass: 'no-titlebar' },
                    })
                ],
                [
                    "editNoteDialog",
                    new Dialog({
                        dialogElementId: "editNoteDialog",
                        triggerElementId: undefined,
                        triggerByEvent: true,
                        htmlFabricator: async (context) => {
                            return await this.dialogManager.loadDialogHtml({
                                url: "/arrangement/planner/dialogs/edit_note/" + context.lastTriggererDetails.note_pk,
                                managerName: "arrangementInspector",
                                dialogId: "editNoteDialog",
                            });
                        },
                        onRenderedCallback: () => { console.info("Rendered"); },
                        onUpdatedCallback: async () => {
                            this.dialogManager.closeDialog("editNoteDialog");
                            await this.dialogManager.reloadDialog("mainDialog");
                            
                            window.MessagesFacility.send( "mainDialog", { tab: "arrangementInfoDialog_tabs_notes" }, "moveToTab" );
                        },
                        onSubmit: async (context, details) => {
                            await fetch('/arrangement/planner/dialogs/edit_note/' + details.id, {
                                method: 'POST',
                                body: Utils.convertObjToFormData(details), 
                                headers: {
                                    'X-CSRFToken': details.csrf_token,
                                }
                            })
                        },
                        dialogOptions: { 
                            width: 500,
                            dialogClass: 'no-titlebar',
                        },
                    })
                ],
                [
                    "orderPersonDialog",
                    new Dialog({
                        dialogElementId: "orderPersonDialog",
                        triggerElementId: undefined,
                        triggerByEvent: true,
                        htmlFabricator: async (context) => {
                            return await this.dialogManager.loadDialogHtml({
                                url: '/arrangement/planner/dialogs/order_person',
                                dialogId: 'orderPersonDialog',
                                managerName: 'arrangementInspector',
                                customParameters: {
                                    event_pk: 0,
                                    mode: context.lastTriggererDetails.mode,
                                }
                            });
                        },
                        onRenderedCallback: () => { this.dialogManager._makeAware(); },
                        dialogOptions: { width: 500, dialogClass: 'no-titlebar', },
                        onSubmit: async (context, details) => {
                            fetch("/arrangement/planner/dialogs/order_people_form", {
                                method: "POST",
                                body: details.formData,
                                headers: {
                                    "X-CSRFToken": details.csrf_token
                                }
                            }).then(_ => {
                                this.dialogManager.reloadDialog("mainDialog");
                                this.dialogManager.closeDialog("orderPersonDialog");
                            });
                        }
                    })
                ],
                [
                    "orderRoomDialog",
                    new Dialog({
                        dialogElementId: "orderRoomDialog",
                        triggerElementId: undefined,
                        triggerByEvent: true,
                        htmlFabricator: async (context) => {
                            return await this.dialogManager.loadDialogHtml({
                                url: '/arrangement/planner/dialogs/order_room',
                                managerName: 'arrangementInspector',
                                dialogId: 'orderRoomDialog',
                                customParameters: {
                                    event_pk: 0,
                                    recipientDialogId: context.lastTriggererDetails.sendTo,
                                }
                            });
                        },
                        onRenderedCallback: () => { this.dialogManager._makeAware(); },
                        dialogOptions: { width: 500, dialogClass: 'no-titlebar', },
                        onUpdatedCallback: () => {
                            this.dialogManager.reloadDialog("mainDialog");
                            this.dialogManager.closeDialog("orderRoomDialog");
                        },
                        onSubmit: async (context, details) => {
                            fetch("/arrangement/planner/dialogs/order_rooms_form", {
                                method: "POST",
                                body: details.formData,
                                headers: {
                                    "X-CSRFToken": details.csrf_token
                                }
                            }).then(_ => {
                                this.dialogManager.reloadDialog("mainDialog");
                                this.dialogManager.closeDialog("orderRoomDialog");
                            });
                        }
                    })
                ],
                [
                    "orderRoomForLocalEventDialog",
                    new Dialog({
                        dialogElementId: "orderRoomForLocalEventDialog",
                        triggerElementId: undefined,
                        triggerByEvent: true,
                        htmlFabricator: async (context) => {
                            return await fetch(`/arrangement/planner/dialogs/order_room?event_pk=0&manager=${MANAGER_NAME}&dialog=orderRoomForLocalEventDialog`)
                                .then(response => response.text());
                        },
                        onRenderedCallback: () => {},
                        dialogOptions: { width: 500, dialogClass: 'no-titlebar', },
                        onUpdatedCallback: () => {
                            toastr.success("Rom lagt til");
                            this.dialogManager.closeDialog("orderRoomForLocalEventDialog");
                        },
                        onSubmit: (context, details) => {
                            context.rooms = details.formData.get("room_ids");
                            context.room_name_map = details.room_name_map;

                            document.dispatchEvent(new CustomEvent(
                                `${MANAGER_NAME}.d1_roomsSelected`,
                                { detail: { context: context } }
                            ));
                        }
                    })
                ],
                [
                    "orderRoomForOneEventDialog",
                    new Dialog({
                        dialogElementId: "orderRoomForOneEventDialog",
                        triggerElementId: undefined,
                        triggerByEvent: true,
                        htmlFabricator: async (context) => {
                            return await fetch(`/arrangement/planner/dialogs/order_room?event_pk=${context.event.pk}&manager=arrangementInspector&dialog=orderRoomForOneEventDialog`)
                                .then(response => response.text());
                        },
                        onRenderedCallback: () => { this.dialogManager._makeAware(); },
                        onUpdatedCallback: () => { 
                            this.dialogManager.closeDialog("orderRoomForOneEventDialog");
                            this.dialogManager.reloadDialog("mainDialog"); 
                        },
                        dialogOptions: { width: 500, dialogClass: 'no-titlebar', },
                        onSubmit: async (context, details) => {
                            fetch("/arrangement/planner/dialogs/order_rooms_for_event_form", {
                                method: "POST",
                                body: details.formData,
                                headers: {
                                    "X-CSRFToken": details.csrf_token
                                }
                            }).then(_ => { 
                                this.dialogManager.reloadDialog("mainDialog"); 
                                this.dialogManager.closeDialog("orderRoomForOneEventDialog"); 
                            });
                        }
                    })
                ],
                [
                    "orderPersonForOneEventDialog",
                    new Dialog({
                        dialogElementId: "orderPersonForOneEventDialog",
                        triggerElementId: undefined,
                        triggerByEvent: true,
                        htmlFabricator: async (context) => {
                            return await fetch(`/arrangement/planner/dialogs/order_person?event_pk=${context.event.pk}&manager=arrangementInspector&dialog=orderPersonForOneEventDialog`)
                                .then(response => response.text());
                        },
                        onRenderedCallback: () => { this.dialogManager._makeAware(); },
                        dialogOptions: { width: 500, dialogClass: 'no-titlebar', },
                        onUpdatedCallback: () => { 
                            this.dialogManager.closeDialog("orderPersonForOneEventDialog");
                            this.dialogManager.reloadDialog("mainDialog"); 
                        },
                        onSubmit: async (context, details) => {
                            fetch("/arrangement/planner/dialogs/order_people_for_event_form", {
                                method: "POST",
                                body: details.formData,
                                headers: {
                                    "X-CSRFToken": details.csrf_token
                                }
                            }).then(_ => { 
                                this.dialogManager.reloadDialog("mainDialog"); 
                                this.dialogManager.closeDialog("orderPersonForOneEventDialog"); 
                            });
                        }
                    })
                ],
                [

                    "cascadeTreeDialog",
                    new Dialog({
                        dialogElementId: "cascadeTreeDialog",
                        triggerElementId: undefined,
                        triggerByEvent: true,
                        htmlFabricator: async (context) => {
                            return await this.dialogManager.loadDialogHtml(
                                {
                                    url: '/arrangement/arrangement/' + context.arrangement.arrangement_pk + '/dialogs/cascade_tree',
                                    managerName: 'arrangementInspector',
                                    dialogId: 'cascadeTreeDialog',
                                }
                            )
                        },
                        onRenderedCallback: () => { this.dialogManager._makeAware() },
                        dialogOptions: { 
                            width: "50%",
                            modal: true,
                            dialogClass: 'no-titlebar',
                        },
                        onUpdatedCallback: () => {
                        },
                        onSubmit: async(context, details) => {
                            this.dialogManager.reloadDialog("mainDialog"); 
                        }
                    })
                ],
                [
                    "nestedOrderRoomDialog",
                    new Dialog({
                        dialogElementId: "nestedOrderRoomDialog",
                        triggerElementId: undefined,
                        triggerByEvent: true,
                        htmlFabricator: async (context) => {
                            return await this.dialogManager.loadDialogHtml({
                                url: '/arrangement/planner/dialogs/order_room',
                                managerName: 'arrangementInspector',
                                dialogId: 'nestedOrderRoomDialog',
                                customParameters: {
                                    event_pk: 0,
                                    recipientDialogId: context.lastTriggererDetails.sendTo,
                                }
                            });
                        },
                        onRenderedCallback: (dialogManager, context) => {
                            window.MessagesFacility.send(
                                "nestedOrderRoomDialog",
                                context.lastTriggererDetails.data,
                                "setRoomSelection"
                            );
                        },
                        dialogOptions: { width: 500, dialogClass: 'no-titlebar' },
                        onUpdatedCallback: () => {
                            this.dialogManager.closeDialog("nestedOrderRoomDialog");
                            toastr.success("Rom har blitt lagt til");
                        },
                        onSubmit: (context, details) => {
                            window.MessagesFacility.send(details.recipientDialog, details.selectedBundle, "roomsSelected");
                        }
                    })
                ],
                [
                    "nestedOrderPersonDialog",
                    new Dialog({
                        dialogElementId: "nestedOrderPersonDialog",
                        triggerElementId: undefined,
                        triggerByEvent: true,
                        htmlFabricator: async (context) => {
                            let multiple = context.lastTriggererDetails.multiple;
                            if (multiple === undefined)
                                multiple = true
                                
                            return this.dialogManager.loadDialogHtml({
                                url: '/arrangement/planner/dialogs/order_person',
                                dialogId: 'nestedOrderPersonDialog',
                                managerName: 'arrangementInspector',
                                customParameters: {
                                    event_pk: 0,
                                    recipientDialogId: context.lastTriggererDetails.sendTo,
                                    multiple: multiple,
                                }
                            });
                        },
                        onRenderedCallback: (dialogManager, context) => {
                            window.MessagesFacility.send(
                                "nestedOrderPersonDialog", 
                                context.lastTriggererDetails.data, 
                                "setPersonSelection"
                            );
                        },
                        dialogOptions: { width: 500, dialogClass: 'no-titlebar', },
                        onUpdatedCallback: () => {
                            this.dialogManager.closeDialog("nestedOrderPersonDialog");
                            toastr.success("Personer har blitt lagt til");
                        },
                        onSubmit: (context, details, dialogManager, dialog) => {
                            const eventName = dialog.data.whenEventName || "peopleSelected";
                            window.MessagesFacility.send(details.recipientDialog, details.selectedBundle, eventName);
                        }
                    })
                ],
                [
                    "nestedOrderPersonDialog",
                    new Dialog({
                        dialogElementId: "nestedOrderPersonDialog",
                        triggerElementId: undefined,
                        triggerByEvent: true,
                        htmlFabricator: async (context) => {
                            let multiple = context.lastTriggererDetails.multiple;
                            if (multiple === undefined)
                                multiple = true
                                
                            return this.dialogManager.loadDialogHtml({
                                url: '/arrangement/planner/dialogs/order_person',
                                dialogId: 'nestedOrderPersonDialog',
                                managerName: 'arrangementInspector',
                                customParameters: {
                                    event_pk: 0,
                                    recipientDialogId: context.lastTriggererDetails.sendTo,
                                    multiple: multiple,
                                }
                            });
                        },
                        onRenderedCallback: () => { },
                        dialogOptions: { width: 500, dialogClass: 'no-titlebar', },
                        onUpdatedCallback: () => {
                            this.dialogManager.closeDialog("nestedOrderPersonDialog");
                            toastr.success("Personer har blitt lagt til");
                        },
                        onSubmit: (context, details, dialogManager, dialog) => {
                            const eventName = dialog.data.whenEventName || "peopleSelected";
                            window.MessagesFacility.send(details.recipientDialog, details.selectedBundle, eventName);
                        }
                    })
                ],
                [
                    "orderServiceDialog",
                    new Dialog({
                        dialogElementId: "orderServiceDialog",
                        triggerElementId: undefined,
                        triggerByEvent: true,
                        dialogOptions: { 
                            width: 500,
                            dialogClass: 'no-titlebar',
                        },
                        onRenderedCallback: () => {},
                        htmlFabricator: async (context, dialog) => {
                            if (!context.lastTriggererDetails.entity_type)
                                throw Error("Please supply a valid entity type (either 'event' or 'serie')");
                            if (!context.lastTriggererDetails.entity_id)
                                throw Error("Please supply a valid entity id");

                            return this.dialogManager.loadDialogHtml({
                                url: '/arrangement/planner/dialogs/order_service/' + context.lastTriggererDetails.entity_type + '/' + context.lastTriggererDetails.entity_id,
                                dialogId: 'orderServiceDialog',
                                managerName: 'arrangementInspector',
                                customParameters: {
                                    recipientDialogId: context.lastTriggererDetails.sendTo,
                                }
                            });
                        },
                        onUpdatedCallback: async () => {
                            this.dialogManager.closeDialog("orderServiceDialog");
                        },
                        onSubmit: (context, details, dialogManager, dialog) => {
                            const eventName = dialog.data.whenEventName || "serviceOrdered";
                            window.MessagesFacility.send(details.recipientDialog, details.requestedServices, eventName);
                        }
                    })
                ],
                [
                    "inspectServiceOrderDialog",
                    new Dialog({
                        dialogElementId: "inspectServiceOrderDialog",
                        triggerElementId: undefined,
                        triggerByEvent: true,
                        // plugins: [ new CustomDialogFormInterceptorPlugin("{{csrf_token}}") ],
                        formUrl: '/arrangement/planner/dialogs/inspect_service_order/<<id>>',
                        htmlFabricator: async (context) => {
                            console.log("context", context);

                            return this.dialogManager.loadDialogHtml({
                                url: '/arrangement/planner/dialogs/inspect_service_order/' + context.lastTriggererDetails.order_id,
                                dialogId: "inspectServiceOrderDialog",
                                managerName: "arrangementInspector",
                            })
                        },
                        onRenderedCallback: () => { this.dialogManager._makeAware(); },
                        dialogOptions: { width: "70%", dialogClass: 'no-titlebar' },
                        onUpdatedCallback: async () => {
                            this.dialogManager.closeDialog("inspectServiceOrderDialog");
                            await this.dialogManager.reloadDialog("mainDialog");

                            window.MessagesFacility.send( "mainDialog", { tab: "service-orders-tab" }, "moveToTab" );
                        },
                        onSubmit: (context, details, dialogManager, dialog) => {
                        }
                    })
                ]  
            ]}
        )
    }
}
