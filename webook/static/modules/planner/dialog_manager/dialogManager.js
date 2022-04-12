 export class Dialog {
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

    async render(context) {
        this.prepareDOM();

        if (this.isOpen() === false) {
            $('body')
                .append(await this.htmlFabricator(context))
                .ready( () => {
                    this.onRenderedCallback(this);
                    this._$getDialogEl().dialog( this.dialogOptions );       
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


export class DialogManager {
    constructor ({ managerName, dialogs }) {
        this.managerName = managerName;

        this._listenForUpdatedEvent();
        this._listenForSubmitEvent();

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
        this._dialogRepository.values.forEach( (dialog) => {
            dialog.close();
        })
    }

    _listenForUpdatedEvent() {
        document.addEventListener(`${this.managerName}.hasBeenUpdated`, (e) => {
            this._dialogRepository.get(e.detail.dialog)
                .onUpdatedCallback();
        });
    }

    _listenForSubmitEvent() {
        console.log(`${this.managerName}.submit`)
        document.addEventListener(`${this.managerName}.submit`, (e) => {
            console.info("==> Submit caught.")
            this._dialogRepository.get(e.detail.dialog)
                .onSubmit(this.context, e.detail);
        })
    }

    _setTriggers() {
        this._dialogRepository.forEach( (value, key, map) => {
            if (value.triggerElementId !== undefined) {
                console.log(value.triggerElementId)
                $("#" + value.triggerElementId).on('click', () => {
                    value.render(this.context);
                });
            }
        })
    }

    _makeAware() {
        this._setTriggers();
    }
}