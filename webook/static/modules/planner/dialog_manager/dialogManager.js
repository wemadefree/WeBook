 export class Dialog {
    constructor ({ dialogElementId, triggerElementId, htmlFabricator, onRenderedCallback, onUpdatedCallback, onSubmit, onPreRefresh, dialogOptions, triggerByEvent=false, customTriggerName=undefined } = {}) {
        this.dialogElementId = dialogElementId;
        this.triggerElementId = triggerElementId;
        this.customTriggerName = customTriggerName;
        this.triggerByEvent = triggerByEvent,
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

    async render(context) {
        // this.prepareDOM();
        $( `#${this.dialogElementId}` ).dialog( "destroy" ).remove();
        this.destroy();

        if (this.isOpen() === false) {
            $('body')
                .append(await this.htmlFabricator(context))
                .ready( () => {
                    this._$getDialogEl().dialog( this.dialogOptions );
                    this.onRenderedCallback(this, context);
                    this._$getDialogEl().dialog("widget").find('.ui-dialog-titlebar-close')
                        .html("<i class='fas fa-times text-danger' style='font-size: 24px'></i>")
                        .click( () => {
                            console.log("Clicked X button")
                            this.destroy();
                        });
                    
                });
        }
    }

    async refresh(context, html) {
        if (this.isOpen() === true) {
            if (this.onPreRefresh !== undefined) {
                await this.onPreRefresh(this);
            }

            if (html === undefined) {
                html = await this.htmlFabricator(context);
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
            this.destroy()
        }
    }

    getInstance() {
        return $( `#${this.dialogElementId}` ).dialog( "instance" );
    }

    destroy() {
        $( `#${this.dialogElementId}` ).dialog( "destroy" ).remove();
    }

    isOpen() {
        var $dialogElement = this._$getDialogEl();

        if ($dialogElement[0] === undefined || this.getInstance() === false || $($dialogElement).dialog("isOpen") === false) {
            return false;
        }

        return true;
    }
}


export class DialogManager {
    constructor ({ managerName, dialogs }) {
        this.managerName = managerName;

        this._listenForUpdatedEvent();
        this._listenForSubmitEvent();
        this._listenForCloseEvent();
        this._listenForReloadEvent();

        this._dialogRepository = new Map(dialogs);
        this.context = {};
    }

    setContext(ctxObj) {
        this.context = ctxObj;
    }

    reloadDialog(dialogId, customHtml=undefined) {
        this._dialogRepository.get(dialogId).refresh(this.context, customHtml);
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

    closeDialog(dialogId) {
        this._dialogRepository.get(dialogId).close();
    }

    closeAllDialogs() {
        this._dialogRepository.forEach( (dialog) => {
            dialog.close();
        })
    }

    _listenForCloseEvent() {
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
            this._dialogRepository.get(e.detail.dialog).onUpdatedCallback();
        });
    }

    _listenForSubmitEvent() {
        document.addEventListener(`${this.managerName}.submit`, async (e) => {
            var dialog = this._dialogRepository.get(e.detail.dialog);
            await dialog.onSubmit(this.context, e.detail);  // Trigger the dialogs onSubmit handling
            dialog.onUpdatedCallback();                     // Trigger the dialogs on update handling
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

                var triggerName = value.dialogElementId;
                if (value.customTriggerName !== undefined) {
                    triggerName = value.customTriggerName;
                }

                document.addEventListener(`${this.managerName}.${triggerName}.trigger`, (detail) => {
                    this.context.lastTriggererDetails = detail.detail;
                    value.render(this.context);
                });
            }
        });
    }
}