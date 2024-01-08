import { Popover } from "./popover.js";

export const NORMAL_CASCADE_BEHAVIOUR = Symbol("NormalCascadeBehaviour")
export const PARENT_INDEPENDENT_CASCADE_BEHAVIOUR = Symbol("ParentIndependentCascadeBehaviour")

function getCascadeSettingsFromCascadeBehaviour(cascadeBehaviour) {
    switch(cascadeBehaviour) {
        case NORMAL_CASCADE_BEHAVIOUR:
            return { };
        case PARENT_INDEPENDENT_CASCADE_BEHAVIOUR:
            return { 
                "three_state": false,
                "cascade": "up+undetermined",
            };
        default:
            throw Error("No such cascade behaviour known!");
    }
}

export class AdvancedTreeFilter extends Popover {
    constructor ( { 
        title,
        triggerElement, 
        wrapperElement, 
        data,
        selectionPresets,
        onSelectionUpdate,
        onSubmit,
        treeSrcUrl,
        cascadeBehaviour=NORMAL_CASCADE_BEHAVIOUR,
        isSearchable=false,
        onChange=null,
        } = {} ) 
    { 
        super({
            triggerElement: triggerElement,
            wrapperElement: wrapperElement,
        });

        this.title = title;
        this.isSearchable = isSearchable;
        this.cascadeBehaviour = cascadeBehaviour;

        this.onChange = onChange;

        this._instanceDiscriminator = crypto.randomUUID();

        this.treeSrcUrl = treeSrcUrl;

        this._selectionPresets = selectionPresets;
        this._data = data;
        this._onSubmit = onSubmit;
        
        this.isRendered = false;

        this.onSelectionUpdate = onSelectionUpdate;

        this._selectedMap = new Map();
        this._categorySearchMap = new Map();

        this._render();
        this._bindOnChange();
    }

    async _loadTreeJson() {
        return fetch(this.treeSrcUrl, {
            method: 'GET'
        }).then(response => response.json())
    }
    
    _$getJsTreeElement() {
        return $(this._jsTreeElement);
    }

    _bindOnChange() {
        if (typeof this.onChange === "function") {
            $(this._jsTreeElement).on("changed.jstree", (e, data) => {
                this.onChange( this, data );
            });
        }
    }

    getSelectedValues() {
        return Array.from(this._selectedMap.keys());
    }
        
    clear() {
        this._selectedMap.clear();
        $(this._jsTreeElement).jstree("deselect_all");

        this._onSubmit(this, [], []);
    }

    _search(term) {
        $(this._jsTreeElement).jstree("search", term, false, true);
    }

    _render() {
        this.wrapperElement.innerHTML = "";
        if (!this.wrapperElement.classList.contains("popover_wrapper")) {
            this.wrapperElement.classList.add("popover_wrapper");
        }

        let popoverContentEl = document.createElement("div");
        popoverContentEl.classList.add("popover_content", this._instanceDiscriminator);
        this.wrapperElement.appendChild(popoverContentEl);

        let titleEl = document.createElement("h4");
        titleEl.innerText = this.title;
        popoverContentEl.appendChild(titleEl);

        if (this.isSearchable) {
            let searchInput = document.createElement("input");
            searchInput.setAttribute("type", "search");
            searchInput.setAttribute("placeholder", "Søk...");
            searchInput.classList.add("form-control", "mb-1");
            
            searchInput.addEventListener("input", (event) => { 
                this._search( event.target.value );
            })

            popoverContentEl.appendChild(searchInput);
        }

        let actionsBtnGroup = document.createElement("div");
        actionsBtnGroup.classList.add("btn-group", "w-100", "shadow-0");
        actionsBtnGroup.setAttribute("role", "group");
        actionsBtnGroup.setAttribute("aria-label", "Filter Actions");

        let filterBtn = document.createElement("button");
        filterBtn.setAttribute("type", "button");
        filterBtn.classList.add("btn", "wb-btn-secondary");
        filterBtn.innerHTML = "<i class='fas fa-filter'></i> Filtrer";
        filterBtn.setAttribute("data-mdb-toggle", "tooltip");
        filterBtn.setAttribute("data-mdb-placement", "top");
        filterBtn.setAttribute("title", "Filtrer med gjeldende valg");

        filterBtn.addEventListener("click", (event) => {
            this._selectedMap.clear();
            const selectedNodes = $(this._jsTreeElement).jstree("get_selected", true);
            const undeterminedNodes = $(this._jsTreeElement).jstree("get_undetermined", true);

            this._onSubmit(this, selectedNodes, undeterminedNodes);
        });

        actionsBtnGroup.appendChild(filterBtn);

        let clearBtn = document.createElement("button");
        clearBtn.setAttribute("type", "button");
        clearBtn.classList.add("btn", "wb-btn-secondary");
        clearBtn.innerHTML = "<i class='fas fa-times'></i>";
        clearBtn.setAttribute("data-mdb-toggle", "tooltip");
        clearBtn.setAttribute("data-mdb-placement", "top");
        clearBtn.setAttribute("title", "Fjern alle valg");

        clearBtn.addEventListener("click", (event) => {
            this.clear();
        });

        actionsBtnGroup.appendChild(clearBtn);

        popoverContentEl.appendChild(actionsBtnGroup);

        let treeHolder = document.createElement("div");
        treeHolder.style = "max-height: 35em; overflow: scroll;"
        popoverContentEl.appendChild(treeHolder);
        this._jsTreeElement = treeHolder;

        this._loadTreeJson()
            .then(treeValidObj => {
                this._jsTree = $(treeHolder).jstree({
                    'checkbox': getCascadeSettingsFromCascadeBehaviour(this.cascadeBehaviour),
                    'plugins': [ 'checkbox', 'search', 'changed' ], 
                    'core': {
                        "themes" : { "icons": false },
                        'data': treeValidObj,
                        'multiple': true,
                    }
                });
            });
    }
}