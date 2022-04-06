/**
 * arrangementInspector.js
 * 
 * This should, when time allows, be split into a more re-usable component. The business logic
 * is too integrated with dialog management and dialog concerns. I think the best solution is to
 * split this up into a dialog manager, and then a consumer of said manager. Allows us to use the dialog approach
 * in more than just the main calendar -- which may be neat.
 */

class Dialog {
    constructor ({ dialogElementId, triggerElementId, htmlFabricator, onRenderedCallback, onUpdatedCallback, onSubmit, onPreRefresh, dialogOptions } = {}) {
        this.dialogElementId = dialogElementId;
        this.triggerElementId = triggerElementId;
        this.htmlFabricator = htmlFabricator;
        this.onRenderedCallback = onRenderedCallback;
        this.onUpdatedCallback = onUpdatedCallback;
        this.onSubmit = onSubmit;
        this.onPreRefresh = onPreRefresh;
        this.dialogOptions = dialogOptions;
    }

    _$getDialogEl() {
        return $("#" + this.dialogElementId);
    }

    async render(arrangement) {
        this.prepareDOM();

        if (this.isOpen() === false) {
            $('body')
                .append(await this.htmlFabricator(arrangement))
                .ready( () => {
                    this.onRenderedCallback(this);
                    this._$getDialogEl().dialog( this.dialogOptions );       
                });
        }
    }

    async refresh(arrangement, html) {
        console.log(html);
        if (this.isOpen() === true) {
            if (this.onPreRefresh !== undefined) {
                await this.onPreRefresh(this);
            }

            if (html === undefined) {
                html = await this.htmlFabricator(arrangement);
            }
            else { console.log(html); }

            var holderEl = document.createElement("span");
            holderEl.innerHTML = html;

            document.querySelector("#" + this.dialogElementId).innerHTML 
                = holderEl.querySelector("#" + this.dialogElementId).innerHTML;

            this.onRenderedCallback(this);

            return;
        }

        console.warn("Tried refreshing a non-open dialog.")
    }

    close() {
        if (this.isOpen() === true) {
            this._$getDialogEl().dialog("close");
        }
    }

    prepareDOM() {
        var $dialogElement = this._$getDialogEl();
        if ($dialogElement[0] !== undefined) {
            $dialogElement[0].remove();
        }
    }

    isOpen() {
        var $dialogElement = this._$getDialogEl();

        if ($dialogElement[0] === undefined || $($dialogElement).dialog("isOpen") === false) {
            return false;
        }

        return true;
    }
}


export class ArrangementInspector {
    constructor (csrf_token) {
        this._listenForRepopRequest();
        this._listenForUpdatedRequest();
        this._listenForSubmitRequest();
        this.csrf_token = csrf_token;

        this._dialogRepository = new Map([
            [ 
                "mainDialog", 
                new Dialog({
                    dialogElementId: "mainDialog",
                    triggerElementId: "_mainDialog",
                    htmlFabricator: async (arrangement) => {
                        return await fetch('/arrangement/planner/dialogs/arrangement_information/' + arrangement.slug)
                                .then(response => response.text());
                    },
                    onPreRefresh: (dialog) => {
                        var active = $('#tabs').tabs ( "option", "active" );
                        dialog._active_tab = active;
                    },
                    onRenderedCallback: (dialog) => {
                        $('#tabs').tabs(); 

                        if (dialog._active_tab !== undefined) {
                            $('#tabs').tabs("option", "active", dialog._active_tab);
                            dialog._active_tab = undefined;
                        }

                        this._makeAware(); 
                    },
                    onSubmit: async (arrangement, formData) => { 
                        var getArrangementHtml = async function (slug, formData, csrf_token) {
                            var response = await fetch("/arrangement/planner/dialogs/arrangement_information/" + slug, {
                                method: 'POST',
                                body: formData,
                                headers: {
                                    "X-CSRFToken": csrf_token
                                },
                                credentials: 'same-origin',
                            });
                            return await response.text();
                        }

                        var somehtml = await getArrangementHtml(arrangement.slug, formData, this.csrf_token);
                        this.reloadDialog("mainDialog", somehtml);

                        document.dispatchEvent(new Event("plannerCalendar.refreshNeeded"));
                    },
                    onUpdatedCallback: () => { this.reloadDialog("mainDialog"); },
                    dialogOptions: { width: 600 }
                }) 
            ],
            [
                "addPlannerDialog",
                new Dialog({
                    dialogElementId: "addPlannerDialog",
                    triggerElementId: "mainDialog__addPlannerBtn",
                    htmlFabricator: async (arrangement) => {
                        return await fetch("/arrangement/planner/dialogs/add_planner?slug=" + arrangement.slug)
                            .then(response => response.text());
                    },
                    onRenderedCallback: () => { console.info("Rendered"); },
                    onUpdatedCallback: ( ) => { this.reloadDialog("mainDialog"); this.closeDialog("addPlannerDialog"); },
                    dialogOptions: { width: 700 }
                })
            ],
            [
                "newTimePlanDialog",
                new Dialog({
                    dialogElementId: "newTimePlanDialog",
                    triggerElementId: "mainPlannerDialog__newTimePlan",
                    htmlFabricator: async (arrangement) => {
                        return await fetch("/arrangement/planner/dialogs/create_serie?slug=" + arrangement.slug)
                            .then(response => response.text());
                    },
                    onRenderedCallback: () => { console.info("Rendered"); },
                    onUpdatedCallback: () => { this.reloadDialog("mainDialog"); this.closeDialog("newTimePlanDialog"); },
                    dialogOptions: { width: 700 }
                })
            ],
            [
                "newSimpleActivityDialog",
                new Dialog({
                    dialogElementId: "newSimpleActivityDialog",
                    triggerElementId: "mainPlannerDialog__newSimpleActivity",
                    htmlFabricator: async (arrangement) => {
                        return await fetch('/arrangement/planner/dialogs/create_simple_event?slug=' + arrangement.slug)
                            .then(response => response.text());
                    },
                    onRenderedCallback: () => { console.info("Rendered") },
                    onUpdatedCallback: () => { this.reloadDialog("mainDialog"); this.closeDialog("newSimpleActivityDialog"); },
                    dialogOptions: { width: 500 }
                })
            ],
            [
                "calendarFormDialog",
                new Dialog({
                    dialogElementId: "calendarFormDialog",
                    triggerElementId: "mainPlannerDialog__showInCalendarForm",
                    htmlFabricator: async (arrangement) => {
                        return await fetch('/arrangement/planner/dialogs/arrangement_calendar_planner/' + arrangement.slug)
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
                    htmlFabricator: async (arrangement) => {
                        return await fetch("/arrangement/planner/dialogs/promote_main_planner?slug=" + arrangement.slug)
                            .then(response => response.text());
                    },
                    onRenderedCallback: () => { console.info("Rendered") },
                    onUpdatedCallback: () => { this.reloadDialog("mainDialog"); this.closeDialog("promotePlannerDialog"); },
                    dialogOptions: { width: 500 },
                })
            ],
            [
                "newNoteDialog",
                new Dialog({
                    dialogElementId: "newNoteDialog",
                    triggerElementId: "mainPlannerDialog__newNoteBtn",
                    htmlFabricator: async (arrangement) => {
                        return await fetch("/arrangement/planner/dialogs/new_note?slug=" + arrangement.slug)
                            .then(response => response.text());
                    },
                    onRenderedCallback: () => { console.info("Rendered") },
                    onUpdatedCallback: () => { this.reloadDialog("mainDialog"); this.closeDialog("newNoteDialog");  },
                    dialogOptions: { width: 500 },
                })
            ],
        ]);

        this.dialogElIdToDialogTriggerKey = new Map();
        this._dialogRepository.forEach((value, key) => {
            this.dialogElIdToDialogTriggerKey.set(value.dialogElementId, key);
        });
    }

    reloadDialog(dialogId, customHtml=undefined) {
        this._dialogRepository.get(dialogId).refresh(this.arrangement, customHtml);
    }

    closeDialog(dialogId) {
        this._dialogRepository.get(dialogId).close();
    }

    _listenForRepopRequest() {
        document.addEventListener("arrangementPlannerDialogs.repop", () => {
            this.repop();
        })
    }
    _listenForUpdatedRequest() {
        document.addEventListener("arrangementPlannerDialogs.hasBeenUpdated", (e) => {
            this._dialogRepository.get(e.detail.dialog).onUpdatedCallback();
        });
    }
    _listenForSubmitRequest() {
        document.addEventListener("arrangementPlannerDialogs.submit", (e) => {
            this._dialogRepository.get(e.detail.dialog).onSubmit(this.arrangement, e.detail.formData);
        })
    }

    repop() {
        this._dialogRepository.forEach( (value, key, map) => {
            var dialogEl = $("#" + value.dialogElementId);
            if (dialogEl !== undefined) {
                dialogEl.dialog("destroy");
            }

            this.inspectArrangement(this.arrangement);
        });
    }

    inspectArrangement( arrangement ) {
        this.arrangement = arrangement;
        this._dialogRepository.get("mainDialog").render(arrangement);

        this.$nameField = undefined;
        this.$targetAudienceField = undefined;
        this.$arrangementTypeField = undefined;
        this.$startsWhenField = undefined;
        this.$endsWhenField = undefined;
        this.$plannersField = undefined;
        this.$multimediaSwitch = undefined;

        this.$saveArrangementBtn = undefined;
        this.$editArrangementBtn = undefined;
        this.$openInDetailedViewBtn = undefined;
        this.$archiveArrangementBtn = undefined;
        this.$addPlannerBtn = undefined;
    }

    _setTriggers() {
        this._dialogRepository.forEach( (value, key, map) => {
            console.log(" >> Binding to " + value.triggerElementId)
            console.log(value);
            $("#" + value.triggerElementId).on('click', () => {
                value.render(this.arrangement);
            });
        })
    }

    _makeAware() {
        this.$nameField = $('#mainPlannerDialog__nameField');
        this.$addPlannerBtn = $('#mainDialog__addPlannerBtn');
        this.$newTimePlanBtn = $('#mainPlannerDialog__newTimePlan');
        this.$newSimpleActivityBtn = $('#mainPlannerDialog__newSimpleActivity');
        this.$showInCalendarFormBtn = $('#mainPlannerDialog__showInCalendarForm');
        this.$promoteNewPlannerBtn = $('#mainPlannerDialog__promotePlannerBtn');

        this._setTriggers();
    }
}