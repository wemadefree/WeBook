import { CollisionsUtil } from "./collisions_util.js";
import { Dialog, DialogManager } from "./dialog_manager/dialogManager.js";
import { PopulateCreateSerieDialogFromSerie } from "./form_populating_routines.js";
import { serieConvert } from "./serieConvert.js";
import { SeriesUtil } from "./seriesutil.js";
import { SerieMetaTranslator } from "./serie_meta_translator.js";


export class ArrangementCreator {
    constructor () {
        this.dialogManager = new DialogManager({
            managerName: "arrangementCreator",  
            dialogs: [
                [
                    "createArrangementDialog",
                    new Dialog({
                        dialogElementId: "createArrangementDialog",
                        triggerElementId: "_createArrangementDialog",
                        htmlFabricator: async (context) => {
                            return await fetch('/arrangement/planner/dialogs/create_arrangement?managerName=arrangementCreator')
                                    .then(response => response.text());
                        },
                        onPreRefresh: (dialog) => {
                            dialog._active_tab = active;
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
                            var csrf_token = details.formData.get("csrf_token");
                            var createArrangement = async function (formData, csrf_token) {
                                var response = await fetch("/arrangement/arrangement/ajax/create", {
                                    method: 'POST',
                                    body: formData,
                                    headers: {
                                        "X-CSRFToken": csrf_token
                                    },
                                    credentials: 'same-origin',
                                });

                                var json = await response.text();
                                var obj = JSON.parse(json);
                                return obj.arrangementPk;
                            };

                            var registerEvents = async function (events, arrangementId, csrf_token, serieUUIDToIdMap) {
                                var formData = new FormData();

                                for (let i = 0; i < events.length; i++) {
                                    var event = events[i];
                                    event.arrangement = arrangementId;
                                    
                                    if (event.is_resolution && "associated_serie_internal_uuid" in event) {
                                        event.associated_serie_id = serieUUIDToIdMap.get(event.associated_serie_internal_uuid);
                                    }

                                    for (var key in event) {
                                        formData.append("events[" + i + "]." + key, event[key]);
                                    }
                                }

                                await fetch("/arrangement/planner/create_events/", {
                                    method:"POST",
                                    body: formData,
                                    headers: {
                                        "X-CSRFToken": csrf_token
                                    },
                                    credentials: 'same-origin',
                                }).then(_ => { 
                                    document.dispatchEvent(new Event("plannerCalendar.refreshNeeded"));
                                })
                            }

                            var registerSerie = async function (serie, arrangementId, csrf_token, ticket_code) {
                                var events = SeriesUtil.calculate_serie(serie);
                                var formData = new FormData();

                                formData = serieConvert(serie, formData);

                                for (let i = 0; i < events.length; i++) {
                                    var event = events[i];
                                    event.title_en = serie.time.title_en;
                                    event.arrangement=arrangementId;
                                    event.start = event.from.toISOString();
                                    event.end = event.to.toISOString();
                                    event.ticket_code = ticket_code;
                                    event.expected_visitors = serie.time.expected_visitors;
                                    event.rooms = serie.rooms;
                                    event.people = serie.people;
                                    event.display_layouts = serie.display_layouts;

                                    for (var key in event) {
                                        formData.append("events[" + i + "]." + key, event[key]);
                                    }
                                }

                                formData.append("saveAsSerie", true);

                                return await fetch("/arrangement/planner/create_events/", {
                                    method:"POST",
                                    body: formData,
                                    headers: {
                                        "X-CSRFToken": csrf_token
                                    },
                                    credentials: 'same-origin',
                                }).then(response => response.json())
                                  .then(responseAsJson => { 
                                    document.dispatchEvent(new Event("plannerCalendar.refreshNeeded"));
                                    return responseAsJson.serie_id;
                                });
                            }
                            
                            var internalSerieUuidsMapToCreatedSerieIds = new Map(); // maps between our internal uuids used locally, to their "real" counter-parts in the back-end
                            createArrangement(details.formData, csrf_token)
                                .then(async arrId => {
                                    for (const serie of details.series) {
                                        var created_serie_id = await registerSerie(serie, arrId, csrf_token, details.formData.get("ticket_code"));
                                        internalSerieUuidsMapToCreatedSerieIds.set(String(serie._uuid), created_serie_id);
                                    }
                                    
                                    if (details.events !== undefined) {
                                        registerEvents(details.events, arrId, csrf_token, internalSerieUuidsMapToCreatedSerieIds);
                                    }
                                });
                        },
                        onUpdatedCallback: () => { 
                            toastr.success("Arrangement opprettet");
                            this.dialogManager.closeDialog("createArrangementDialog");
                        },
                        dialogOptions: { width: 900 }
                    }),
                ],
                [
                    "newTimePlanDialog",
                    new Dialog({
                        dialogElementId: "newTimePlanDialog",
                        triggerElementId: "createArrangementDialog_createSerie",
                        triggerByEvent: true,
                        htmlFabricator: async (context) => {
                            return await fetch("/arrangement/planner/dialogs/create_serie?managerName=arrangementCreator&dialog=newTimePlanDialog&orderRoomDialog=orderRoomDialog&orderPersonDialog=orderPersonDialog")
                                .then(response => response.text());
                        },
                        onRenderedCallback: (dialogManager, context) => { 
                            if (context.lastTriggererDetails === undefined) {
                                $('#serie_ticket_code').attr('value', $('#id_ticket_code')[0].value );
                                $('#serie_title').attr('value', $('#id_name')[0].value );
                                $('#serie_title_en').attr('value', $('#id_name_en')[0].value );
                                $('#serie_expected_visitors').attr('value', $('#id_expected_visitors')[0].value );

                                document.querySelectorAll("input[name='display_layouts']:checked")
                                    .forEach(checkboxElement => {
                                        $('#id_display_layouts_serie_planner_' + checkboxElement.value)
                                            .prop( "checked", true );
                                    })
                                
                                $('#serie_uuid').val(crypto.randomUUID());

                                return;
                            }
                            
                            var serie = context.series.get(context.lastTriggererDetails.serie_uuid);
                            PopulateCreateSerieDialogFromSerie(serie);
                        },
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
                        dialogOptions: { width: 700 }
                    })
                ],
                [
                    "breakOutActivityDialog",
                    new Dialog({
                        dialogElementId: "breakOutActivityDialog",
                        triggerElementId: "breakOutActivityDialog",
                        triggerByEvent: true,
                        htmlFabricator: async (context) => {
                            return await fetch('/arrangement/planner/dialogs/create_simple_event?slug=0&managerName=arrangementCreator&dialog=breakOutActivityDialog&orderRoomDialog=orderRoomDialog&orderPersonDIalog=orderPersonDialog&dialogTitle=Kollisjonshåndtering&dialogIcon=fa-code-branch')
                                .then(response => response.text());
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

                            var serie = context.lastTriggererDetails.serie;
                            var collision_record = serie.collisions[context.lastTriggererDetails.collision_index];

                            $('#ticket_code').val(serie.time.ticket_code ).trigger('change');
                            $('#title').val(serie.time.title ).trigger('change');
                            $('#title_en').attr('value', serie.time.title_en ).trigger('change');
                            $('#expected_visitors').attr('value', serie.time.expected_visitors ).trigger('change');

                            serie.display_layouts.split(",")
                                .forEach(checkboxElement => {
                                    $(`#${checkboxElement.value}_dlcheck`)
                                        .prop( "checked", true );
                                })

                            $('#breakOutActivityDialog').prepend( $(
                                document.querySelector('.conflict_summary_'  + context.lastTriggererDetails.collision_index).outerHTML
                            ).addClass("mb-4"));
                            
                            
                            // document.querySelectorAll("input[name='display_layouts']:checked")
                            //     .forEach(checkboxElement => {
                            //         $(`#${checkboxElement.value}_dlcheck`)
                            //             .prop( "checked", true );
                            //     })


                            var splitDateFunc = function (strToDateSplit) {
                                var date_str = strToDateSplit.split("T")[0];
                                var time_str = new Date(strToDateSplit).toTimeString().split(' ')[0];
                                return [ date_str, time_str ];
                            }

                            var startTimeArtifacts = splitDateFunc(collision_record.event_a_start);
                            var endTimeArtifacts = splitDateFunc(collision_record.event_a_end);
                            $('#fromDate').val(startTimeArtifacts[0]).trigger('change');
                            $('#fromTime').val(startTimeArtifacts[1]).trigger('change');
                            $('#toDate').val(endTimeArtifacts[0]).trigger('change');
                            $('#toTime').val(endTimeArtifacts[1]).trigger('change');
                                
                            // This ensures that english title is only obligatory IF a display layout has been selected.
                            // dialogCreateEvent__evaluateEnTitleObligatory();

                            if (serie.people.length > 0) {
                                var peopleSelectContext = Object();
                                peopleSelectContext.people = serie.people.join(",");
                                peopleSelectContext.people_name_map = serie.people_name_map;
                                document.dispatchEvent(new CustomEvent(
                                    "arrangementCreator.d1_peopleSelected",
                                    { detail: {
                                        context: peopleSelectContext
                                    } }
                                ));
                            }
                            if (serie.rooms.length > 0) {
                                var roomSelectContext = Object();
                                roomSelectContext.rooms = serie.rooms.join(",");
                                roomSelectContext.room_name_map = serie.room_name_map;
                                document.dispatchEvent(new CustomEvent(
                                    "arrangementCreator.d1_roomsSelected",
                                    { detail: {
                                        context: roomSelectContext
                                    } }
                                ));
                            }

                            $('#event_uuid').val(crypto.randomUUID());
                            document.querySelectorAll('.form-outline').forEach((formOutline) => {
                                new mdb.Input(formOutline).init();
                            });
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

                            var formData = new FormData();
                            for (var key in details.event) {
                                formData.append(key, details.event[key])
                            }

                            var startDate = new Date(details.event.start);
                            var endDate = new Date(details.event.end);
                            formData.append("fromDate", startDate.toISOString());
                            formData.append("toDate", endDate.toISOString());
                            
                            details.event.collisions = await CollisionsUtil.GetCollisionsForEvent(formData, details.csrf_token);

                            if (details.event.collisions.length > 0) {
                                var collision = details.event.collisions[0];
                                await CollisionsUtil.FireOneToOneCollisionWarningSwal(collision);
                                
                                return false;
                            }

                            context._lastTriggererDetails.serie.collisions
                                .splice(context._lastTriggererDetails.collision_index, 1);

                            context.events.set(details.event._uuid, details.event);
                            document.dispatchEvent(new CustomEvent(this.dialogManager.managerName + ".contextUpdated", { detail: { context: context } }))
                        },
                        dialogOptions: { width: 700 }
                    })
                ],
                [
                    "newSimpleActivityDialog",
                    new Dialog({
                        dialogElementId: "newSimpleActivityDialog",
                        triggerElementId: "createArrangementDialog_createSimpleActivity",
                        triggerByEvent: true,
                        htmlFabricator: async (context) => {
                            return await fetch('/arrangement/planner/dialogs/create_simple_event?slug=0&managerName=arrangementCreator&dialog=newSimpleActivityDialog&orderRoomDialog=orderRoomDialog&orderPersonDialog=orderPersonDialog')
                                .then(response => response.text());
                        },
                        onRenderedCallback: (dialogManager, context) => { 
                            
                            document.querySelectorAll('.form-outline').forEach((formOutline) => {
                                new mdb.Input(formOutline).init();
                            });
                            if (context.lastTriggererDetails === undefined) {
                                $('#ticket_code').attr('value', $('#id_ticket_code')[0].value );
                                $('#title').attr('value', $('#id_name')[0].value );
                                $('#title_en').attr('value', $('#id_name_en')[0].value );
                                $('#expected_visitors').attr('value', $('#id_expected_visitors')[0].value );
                                
                                document.querySelectorAll("input[name='display_layouts']:checked")
                                    .forEach(checkboxElement => {
                                        $(`#${checkboxElement.value}_dlcheck`)
                                            .prop( "checked", true );
                                    })
                                    
                                // This ensures that english title is only obligatory IF a display layout has been selected.
                                dialogCreateEvent__evaluateEnTitleObligatory();

                                $('#event_uuid').val(crypto.randomUUID());

                                return;
                            }

                            var event = context.events.get(context.lastTriggererDetails.event_uuid);
                            
                            var splitDateFunc = function (strToDateSplit) {
                                var date_str = strToDateSplit.split("T")[0];
                                var time_str = new Date(strToDateSplit).toTimeString().split(' ')[0];
                                return [ date_str, time_str ];
                            }
                            var startTimeArtifacts = splitDateFunc(event.start);
                            var endTimeArtifacts = splitDateFunc(event.end);

                            $('#event_uuid').val(event._uuid);
                            $('#title').val(event.title);
                            $('#title_en').val(event.title_en);
                            $('#ticket_code').val(event.ticket_code);
                            $('#expected_visitors').val(event.expected_visitors);
                            $('#fromDate').val(startTimeArtifacts[0]);
                            $('#fromTime').val(startTimeArtifacts[1]);
                            $('#toDate').val(endTimeArtifacts[0]);
                            $('#toTime').val(endTimeArtifacts[1]);

                            event.display_layouts.split(",").forEach(element => {
                                $(`#${String(parseInt(element))}_dlcheck`)
                                    .prop( "checked", true );
                            })

                            // This is fairly messy I am afraid, but the gist of what we're doing here is simulating that the user
                            // has "selected" rooms as they would through the dialog interface.
                            if (event.people.length > 0) {
                                var peopleSelectContext = Object();
                                peopleSelectContext.people = event.people.join(",");
                                peopleSelectContext.people_name_map = event.people_name_map;
                                document.dispatchEvent(new CustomEvent(
                                    "arrangementCreator.d1_peopleSelected",
                                    { detail: {
                                        context: peopleSelectContext
                                    } }
                                ));
                            }
                            if (event.rooms.length > 0) {
                                var roomSelectContext = Object();
                                roomSelectContext.rooms = event.rooms.join(",");
                                roomSelectContext.room_name_map = event.room_name_map;
                                document.dispatchEvent(new CustomEvent(
                                    "arrangementCreator.d1_roomsSelected",
                                    { detail: {
                                        context: roomSelectContext
                                    } }
                                ));
                            }

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

                            var formData = new FormData();
                            for (var key in details.event) {
                                formData.append(key, details.event[key])
                            }

                            var startDate = new Date(details.event.start);
                            var endDate = new Date(details.event.end);
                            formData.append("fromDate", startDate.toISOString());
                            formData.append("toDate", endDate.toISOString());
                            
                            details.event.collisions = await CollisionsUtil.GetCollisionsForEvent(formData, details.csrf_token);

                            if (details.event.collisions.length > 0) {
                                var collision = details.event.collisions[0];
                                await CollisionsUtil.FireOneToOneCollisionWarningSwal(collision);
                                return false;
                            }

                            context.events.set(details.event._uuid, details.event);
                            document.dispatchEvent(new CustomEvent(this.dialogManager.managerName + ".contextUpdated", { detail: { context: context } }))
                        },
                        dialogOptions: { width: 700 }
                    })
                ],
                [
                    "orderRoomDialog",
                    new Dialog({
                        dialogElementId: "orderRoomDialog",
                        triggerElementId: undefined,
                        triggerByEvent: true,
                        htmlFabricator: async (context) => {
                            return await fetch(`/arrangement/planner/dialogs/order_room?event_pk=0&manager=arrangementCreator&dialog=orderRoomDialog`)
                                .then(response => response.text());
                        },
                        onRenderedCallback: () => { },
                        dialogOptions: { width: 500 },
                        onUpdatedCallback: () => { 
                            toastr.success("Rom lagt til");
                            this.dialogManager.closeDialog("orderRoomDialog");
                        },
                        onSubmit: (context, details) => { 
                            context.rooms = details.formData.get("room_ids");
                            context.room_name_map = details.room_name_map;
                            
                            document.dispatchEvent(new CustomEvent(
                                `arrangementCreator.d1_roomsSelected`, 
                                { detail: { context: context } }
                            ));
                            document.dispatchEvent(new CustomEvent(
                                `arrangementCreator.d2_roomsSelected`, 
                                { detail: { context: context } }
                            ));
                        }
                    })
                ],
                [
                    "orderPersonDialog",
                    new Dialog({
                        dialogElementId: "orderPersonDialog",
                        triggerElementId: undefined,
                        triggerByEvent: true,
                        htmlFabricator: async (context) => {
                            return await fetch(`/arrangement/planner/dialogs/order_person?event_pk=0&manager=arrangementCreator&dialog=orderPersonDialog`)
                            .then(response => response.text());
                        },
                        onRenderedCallback: () => { },
                        dialogOptions: { width: 500 },
                        onUpdatedCallback: () => { 
                            toastr.success("Personer lagt til");
                            this.dialogManager.closeDialog("orderPersonDialog");
                        },
                        onSubmit: (context, details) => {
                            var people_ids = details.formData.get("people_ids");
                            context.people = people_ids;
                            context.people_name_map = details.people_name_map;
                            
                            document.dispatchEvent(new CustomEvent(
                                "arrangementCreator.d1_peopleSelected",
                                { detail: {
                                    context: context
                                } }
                            ));
                            document.dispatchEvent(new CustomEvent(
                                "arrangementCreator.d2_peopleSelected",
                                { detail: {
                                    context: context
                                } }
                            ));
                        }
                    })
                ]
            ]            
        })
    }

    open() {
        this.dialogManager.openDialog( "createArrangementDialog" );
    }    
}