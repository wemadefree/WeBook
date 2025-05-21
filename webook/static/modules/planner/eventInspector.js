import { Dialog, DialogFormInterceptorPlugin, DialogManager } from "./dialog_manager/dialogManager.js";
import { QueryStore } from "./querystore.js";

export class EventInspector {
    constructor () {
        this.dialogManager = new DialogManager({
            managerName: "eventInspector",
            dialogs: [
                [
                    "inspectEventDialog",
                    new Dialog({
                        dialogElementId: "inspectEventDialog",
                        triggerElementId: "_inspectEventDialog",
                        triggerByEvent: true,
                        htmlFabricator: async (context) => {
                            if (context.lastTriggererDetails !== undefined && context.lastTriggererDetails.pk !== undefined) {
                                context.event.pk = context.lastTriggererDetails.pk;
                            }   

                            return this.dialogManager.loadDialogHtml({
                                url: "/arrangement/planner/dialogs/event_inspector/" + context.event.pk,
                                managerName: "eventInspector",
                                dialogId: "inspectEventDialog",
                                dialogTitle: "Inspect event",
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
                            document.querySelectorAll('.form-outline').forEach((formOutline) => {
                                new mdb.Input(formOutline).init();
                            });
                        },
                        dialogOptions: { width: "80%", height: "100%", dialogClass: 'no-titlebar', modal:true, },
                        onUpdatedCallback: () => {
                            // this.dialogManager.closeDialog("inspectEventDialog");
                            toastr.success("Endringer er lagret");
                        },
                        onSubmit: async (context, details) => {
                            const responses = await QueryStore.UpdateEvents( [details.event], details.csrf_token );
                            const response = responses[0];
                            
                            if (response.success === true) {
                                document.dispatchEvent(new Event("plannerCalendar.refreshNeeded"));
                                this.dialogManager.reloadDialog("inspectEventDialog");
                                
                                return true;
                            }

                            let collisionText = "";
                            let subtext = "Forandringer på selve aktiviteten har blitt lagret, men aktiviteter for rigging har ikke blitt opprettet."
                            if (response.main_event_is_in_collision === true) {
                                collisionText = "aktiviteten"
                                subtext = "";
                            }
                            else if (response.post_buffer_event_is_in_collision === true) {
                                collisionText = "riggetid etter aktiviteten"
                            }
                            else if (response.pre_buffer_event_is_in_collision) {
                                collisionText = "riggetid før aktiviteten"
                            }

                            Swal.fire(
                                'Kollisjon',
                                `Endringen kunne ikke lagres da ${collisionText} er i en kollisjon med en annen aktivitet på en eksklusiv ressurs.\n${subtext}`,
                                'warning'
                            )

                            return false;
                        }
                    }),
                ],
                [
                    "orderPersonDialog",
                    new Dialog({
                        dialogElementId: "orderPersonDialog",
                        triggerElementId: "inspectEventDialog_addPeopleBtn",
                        triggerByEvent: true,
                        htmlFabricator: async (context) => {
                            let multiple = context.lastTriggererDetails.multiple;
                            if (multiple === undefined)
                                multiple = true
                                
                            return this.dialogManager.loadDialogHtml({
                                url: '/arrangement/planner/dialogs/order_person',
                                managerName: 'eventInspector',
                                dialogId: 'orderPersonDialog',
                                customParameters: {
                                    event_pk: context.event.pk,
                                    multiple: multiple,
                                    recipientDialogId: context.lastTriggererDetails.sendTo,
                                },
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
                            this.dialogManager.closeDialog("orderPersonDialog");
                            // this.dialogManager.reloadDialog("inspectEventDialog")
                        },
                        onSubmit: (context, details, dialogManager, dialog) => {
                            const eventName = dialog.data.whenEventName || "peopleSelected";

                            window.MessagesFacility.send("inspectEventDialog", details.selectedBundle, eventName);
                            toastr.success("Valgte personer er blitt lagt til i arrangementet");
                        }
                    })
                ],
                [
                    "orderRoomDialog",
                    new Dialog({
                        dialogElementId: "orderRoomDialog",
                        triggerElementId: "inspectEventDialog_addRoomsBtn",
                        triggerByEvent: true,
                        htmlFabricator: async (context) => {
                            return await this.dialogManager.loadDialogHtml({
                                url: '/arrangement/planner/dialogs/order_room',
                                managerName: 'eventInspector',
                                dialogId: 'orderRoomDialog',
                                customParameters: {
                                    event_pk: context.event.pk,
                                    recipientDialogId: context.lastTriggererDetails.sendTo,
                                }
                            });
                        },
                        onRenderedCallback: (dialogManager, context) => {
                            window.MessagesFacility.send(
                                "orderRoomDialog", 
                                context.lastTriggererDetails.data, 
                                "setRoomSelection"
                            );
                        },
                        dialogOptions: { 
                            width: 500,
                            dialogClass: 'no-titlebar',
                        },
                        onUpdatedCallback: () => { 
                            this.dialogManager.closeDialog("orderRoomDialog"); 
                        },
                        onSubmit: (context, details, dialogManager) => { 
                            dialogManager._dialogRepository.get(details.recipientDialog)
                                .communicationLane.send("roomsSelected", details.selectedBundle);
                        }
                    })
                ],
                [
                    "uploadFilesDialog",
                    new Dialog({
                        dialogElementId: "uploadFilesDialog",
                        triggerElementId: "eventDialog_uploadFilesBtn",
                        triggerByEvent: true,
                        htmlFabricator: async (context) => {
                            return await this.dialogManager.loadDialogHtml({
                                url: '/arrangement/planner/dialogs/upload_files_dialog',
                                dialogId: 'uploadFilesDialog',
                                managerName: 'eventInspector',
                            });
                        },
                        onRenderedCallback: (dialogInstance, context) => {},
                        dialogOptions: { 
                            width: 600, 
                            dialogClass: 'no-titlebar',
                        },
                        onUpdatedCallback: async () => { 
                            this.dialogManager.closeDialog("uploadFilesDialog"); 
                            await this.dialogManager.reloadDialog("inspectEventDialog");

                            window.MessagesFacility.send( "inspectEventDialog", { tab: "files-tab" }, "moveToTab" );
                        },
                        onSubmit: async (context, details) => {
                            details.formData.append("pk", context.event.pk);
                            await fetch(`/arrangement/event/${context.event.pk}/upload`, {
                                method: 'POST',
                                body: details.formData,
                                headers: {
                                    'X-CSRFToken': details.csrf_token
                                }
                            });
                        }
                    })
                ],
                [
                    "newNoteDialog",
                    new Dialog({
                        dialogElementId: 'newNoteDialog',
                        triggerElementId: 'inspectEventDialog__newNoteBtn',
                        triggerByEvent: true,
                        htmlFabricator: async (context) => {
                            return await this.dialogManager.loadDialogHtml(
                                {
                                    url: '/arrangement/planner/dialogs/new_note',
                                    managerName: 'eventInspector',
                                    dialogId: 'newNoteDialog',
                                    customParameters: {
                                        pk: context.event.pk,
                                        entityType: "event",
                                    }
                                }
                            );
                        },
                        onRenderedCallback: () => { console.info("Rendered") },
                        onUpdatedCallback: async () => {
                            this.dialogManager.closeDialog("newNoteDialog");
                            await this.dialogManager.reloadDialog("inspectEventDialog");

                            window.MessagesFacility.send( "inspectEventDialog", { tab: "notes-tab" }, "moveToTab" );
                        },
                        onSubmit: async (context, details) => {
                            await fetch('/arrangement/note/post', {
                                method: 'POST',
                                body: Utils.convertObjToFormData(details),
                                credentials: 'same-origin',
                                headers: {
                                    "X-CSRFToken": details.csrf_token
                                }
                            }).then(response => console.log("response", response));
                        },
                        dialogOptions: { 
                            width: 700,
                            height: "100%",
                            dialogClass: 'no-titlebar',
                        },
                    })
                ],
                [
                    "editNoteDialog",
                    new Dialog({
                        dialogElementId: "editNoteDialog",
                        triggerElementId: undefined,
                        triggerByEvent: true,
                        htmlFabricator: async (context) => {
                            return await this.dialogManager.loadDialogHtml(
                                {
                                    url: '/arrangement/planner/dialogs/edit_note/' + context.lastTriggererDetails.note_pk,
                                    managerName: 'eventInspector',
                                    dialogId: 'editNoteDialog',
                                }
                            );
                        },
                        onRenderedCallback: () => { console.info("Rendered"); },
                        onUpdatedCallback: async () => {
                            this.dialogManager.closeDialog("editNoteDialog");
                            await this.dialogManager.reloadDialog("inspectEventDialog");

                            window.MessagesFacility.send( "inspectEventDialog", { tab: "notes-tab" }, "moveToTab" );
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
                    "orderServiceDialog",
                    new Dialog({
                        dialogElementId: "orderServiceDialog",
                        triggerElementId: undefined,
                        triggerByEvent: true,
                        htmlFabricator: async (context) => {
                            if (!context.lastTriggererDetails.entity_type)
                                throw Error("Please supply a valid entity type (either 'event' or 'serie')");

                            return this.dialogManager.loadDialogHtml({
                                url: '/arrangement/planner/dialogs/order_service/' + context.lastTriggererDetails.entity_type + '/' + context.event.pk,
                                dialogId: 'orderServiceDialog',
                                managerName: 'eventInspector',
                                customParameters: {
                                    recipientDialogId: context.lastTriggererDetails.sendTo,
                                }
                            });
                        },
                        onRenderedCallback: () => { },
                        dialogOptions: { width: "70%", dialogClass: 'no-titlebar', },
                        onUpdatedCallback: async () => {
                        },
                        onSubmit: async (context, details, dialogManager, dialog) => {
                            details.requestedServices.forEach(async (serviceOrder) => {
                                let formData = new FormData();
                                formData.append("parent_type", "event")
                                formData.append("parent_id", serviceOrder.parent_id);   
                                formData.append("service_id", serviceOrder.service_id);
                                formData.append("freetext_comment", serviceOrder.freetext_comment);

                                await fetch('/arrangement/planner/dialogs/order_service/event/' + serviceOrder.parent_id, {
                                    method: 'POST',
                                    body: formData,
                                    headers: {
                                        "X-CSRFToken": details.csrf_token
                                    }
                                }).then(response => response.json())
                                .then(async _ => { 
                                    this.dialogManager.closeDialog("orderServiceDialog");
                                    await this.dialogManager.reloadDialog("inspectEventDialog");

                                    window.MessagesFacility.send( "inspectEventDialog", { tab: "service-orders-tab" }, "moveToTab" );
                                 });
                            });

                        }
                    })
                ],
                [
                    "inspectServiceOrderDialog",
                    new Dialog({
                        dialogElementId: "inspectServiceOrderDialog",
                        triggerElementId: undefined,
                        triggerByEvent: true,
                        plugins: [ new CustomDialogFormInterceptorPlugin("{{csrf_token}}") ],
                        formUrl: '/arrangement/planner/dialogs/inspect_service_order/<<id>>',
                        htmlFabricator: async (context) => {
                            console.log("context", context);

                            return this.dialogManager.loadDialogHtml({
                                url: '/arrangement/planner/dialogs/inspect_service_order/' + context.lastTriggererDetails.order_id,
                                dialogId: "inspectServiceOrderDialog",
                                managerName: "eventInspector",
                            })
                        },
                        onRenderedCallback: () => { this.dialogManager._makeAware(); },
                        dialogOptions: { width: "70%", dialogClass: 'no-titlebar' },
                        onUpdatedCallback: async () => {
                            this.dialogManager.closeDialog("inspectServiceOrderDialog");
                            await this.dialogManager.reloadDialog("inspectEventDialog");

                            window.MessagesFacility.send( "inspectEventDialog", { tab: "service-orders-tab" }, "moveToTab" );
                        },
                        onSubmit: (context, details, dialogManager, dialog) => {
                        }
                    })
                ]
            ]            
        })
    }

    inspect(pk) {
        this.dialogManager.setContext({ event: { pk: pk } });
        this.dialogManager.openDialog( "inspectEventDialog" );
    }    
}

class CustomDialogFormInterceptorPlugin extends DialogFormInterceptorPlugin {
    constructor (csrf_token) {
        super(csrf_token);
    }

    onResponseOk() {
        toastr.success("Forandringene har blitt lagret!");
    }
}