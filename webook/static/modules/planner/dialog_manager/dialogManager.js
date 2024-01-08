
 export class Dialog {
    constructor ({ dialogElementId, 
                   triggerElementId, 
                   htmlFabricator, 
                   onRenderedCallback, 
                   onUpdatedCallback, 
                   onSubmit, 
                   onPreRefresh, 
                   dialogOptions, 
                   triggerByEvent=false, 
                   customTriggerName=undefined,
                   title=undefined,
                   formUrl=undefined,
                   onDestroy=undefined,
                   renderer=new DialogComplexDiscriminativeRenderer(),
                   plugins=[ ],
                } = {}) {
        this.dialogElementId = dialogElementId;
        this.triggerElementId = triggerElementId;
        this.customTriggerName = customTriggerName;
        this.triggerByEvent = triggerByEvent,
        this.htmlFabricator = htmlFabricator;
        this.onRenderedCallback = onRenderedCallback;
        this.onUpdatedCallback = onUpdatedCallback;
        this.onSubmit = onSubmit;
        this.onDestroy = onDestroy || this.standardOnDestroy;
        this.onPreRefresh = onPreRefresh;
        this.dialogOptions = dialogOptions;
        this._isRendering = false;
        this.title = title;

        this.data = {};

        // The internal data on the dialog itself. Synced up from the dialog instance, and allows viewing the data[ {} .. .] 
        // The data-to-manager syncing plugin must be activated on the respective dialgo for this to be populated.
        this.internalDialogData = {}

        this.formUrl = formUrl;

        this.renderer = renderer;
        this.discriminator = null;

        this.communicationLane = new FakeOutDialogEventCommunicationLane(this.dialogElementId);

        this.plugins = [];
        plugins.forEach((plugin) => {
            plugin.dialog = this;
            this.plugins.push( plugin );
        });
    }

    standardOnDestroy() {
    }

    _$getDialogEl() {
        return this.renderer.$dialogElement;
    }

    async render(context, html) {
        if (context.lastTriggererDetails?.data !== undefined)
            this.data = context.lastTriggererDetails.data;

        let result = await this.renderer.render(context, this, html);
        
        $(this.renderer.$dialogElement).on("dialogclose", (event) => {
            this.destroy();
        });
        
        debugger;

        this.plugins.forEach((plugin) => plugin.onRender(context));
        return result;
    }

    changeTitle(newTitle) {
        this._$getDialogEl().dialog('option', 'title', newTitle);
    }

    async refresh(context, html) {
        if (this.isOpen() === true) {
            if (this.onPreRefresh !== undefined) {
                await this.onPreRefresh(this);
            }
            
            if (html === undefined) {
                html = await this.htmlFabricator(context, this);
            }

            // this.destroy();
            this.render(context, html);

            this.onRenderedCallback(this, context);

            return;
        }

        console.warn("Tried refreshing a non-open dialog.")
    }

    close() {
        if (this.isOpen() === true) {
            if (typeof this.destructure !== "undefined")
                this.destructure();
            this.destroy();
        }
    }

    prepareDOM() {
        const selector = `#${this.dialogElementId}.${this.discriminator}`

        if (this.dialogElementId == "editEventSerieDialog") {
            selector += ",#newTimePlanDialog";
        }

        let elements = document.querySelectorAll(selector);
        elements.forEach(element => {
            element.remove();
        });
    }

    getInstance() {
        return this._$getDialogEl().dialog( "instance" );
    }

    destroy() {
        if (!this.renderer.dialogElement)
            return;
        this._$getDialogEl().dialog( "destroy" );
        this.renderer.removeFromDOM();
        this.discriminator=null;
    }

    isOpen() {
        const $dialogElement = this._$getDialogEl();
        return !($dialogElement === null || $dialogElement === undefined || this.getInstance() === false || this.getInstance() === undefined || $dialogElement.dialog("isOpen") === false)
    }
}

export class DialogFormInterceptorPlugin {
    constructor (csrf_token) {
        this.dialog = null;
        this.context = null;
        this.csrf_token = csrf_token;
    }

    onResponseOk() {
        location.reload();
    }

    onRender(context) {
        this.context = context;
        this._findAllForms();
    }

    /**
     * When receiving response 200 it is not a guarantee that the submission was a success.
     * Status code 200 will be returned if; a) submission succeeded or b) validation failed.
     * Validation messages will in the latter case be visible. This function checks the returned
     * html, and ascertains which one of these cases it is.
     */
    _ascertainStateFromBodyHtml(html) {
        let holder = document.createElement("span");
        holder.innerHTML = html;
        
        return holder.querySelectorAll(".form-error").length == 0
    }

    _findAllForms() {
        let formElementsWithinDialog = this.dialog._$getDialogEl()[0].querySelectorAll("form");
        
        formElementsWithinDialog.forEach((formElement) => {
            let cancelButtons = formElement.querySelectorAll(".cancel-button");
            cancelButtons.forEach((cancelButton) => {
                cancelButton.onclick = (event) => {
                    event.preventDefault();
                    this.dialog.close();
                }
            });

            formElement.onsubmit = function (event) {
                event.preventDefault();

                const action = formElement.getAttribute("action") || this.dialog.formUrl;
                const formData = new FormData(formElement);

                fetch(action, {
                    method: 'POST',
                    body: formData,
                    headers: {
                        "X-CSRFToken": this.csrf_token,
                    },
                    credentials: 'same-origin',
                }).then(response => {
                    if (response.status !== 200) {
                        throw Error("Submission of form failed", response);
                    }

                    return response.text();
                }).then(html => { 
                    if (this._ascertainStateFromBodyHtml(html)) {
                        this.onResponseOk();
                        this.dialog.close();
                    }
                    else {
                        // validation error -- we want to refresh the dialog
                        this.dialog.refresh(this.context, html);
                    }
                });
            }.bind(this);
        });
    }
}

export class DialogBaseRenderer {
    constructor() {
        this._isRendering = false;
        this.$dialogElement = null;
        this.dialogElement = null;
    }

    async render(context, dialog) {
    }

    removeFromDOM() {
        this.dialogElement.remove();
        this.dialogElement = null;
        this.$dialogElement = null;
    }
}

export class DialogSimpleRenderer extends DialogBaseRenderer {
    constructor() {
        super();
    }

    async render(context, dialog, html=null) {
        if (this._isRendering === false) {
            this._isRendering = true;
            if (dialog.isOpen() === false) {
                if (!html)
                    html = await dialog.htmlFabricator(context, dialog);
                let span = document.createElement("span");
                span.innerHTML = html;

                this.dialogElement = span;
                this.$dialogElement = $(span);

                $('body')
                    .append(span)
                    .ready( () => {
                        dialog._$getDialogEl().dialog( dialog.dialogOptions );
                        dialog.onRenderedCallback(dialog, context);

                        dialog._$getDialogEl().parent().find('.ui-dialog-titlebar-close')
                            .html("<span id='railing'></span><span class='dialogCloseButton'><i class='fas fa-times float-end'></i></span>")
                            .click( () => {
                                dialog.onDestroy();
                                dialog.destroy();
                            });
                        
                        dialog.changeTitle( dialog.title );
                        this._isRendering = false;
                });
            }
            else {
                this._isRendering = false;
            }
        }
        else {
            console.warn("Dialog is already rendering...")
        }
    }
}

export class DialogComplexDiscriminativeRenderer extends DialogBaseRenderer {
    constructor() {
        super();

        this.discriminator = null;

        this.headerButtons = [
            {
                tooltip: "Lukk denne dialogen",
                icon: "fa-times",
                action: (dialog, $buttonNode) => {
                    dialog.onDestroy();
                    dialog.destroy();
                },
            },
            {
                tooltip: "Ekspander dialogen til å dekke hele skjermen",
                icon: "fa-expand",
                action: (dialog, clickEvent) => {
                    const changeIcon = (node, newClass) => {
                        if (node.tagName === "SPAN")
                            node = node.children[0];
                        node.setAttribute("class", "fas " + newClass)
                    };

                    let options = {};
                    if (dialog._isExpanded === true) {
                        options = { height: dialog._originalHeight, width: dialog._originalWidth };
                        changeIcon(clickEvent.target, "fa-expand");
                    }
                    else {
                        options = { height: "100%", width: "100%" };
                        dialog._originalHeight = dialog._$getDialogEl().dialog("option", "height");
                        dialog._originalWidth = dialog._$getDialogEl().dialog("option", "width");
                        changeIcon(clickEvent.target, "fa-compress");
                    }

                    dialog._$getDialogEl().dialog("option", options);

                    dialog._isExpanded = !dialog._isExpanded;
                }
            }
        ];
    }

    async render(context, dialog, html=null) {
        // if (this.discriminator) {
        //     dialog.destroy();
        // }

        if (this._isRendering === false) {
            this._isRendering = true;

            if (!html)
                html = await dialog.htmlFabricator(context, dialog);
        
            let span = document.createElement("span");
            span.innerHTML = html;

            let dialogEl = span.querySelector("#" + dialog.dialogElementId);
            dialog.discriminator = dialogEl.getAttribute("class");

            let instantializeDialog;

            if (!this.$dialogElement) { // Dialog does not exist in DOM and must be instantialized
                this.dialogElement = span;
                this.$dialogElement = $(span);
                
                $('body').append(this.dialogElement);
                dialog._$getDialogEl().dialog( dialog.dialogOptions );
            }
            else { // Dialog already exists in DOM -- let's update its HTML instead
                this.dialogElement.innerHTML = "";
                this.$dialogElement.append(span);
                instantializeDialog = false;
            }

            let $buttonHolder = $("<span id='railing'></span>");

            for (let i = 0; i < this.headerButtons.length; i++) {1
                const buttonConfig = this.headerButtons[i];

                let marginClass = "";
                if (i != this.headerButtons.length)
                    marginClass = "ms-3";

                $buttonHolder.append(
                    $(`<span class='dialogHeaderButton ${marginClass} float-end' data-mdb-toggle='tooltip' title='${buttonConfig.tooltip}'> <i class='fas ${buttonConfig.icon}' </span>`)
                        .on('click', (clickEvent) => { buttonConfig.action(dialog, clickEvent) })
                )
            }

            dialog._$getDialogEl().prepend($buttonHolder);
            dialog.onRenderedCallback(dialog, context);

            this._isRendering = false;
        }
        else {
            console.warn("Dialog is already rendering...")
        }
    }
}

class DialogEventCommunicationLane {
    constructor(dialogElement) {
        this.dialogElement = dialogElement;
    }

    /**
     * Send a message to the recipient dialog instance, through an event on the dialog element
     * @param {*} typeName A discriminating name for this specific message
     * @param {*} payload Payload
     */
    send(typeName, payload) {
        this.dialogElement.dispatchEvent(new CustomEvent("laneCommunication", { "detail": { name: typeName, payload: payload } }));
    }
}

class FakeOutDialogEventCommunicationLane {
    constructor(dialogElementId) {
        this.dialogElementId = dialogElementId;
    }

    send(typeName, payload) {
        window.MessagesFacility.send("inspectEventDialog", payload, typeName);
    }
}


export class DialogManager {
    constructor ({ managerName, dialogs, allowMultipleOpenAtOnce=true, renderInChain=false }) {
        this.managerName = managerName;
        this.allowMultipleOpenAtOnce = allowMultipleOpenAtOnce;

        /// Designates if we are to render the subsequently triggered dialogs in a chain -- side by side
        this.renderInChain = renderInChain;

        this._listenForUpdatedEvent();
        this._listenForSubmitEvent();
        this._listenForCloseAllEvent();
        this._listenForReloadEvent();
        this._listenForCloseDialogEvent();
        this._listenForDataUpdateEvent();

        this._dialogRepository = new Map(dialogs);
        this.context = {};
    }
    
    async loadDialogHtml( 
            { url, managerName, dialogId, dialogTitle=undefined, customParameters=undefined } = {}) {
        const params = new URLSearchParams({
            managerName: managerName,
            dialogId: dialogId,
            title: dialogTitle,
            ...customParameters
        });

        let mutated_url = `${url}?${params.toString()}`;
        return await fetch(mutated_url).then(response => response.text());
    }

    $getDialogElement(dialogId) {
        return this._dialogRepository.get(dialogId)._$getDialogEl();
    }

    setContext(ctxObj) {
        this.context = ctxObj;
    }

    async reloadDialog(dialogId, customHtml=undefined) {
        await this._dialogRepository
            .get(dialogId)
            .refresh(this.context, customHtml);
    }

    openDialog(dialogId) {
        if (this._dialogRepository.has(dialogId)) {
            this._dialogRepository.get(dialogId).render(this.context);
            this._setTriggers();
        }
        else {
            console.error(`Dialog with key ${dialogId} does not exist. Repository: `, this._dialogRepository);
        }
    }

    setTitle(dialogId, newTitle) {
        this._dialogRepository.get(dialogId)._$getDialogEl().dialog("option", "title", newTitle);
    } 

    closeDialog(dialogId) {
        const dialog = this._dialogRepository.get(dialogId);
        dialog.onDestroy();
        dialog.close();
    }

    closeAllDialogs(triggerOnDestroy=false) {
        this._dialogRepository.forEach( (dialog) => {
            if (triggerOnDestroy)
                dialog.onDestroy();
            dialog.close();
        });
    }

    // Listen for data update events -- dialog.data synced to dialog.context in manager SOI
    _listenForDataUpdateEvent() {
        document.addEventListener(`${this.managerName}.dataUpdate`, (event) => {
            const dialogId = event.detail.dialog;
            const propertyName = event.detail.prop;
            const newPropertyValue = event.detail.propValue;

            const dialog = this._dialogRepository.get(dialogId);
            dialog.internalDialogData[propertyName] = newPropertyValue;
        })
    }

    _listenForCloseDialogEvent() {
        document.addEventListener(`${this.managerName}.closeDialog`, (e) => {
            this.closeDialog(e.detail.dialog);
        });
    }

    _listenForCloseAllEvent() {
        document.addEventListener(`${this.managerName}.close`, (e) => {
            this.closeAllDialogs();
        })
    }

    /**
     * Listens for custom reload events being fired, allowing us to reload a dialog from 
     * anywhere. The dialog name must be specified in detail.
     * When called with valid dialog name it will reload the dialog with the given dialog name.
     */
    _listenForReloadEvent() {
        document.addEventListener(`${this.managerName}.reload`, (e) => {
            this.reloadDialog(e.detail.dialog);
        })
    }

    _listenForUpdatedEvent() {
        document.addEventListener(`${this.managerName}.hasBeenUpdated`, (e) => {
            this._dialogRepository.get(e.detail.dialog).onUpdatedCallback(this.context);
        });
    }

    _listenForSubmitEvent() {
        document.addEventListener(`${this.managerName}.submit`, async (e) => {
            let dialog = this._dialogRepository.get(e.detail.dialog);
            let submitResult = await dialog.onSubmit(this.context, e.detail, this, dialog);  // Trigger the dialogs onSubmit handling
            if (submitResult !== false) {
                dialog.onUpdatedCallback(this.context);  // Trigger the dialogs on update handling
            }
        })
    }

    _setTriggers() {
        this._dialogRepository.forEach( (value, key, map) => {
            if (value.triggerElementId !== undefined) {
                $("#" + value.triggerElementId).on('click', () => {
                    this.context.lastTriggererDetails = undefined;
                    this.context.lastTriggererElement = document.querySelector(`#${value.triggerElementId}`);
                    value.render(this.context);
                });
            }
        })
    }

    _makeAware() {
        this._setTriggers();

        this._dialogRepository.forEach(( value, key, map) => {
            if (value.triggerByEvent === true) {
                let triggerName = value.dialogElementId;
                if (value.customTriggerName !== undefined) {
                    triggerName = value.customTriggerName;
                }

                document.addEventListener(`${this.managerName}.${triggerName}.trigger`, (event) => {
                    if (this.allowMultipleOpenAtOnce === false) {
                        this.closeAllDialogs();
                    }

                    this.context.lastTriggererDetails = event.detail;
                    value.render(this.context);

                    debugger;

                    let parent = event.detail.$parent;
                    let overrideRenderInChain = event.detail.renderInChain;
                    let current = $(value._$getDialogEl());

                    if (parent && this.renderInChain || overrideRenderInChain) {
                        // $(parent).on("dialogdrag", function (event, ui) {
                        //     $(value._$getDialogEl()).dialog("option", "position", { my: "left+20 top", at: "right top", of: parent.parentNode });
                        // });
                        // current.on("dialogdrag", function (event, ui) {
                        //     // $(parent).dialog("option", "modal", true);
                        //     // $(parent).dialog("option","position", { my: "right top", at: "left top", of: current[0].parentNode } )
                        // });

                        value.dialogOptions = { 
                            dialogClass: "slave-dialog" + value.dialogOptions.dialogClass !== undefined ? (" " + value.dialogOptions.dialogClass) : "",
                            classes: {
                                "ui-dialog": "slave-dialog"
                            },
                            position: { my: "left top", at: "right top", of: parent.parentNode },
                            modal: true,
                            height: parent.parentNode.offsetHeight,
                            width: 600,
                            show: { effect: "slide", direction: "left", duration: 400 }
                        }
                    }
                });
            }
        });
    }
}