_STD_TAB_DISTANCE = 100;

class QuickTabOrchestrator {
    constructor(quickTabs) {
        this._tabMap = new Map();

        if (Array.isArray(quickTabs)) { 
            quickTabs.forEach( (tab) => {
                this.addTab(tab);
            })
        }
    }

    get _tabsLength() {
        return this._tabMap.size;
    }

    _orchestrate() {

    }

    addTab({ element, tabName, headerHtml, startOpened=false } = {}) {
        let tab = new QuickTab({
            element: element,
            tabName: tabName,
            pushAway: this._tabsLength * _STD_TAB_DISTANCE,
            headerHtml: headerHtml,
            startOpened: startOpened,
            callMeOnInit: this._orchestrate,
        });
        this._tabMap.set(tabName, tab);
    }

    removeTab({ element, tabName, headerHtml, startOpened=false }) {
        this._tabMap.removeTab(tab.name, tab);
    }
}

class QuickTab {
    constructor({ element, tabName, headerHtml, pushAway, startOpened=false, callMeOnInit=undefined } = {}) {
        this._element = element;
        this.name = tabName;
        this._headerHtml = headerHtml;

        this._bodyHtml = this._element.innerHTML;

        this.state = "closed";

        this._PUSHAWAY = pushAway;

        this._HEADER_ELEMENT = undefined;
        this._BODY_ELEMENT = undefined;
        this._OPENNAV_ELEMENT = undefined;
        this._INNERWRAPPER_ELEMENT = undefined;

        this._OPENED_EVENT = new Event('quickTab.opened');
        this._CLOSED_EVENT = new Event('quickTab.closed');

        this._init();

        if (startOpened === false) {
            this._INNERWRAPPER_ELEMENT.hide();
        }
    }

    _init () {
        let root = $('<div></div>')
        root.addClass("quickTab");
        console.log(this._bodyHtml)

        root.append( $(`<div class='quickTab_header' id='quickTab_header_${this.name}'> ${this._headerHtml}  </div>`) );
        let innerWrapper = $(`<div id='quickTab_innerWrapper_${this.name}'></div>`);
        innerWrapper.append( $(`<div class='quickTab_hider text-center' id='quickTab_hider_${this.name}'> <a id='hideQuickTab_${this.name}'> <i class='fas fa-chevron-down'></i> </a> </div>`) );
        innerWrapper.append( $(`<div class='quickTab_body'> ${this._bodyHtml} </div>`) );
        root.append( innerWrapper );

        // if (this._PUSHAWAY !== undefined) {
        //     root[0].style.marginRight = `${this._PUSHAWAY}px`;
        // }

        this._element.innerHTML = root[0].outerHTML;

        this._HEADER_ELEMENT = $(`#quickTab_header_${this.name}`);
        this._BODY_ELEMENT = $(`#quickTab_body_${this.name}`);
        this._OPENNAV_ELEMENT = $(`#quickTab_hider_${this.name}`);
        this._INNERWRAPPER_ELEMENT = $(`#quickTab_innerWrapper_${this.name}`);
        
        this._listenToCloseClick();
        this._listenToHeaderClick();
    }

    _listenToCloseClick() {
        this._OPENNAV_ELEMENT.on('click', () => {
            this.close();
        })
    }

    _listenToHeaderClick() {
        this._HEADER_ELEMENT.on('click', () => {
            this.open();
        })
    }

    open() {
        if (this.state === "open") {
            console.debug("QuickTab open was triggered, but tab is already open!");
            return;
        }

        this.state = "open";
        this._INNERWRAPPER_ELEMENT.show();
        

        this._fireTabOpenedEvent();
    }

    close() {
        if (this.state === "closed") {
            console.debug("QuickTab close was triggered, but tab is already closed!")
            return;
        }

        this.state = "closed";
        this._INNERWRAPPER_ELEMENT.hide();
        console.log("==> Close")
        console.log(this._INNERWRAPPER_ELEMENT)

        this._fireTabClosedEvent();
    }

    _fireTabOpenedEvent() {
        this._element.dispatchEvent(this._OPENED_EVENT);
    }

    _fireTabClosedEvent() {
        this._element.dispatchEvent(this._CLOSED_EVENT);
    }
}