import { CollisionsUtil } from "./collisions_util.js";
import { Dialog, DialogManager } from "./dialog_manager/dialogManager.js";
import { PopulateCreateEventDialog, PopulateCreateEventDialogFromCollisionResolution, PopulateCreateSerieDialogFromSerie } from "./form_populating_routines.js";
import { QueryStore } from "./querystore.js";
import { serieConvert } from "./serieConvert.js";
import { SerieMetaTranslator } from "./serie_meta_translator.js";


export class ArrangementCreator {
    constructor () {
        this.dialogManager = new DialogManager({
            managerName: "arrangementCreator",
            renderInChain: true,
            dialogs: [
                [
                    "createArrangementDialog",
                    new Dialog({
                        dialogElementId: "createArrangementDialog",
                        triggerElementId: "_createArrangementDialog",
                        htmlFabricator: async (context) => {
                            return this.dialogManager.loadDialogHtml({
                                url: '/arrangement/planner/dialogs/create_arrangement',
                                dialogId: "createArrangementDialog",
                                managerName: "arrangementCreator",
                                customParameters: {
                                    orderRoomDialog: 'orderRoomDialog',
                                    orderPersonDialog: 'orderPersonDialog',
                                },
                            });
                        },
                        onPreRefresh: (dialog) => {
                            dialog._active_tab = active;
                        },
                        onDestroy: () => {
                            this.dialogManager.closeAllDialogs(false);
                        },
                        onRenderedCallback: (dialog) => {
                            if (this.dialogManager.context.series !== undefined) {
                                this.dialogManager.context.series = new Map();
                            }
                            if (this.dialogManager.context.events !== undefined) {
                                this.dialogManager.context.events = new Map();
                            }

                            this.dialogManager._makeAware();
                        },
                        onSubmit: async (context, details) => {
                            let csrf_token = details.formData.get("csrf_token");

                            let eventSort = ( a, b ) => {
                                if ( a.parent_position_hash ) {
                                  return 1;
                                }
                                else {
                                  return -1;
                                }
                            }

                            await fetch("/arrangement/arrangement/ajax/create", {
                                method: 'POST',
                                body: details.formData,
                                headers: {
                                    "X-CSRFToken": csrf_token
                                },
                                credentials: 'same-origin',
                            }).then(async response => await response.json())
                              .then(async (arrId) => {
                                for (let serie of details.series) {
                                    await QueryStore.SaveSerie(
                                        serie,
                                        csrf_token,
                                        arrId.arrangementPk,
                                    );
                                }
                                
                                if (details.events !== undefined) {
                                    details.events.forEach((event) => event.arrangement = arrId.arrangementPk);
                                    details.events = details.events.sort(eventSort)
                                    await QueryStore.SaveEvents(details.events, csrf_token);
                                }
                              })
                              .then(_ => {
                                document.dispatchEvent(new Event("plannerCalendar.refreshNeeded"));
                              });
                        },
                        onUpdatedCallback: () => {  
                            toastr.success("Arrangement opprettet");
                            this.dialogManager.closeDialog("createArrangementDialog");
                        },
                        dialogOptions: { 
                            width: 900, 
                            height: 800,
                            modal: true,
                            position: "center center",
                            dialogClass: 'no-titlebar',
                        }
                    }),
                ],
                [
                    "newTimePlanDialog",
                    new Dialog({
                        dialogElementId: "newTimePlanDialog",
                        triggerElementId: "createArrangementDialog_createSerie",
                        triggerByEvent: true,
                        htmlFabricator: async (context) => {
                            return await this.dialogManager.loadDialogHtml({
                                url: '/arrangement/planner/dialogs/create_serie',
                                managerName: 'arrangementCreator',
                                dialogId: 'newTimePlanDialog',
                                customParameters: {
                                    orderRoomDialog: 'orderRoomDialog',
                                    orderPersonDialog: 'orderPersonDialog',
                                }
                            })
                        },
                        onRenderedCallback: (dialogManager, context) => {
                            const isCreatingNewTimeplan = context.lastTriggererDetails?.serie_uuid === undefined;

                            if (isCreatingNewTimeplan) {
                                const $thisDialog = this.dialogManager.$getDialogElement("newTimePlanDialog");
                                const $mainDialog = this.dialogManager.$getDialogElement("createArrangementDialog");

                                if (context.lastTriggererDetails.preselectedPeople) {
                                    window.MessagesFacility.send("newTimePlanDialog", context.lastTriggererDetails.preselectedPeople, "peopleSelected");
                                }
                                if (context.lastTriggererDetails.preselectedRooms) {
                                    window.MessagesFacility.send("newTimePlanDialog", context.lastTriggererDetails.preselectedRooms, "roomsSelected");
                                }
                                if (context.lastTriggererDetails.preselectedMainPlanner) {
                                    window.MessagesFacility.send("newTimePlanDialog", context.lastTriggererDetails.preselectedMainPlanner, "setPlanner");
                                }

                                if (context.lastTriggererDetails.orderedServices) {
                                    window.MessagesFacility.send("newTimePlanDialog", context.lastTriggererDetails.orderedServices, "setServiceOrders");
                                }

                                console.log("context newTimePlanDialog", context);

                                [
                                    { from: '#countySelect', to: '#countySelect' },
                                    { from: '#schoolSelect', to: '#initialSchoolValue' },
                                    { from: '#id_ticket_code', to: '#serie_ticket_code' },
                                    { from: '#id_name', to: '#serie_title' },
                                    { from: '#id_name_en', to: '#serie_title_en' },
                                    { from: '#id_expected_visitors', to: '#serie_expected_visitors'},
                                    { from: '#id_meeting_place', to: '#id_meeting_place' },
                                    { from: '#id_meeting_place_en', to: '#id_meeting_place_en' },
                                    { from: '#_audienceId', to: '#_backingAudienceId' },
                                    { from: '#_arrangementTypeId', to: '#_backingArrangementTypeId' },
                                    { from: '#_statusTypeId', to: '#_statusTypeId' },
                                    { from: '#id_display_text', to: '#id_display_text' },
                                ].forEach( (mapping) => {
                                    $thisDialog.find( mapping.to ).val( $mainDialog.find( mapping.from )[0].value );
                                });

                                $thisDialog.find('#serie_uuid').val(crypto.randomUUID());
                                $mainDialog[0].querySelectorAll("#createArrangementDialog input[name='display_layouts']:checked")
                                    .forEach(checkboxElement => {
                                        $thisDialog.find('#id_display_layouts_serie_planner_' + checkboxElement.value)
                                            .prop( "checked", true );
                                    });

                                document.querySelectorAll('.form-outline').forEach((formOutline) => {
                                    new mdb.Input(formOutline).init();
                                });
                            }
                            else {
                                if (context.series !== undefined) {
                                    let serie = context.series.get(context.lastTriggererDetails.serie_uuid);
                                    const $dialogElement = $(this.dialogManager.$getDialogElement("newTimePlanDialog"));
                                    
                                    this.dialogManager._dialogRepository.get("newTimePlanDialog");

                                    PopulateCreateSerieDialogFromSerie(serie, $dialogElement, "newTimePlanDialog");
                                }
                            }
                            
                            document.querySelectorAll('.form-outline').forEach((formOutline) => {
                                new mdb.Input(formOutline).init();
                            });
                        },
                        destructure: () => {},
                        onUpdatedCallback: () => {
                            toastr.success("Tidsplan lagt til eller oppdatert i planen");
                            this.dialogManager.closeDialog("newTimePlanDialog");
                        },
                        onSubmit: async (context, details) => {
                            details.serie.friendlyDesc = SerieMetaTranslator.generate(details.serie);

                            if (context.series === undefined) {
                                context.series = new Map();
                            }
                            if (details.serie._uuid === undefined) {
                                details.serie._uuid = crypto.randomUUID();
                            }

                            details.serie.collisions = await CollisionsUtil.GetCollisionsForSerie(serieConvert(details.serie, new FormData(), ""), details.csrf_token);
                            context.series.set(details.serie._uuid, details.serie);
                            document.dispatchEvent(new CustomEvent(this.dialogManager.managerName + ".contextUpdated", { detail: { context: context } }))
                        },
                        dialogOptions: { 
                            width: 700,
                            dialogClass: 'no-titlebar',
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
                                dialogId: "breakOutActivityDialog",
                                managerName: "arrangementCreator",
                                customParameters: {
                                    slug: 0,
                                    orderPersonDialog: "orderPersonDialog",
                                    orderRoomDialog: "orderRoomDialog",
                                    hideRigging: true,
                                }
                            })
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

                            let serie = context.lastTriggererDetails.serie;
                            let collisionRecord = serie.collisions[context.lastTriggererDetails.collision_index];

                            const $breakOutActivityDialog = this.dialogManager.$getDialogElement("breakOutActivityDialog");
                            PopulateCreateEventDialogFromCollisionResolution(
                                $breakOutActivityDialog,
                                "breakOutActivityDialog",
                                collisionRecord,
                                serie
                            );

                            $('#breakOutActivityDialog').prepend( $(
                                document.querySelector('.conflict_summary_'  + context.lastTriggererDetails.collision_index).outerHTML
                            ).addClass("mb-4"));

                            $breakOutActivityDialog.find('#event_uuid').val(crypto.randomUUID());
                            document.querySelectorAll('.form-outline').forEach((formOutline) => {
                                new mdb.Input(formOutline).init();
                            });

                            this.dialogManager.setTitle("breakOutActivityDialog", "Bryt ut aktivitet");
                        },
                        onUpdatedCallback: () => {
                            toastr.success("Kollisjon løst, enkel aktivitet har blitt opprettet");
                            this.dialogManager.closeDialog("breakOutActivityDialog");
                        },
                        onSubmit: async (context, details) => {
                            if (context.events === undefined) {
                                context.events = new Map();
                            }
                            if (details.event._uuid === undefined) {
                                details.event._uuid = crypto.randomUUID();
                            }

                            details.event.is_resolution = true;
                            details.event.associated_serie_internal_uuid = context._lastTriggererDetails.serie._uuid;

                            let formData = new FormData();
                            for (let key in details.event) {
                                formData.append(key, details.event[key])
                            }

                            let startDate = new Date(details.event.start);
                            let endDate = new Date(details.event.end);
                            formData.append("fromDate", startDate.toISOString());
                            formData.append("toDate", endDate.toISOString());

                            details.event.collisions = await CollisionsUtil.GetCollisionsForEvent(formData, details.csrf_token);

                            if (details.event.collisions.length > 0) {
                                let collision = details.event.collisions[0];
                                await CollisionsUtil.FireOneToOneCollisionWarningSwal(collision);

                                return false;
                            }

                            context._lastTriggererDetails.serie.collisions
                                .splice(context._lastTriggererDetails.collision_index, 1);

                            context.events.set(details.event._uuid, details.event);
                            document.dispatchEvent(new CustomEvent(this.dialogManager.managerName + ".contextUpdated", { detail: { context: context } }))
                        },
                        dialogOptions: { 
                            width: 700,
                            dialogClass: 'no-titlebar',
                        }
                    })
                ],
                [
                    "newSimpleActivityDialog",
                    new Dialog({
                        dialogElementId: "newSimpleActivityDialog",
                        triggerElementId: "createArrangementDialog_createSimpleActivity",
                        triggerByEvent: true,
                        htmlFabricator: async (context) => {
                            return await this.dialogManager.loadDialogHtml({
                                url: "/arrangement/planner/dialogs/create_simple_event",
                                dialogId: "newSimpleActivityDialog",
                                managerName: "arrangementCreator",
                                dialogTitle: "Edit Activity",
                                customParameters: {
                                    slug: 0,
                                    orderPersonDialog: "orderPersonDialog",
                                    orderRoomDialog: "orderRoomDialog",
                                }
                            });
                        },
                        onRenderedCallback: (dialogManager, context) => {
                            document.querySelectorAll('.form-outline').forEach((formOutline) => {
                                new mdb.Input(formOutline).init();
                            });

                            let $simpleActivityDialog = this.dialogManager.$getDialogElement("newSimpleActivityDialog");
                            
                            if (context.lastTriggererDetails?.event_uuid === undefined) {
                                const $mainDialog = this.dialogManager.$getDialogElement("createArrangementDialog");
                                this.dialogManager.setTitle("newSimpleActivityDialog", "Opprett aktivitet");

                                if (context.lastTriggererDetails.preselectedPeople) {
                                    window.MessagesFacility.send("newSimpleActivityDialog", context.lastTriggererDetails.preselectedPeople, "peopleSelected");
                                }
                                if (context.lastTriggererDetails.preselectedRooms) {
                                    window.MessagesFacility.send("newSimpleActivityDialog", context.lastTriggererDetails.preselectedRooms, "roomsSelected");
                                }
                                if (context.lastTriggererDetails.preselectedMainPlanner) {
                                    window.MessagesFacility.send("newSimpleActivityDialog", context.lastTriggererDetails.preselectedMainPlanner, "setPlanner");
                                }

                                if (context.lastTriggererDetails.orderedServices) {
                                    window.MessagesFacility.send("newSimpleActivityDialog", context.lastTriggererDetails.orderedServices, "setServiceOrders");
                                }

                                [
                                    { from: '#countySelect', to: '#countySelect' },
                                    { from: '#schoolSelect', to: '#initialSchoolValue' },
                                    { from: '#id_ticket_code', to: '#ticket_code' },
                                    { from: '#id_name', to: '#title' },
                                    { from: '#id_name_en', to: '#title_en' },
                                    { from: '#id_expected_visitors', to: '#expected_visitors'},
                                    { from: '#id_meeting_place', to: '#id_meeting_place' },
                                    { from: '#id_meeting_place_en', to: '#id_meeting_place_en' },
                                    { from: '#id_display_text', to: '#id_display_text' },
                                    { from: '#_audienceId', to: '#_backingAudienceId' },
                                    { from: '#_arrangementTypeId', to: '#_backingArrangementTypeId'},
                                    { from: '#_statusTypeId', to: '#_statusTypeId' },
                                ].forEach( (mapping) => { 
                                    console.log(mapping, $mainDialog.find( mapping.from )[0].value);
                                    $simpleActivityDialog.find( mapping.to ).val( $mainDialog.find( mapping.from )[0].value );
                                });

                                $simpleActivityDialog.find('#event_uuid').val(crypto.randomUUID());
                                $mainDialog[0].querySelectorAll("input[name='display_layouts']:checked")
                                    .forEach(checkboxElement => {
                                        $simpleActivityDialog.find(`#${checkboxElement.value}_dlcheck`)
                                            .prop( "checked", true );
                                    })

                                return;
                            }
                            
                            this.dialogManager.setTitle("newSimpleActivityDialog", "Rediger aktivitet");
                            const $dialogElement = $(this.dialogManager.$getDialogElement("newSimpleActivityDialog"));
                            PopulateCreateEventDialog(context.events.get(context.lastTriggererDetails.event_uuid), $dialogElement, "newSimpleActivityDialog");

                            document.querySelectorAll('.form-outline').forEach((formOutline) => {
                                new mdb.Input(formOutline).init();
                            });
                        },
                        onUpdatedCallback: () => {
                            toastr.success("Enkel aktivitet lagt til eller oppdatert i planen");
                            this.dialogManager.closeDialog("newSimpleActivityDialog");
                        },
                        onSubmit: async (context, details) => {
                            if (context.events === undefined) {
                                context.events = new Map();
                            }
                            if (details.event._uuid === undefined) {
                                details.event._uuid = crypto.randomUUID();
                            }

                            let formData = new FormData();
                            for (let key in details.event) {
                                formData.append(key, details.event[key])
                            }

                            let startDate = new Date(details.event.start);
                            let endDate = new Date(details.event.end);
                            formData.append("fromDate", startDate.toISOString());
                            formData.append("toDate", endDate.toISOString());

                            details.event.collisions = await CollisionsUtil.GetCollisionsForEvent(formData, details.csrf_token);

                            if (details.event.collisions.length > 0) {
                                let collision = details.event.collisions[0];
                                await CollisionsUtil.FireOneToOneCollisionWarningSwal(collision);
                                return false;
                            }

                            context.events.set(details.event._uuid, details.event);
                            document.dispatchEvent(new CustomEvent(this.dialogManager.managerName + ".contextUpdated", { detail: { context: context } }))
                        },
                        dialogOptions: { 
                            width: 700, 
                            dialogClass: 'no-titlebar',
                        },
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
                                dialogId: 'orderRoomDialog',
                                managerName: 'arrangementCreator',
                                customParameters: {
                                    event_pk: 0,
                                    recipientDialogId: context.lastTriggererDetails.sendTo,
                                }
                            })
                        },
                        onRenderedCallback: (dialogManager, context) => {
                            window.MessagesFacility.send(
                                "orderRoomDialog", 
                                context.lastTriggererDetails.data, 
                                "setRoomSelection"
                            );
                        },
                        dialogOptions: { 
                            width: "50%",
                            dialogClass: 'no-titlebar',
                        },
                        onUpdatedCallback: () => {
                            // $(this.dialogManager.$getDialogElement("orderRoomDialog")).toggle("slide", () => {
                            //     this.dialogManager.closeDialog("orderRoomDialog");
                            // });
                        },
                        onSubmit: (context, details, dialogManager) => {
                            window.MessagesFacility.send(details.recipientDialog, details.selectedBundle, "roomsSelected");
                        }
                    })
                ],
                [
                    "orderPersonDialog",
                    new Dialog({
                        dialogElementId: "orderPersonDialog",
                        triggerElementId: undefined,
                        triggerByEvent: true,
                        htmlFabricator: async (context, dialog) => {
                            let multiple = context.lastTriggererDetails.multiple;
                            if (multiple === undefined)
                                multiple = true

                            return this.dialogManager.loadDialogHtml({
                                url: '/arrangement/planner/dialogs/order_person',
                                managerName: 'arrangementCreator',
                                dialogId: 'orderPersonDialog',
                                customParameters: {
                                    event_pk: 0,
                                    recipientDialogId: context.lastTriggererDetails.sendTo,
                                    multiple: multiple,
                                }
                            });
                        },
                        onRenderedCallback: (dialogManager, context) => {
                            window.MessagesFacility.send(
                                "orderPersonDialog", 
                                context.lastTriggererDetails.data, 
                                "setPersonSelection"
                            );
                        },
                        dialogOptions: { 
                            width: 500,
                            dialogClass: 'no-titlebar',
                        },
                        onUpdatedCallback: () => {
                            $(this.dialogManager.$getDialogElement("orderPersonDialog")).toggle("slide", () => {
                                this.dialogManager.closeDialog("orderPersonDialog");
                            });
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
                                managerName: 'arrangementCreator',
                                customParameters: {
                                    recipientDialogId: context.lastTriggererDetails.sendTo,
                                }
                            });
                        },
                        onUpdatedCallback: async () => {
                            this.dialogManager.closeDialog("orderServiceDialog");
                        },
                        onSubmit: (context, details, dialogManager, dialog) => {
                            console.log("orderServiceDialog.submit")
                            const eventName = dialog.data.whenEventName || "newServiceOrder";
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
                                managerName: "arrangementCreator",
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
                ],
            ]
        })
    }

    open() {
        this.dialogManager.openDialog( "createArrangementDialog" );
    }
}
