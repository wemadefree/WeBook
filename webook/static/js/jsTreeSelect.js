import { Popover } from "./popover.js";

/**
 * JS Tree Select
 * A custom component to be used in tandem with the excellent JSTree plugin.
 * Leveraging the Popover class from popover.js we create a select-like component that can be used to select elements in a JSTree rendered
 * inside of the Popover, allowing a smooth, easy and intuitive way of selecting items in a nested structure.
 */
export class JSTreeSelect {
    /** 
     * Construct a new JSTreeSelect instance
     * @param {Element} element - Wrapper element where the JSTreeSelect component is to be injected
     * @param {string} treeJsonSrcUrl - URL to an endpoint from which a JSTree compliant JSON document can be retrieved to populate the tree with
     * @param {any} initialSelected - The id or key of the initially selected item, this is optional.
     * @param {Boolean} allowMultipleSelect - Designates if one is able to select multiple nodes in the tree, or only one. True if multiple, False if only one is selectable.
     * @param {String | Function} noneSelectedLabelText - Given either a function or a string this will be the text of the label when a selection has been made in the component. Is optional.
     * @param {String | Function} selectFirstTimeButtonText - A string or a function providing the text shown on the "Select" button before selecting a value. On the component, not in Popover.
     * @param {String | Function} changeSelectedValueButtonText - A string or a function providing the text shown on the "Select" button after selecting a value. On the component, not in Popover.
     * @param {String | Function} popoverSaveChoicesButtonText - A string or a function providing the text shown on the "Save" button within the Popover.
     * @param {String | Function} invalidFeedbackText - A string or a function providing the text shown when no item has been selected, and validation has been called.
    */
    constructor( { 
        element, 
        treeJsonSrcUrl,
        initialSelected=null,
        onValueSet=null,
        allowMultipleSelect=false,
        isSearchable=true,
        noneSelectedLabelText="None selected",
        valueSelectedLabelText=undefined,
        selectFirstTimeButtonText="Select",
        changeSelectedValueButtonText="Change",
        popoverSaveChoicesButtonText="Save choices",
        invalidFeedbackText=window.WEBOOK_MESSAGES?.selectAnItem || "Please select an item"} = {} ) {

        this.element = element;
        this.srcUrl = treeJsonSrcUrl;
        this.allowMultipleSelect = allowMultipleSelect;

        this.isSearchable = isSearchable;

        this.onValueSet = onValueSet;
        this.selected = initialSelected;

        this.invalidFeedbackText = invalidFeedbackText;

        this.noneSelectedLabelText = noneSelectedLabelText;
        this.valueSelectedLabelText = valueSelectedLabelText === undefined ? this._standardValueSelectedLabelText : valueSelectedLabelText;
        this.popoverSaveChoicesButtonText = popoverSaveChoicesButtonText;
        this.selectFirstTimeButtonText = selectFirstTimeButtonText;
        this.changeSelectedValueButtonText = changeSelectedValueButtonText;

        this._popover = null;
        this._jsTree = null;

        this._render();
    }

    /**
     * Set the value of this.selected.id as the selected_node of the JsTree element, achieving the effect of mirroring internal state
     * to the JSTree instance.
     */
    _jsTreeSet() {
        $(this._jsTreeElement).jstree('select_node', this.selected.id);

        let node = $(this._jsTreeElement).jstree(true).get_node(this.selected.id);
        this.selected.parent = node.parent;
        this.selected.text = node.text;

        if (this.selected.parent) {
            this.selected.parent = $(this._jsTreeElement).jstree(true).get_node(this.selected.parent);
            this._labelElement.innerHTML = this._generateLabelElement().innerHTML;
        }
    }

    _standardValueSelectedLabelText(selected) {
        return selected.text;
    }

    /**
     * Given id and text set the selected value, and reflect this on the component, updating the label text.
     * @param {*} id 
     * @param {*} text 
     * @param {*} directParentId
     */
    _setSelectedValue(id, text, directParentId) {
        const node = $(this._jsTreeElement).jstree(true).get_node(id);

        this.selected = { id: id, text: node.text, parent: $(this._jsTreeElement).jstree(true).get_node(node.parent) };
        this._labelElement.innerHTML = this._generateLabelElement().innerHTML;
        this._hideInvalidFeedback();

        const event = new Event("change");
        this.element.dispatchEvent(event);
    }

    /**
     * Get the id or key of the currently selected value. If no value has been selected
     * then an error will be thrown.
     * @returns id or key of the selected value, if any
     */
    getSelectedValue() {
        if (!this._hasSelectedValue() || this.selected.id === null || this.selected.id === "null")
            return undefined;
            
        return this.selected.id;
    }

    setSelected(id) {
        const jsTree = $(this._jsTreeElement).jstree(true);
        if (jsTree === false) { // if jsTree is false, then jsTree is not initialized yet, so we stage the set value.
            this.selected={ id: id };
            return;
        }

        /** 
         * It is possible for JSTREE to be initialized, but not having finished loading the tree json from the endpoint yet
         * We ascertain this state by get_node being False -- and again we default to staging the value.
        */
        const selected = $(this._jsTreeElement).jstree(true).get_node(id);
        if (selected === false)
        {
            this.selected={ id: id };
            return;
        }

        this._setSelectedValue(selected.id, selected.text, selected.parent);
    }
    
    /**
     * Check if a value has been selected
     * @returns True if a value has been selected, False if a value has not been selected
     */
    isValid()  {
        return this._hasSelectedValue();
    }

    /**
     * Render invalid feedback text / alert in the DOM.
     */
    showInvalidFeedback() {
        let invalidText = document.createElement("span");
        invalidText.classList.add("text-danger");
        invalidText.innerText = this.invalidFeedbackText;
        this._activeInvalidTextElement = invalidText;
        this.element.append(invalidText);
    }

    _hideInvalidFeedback() {
        if (this._activeInvalidTextElement !== undefined){
            this._activeInvalidTextElement.remove();
            this._activeInvalidTextElement = undefined;
        }
    }
 
    /**
     * Check if a value has been selected, and if so return true, otherwise false.
     * @returns a boolean value indicating if a value has been selected or not
     */
    _hasSelectedValue() { 
        return this.selected !== undefined && this.selected !== null;
    }

    /**
     * Generate the label element, which contains text indicating the status of the component and value selection.
     * @returns a html element, the label
     */
    _generateLabelElement() {
        let labelElement = document.createElement('span');
        
        if (this._hasSelectedValue())
            labelElement.innerHTML = typeof this.valueSelectedLabelText === "function" ? this.valueSelectedLabelText( this.selected ) : this.valueSelectedLabelText;
        else
            labelElement.innerHTML = typeof this.noneSelectedLabelText === "function" ? this.noneSelectedLabelText() : this.noneSelectedLabelText;

        return labelElement;
    }

    _search(term) {
        $(this._jsTreeElement).jstree("search", term, false, true);
    }

    /**
     * Generate a HTML element containing the trigger for the popover containing the JS Tree, and a button for triggering the
     * said popover to show. As a side effect this function will also  set the variable _popover on the instance to the popover instance
     * that it creates in tandem with its generated elements.
     */
    _generateJsTreeTriggerElement() {
        let wrapper = document.createElement("div");

        let buttonElement = document.createElement("button");
        buttonElement.setAttribute("type", "button");
        buttonElement.innerText = this._hasSelectedValue ? this.selectFirstTimeButtonText : this.changeSelectedValueButtonText;
        buttonElement.classList.add("btn", "wb-btn-secondary");
        wrapper.appendChild(buttonElement);

        let popoverWrapper = document.createElement("div");
        popoverWrapper.classList.add("popover_wrapper");
        wrapper.appendChild(popoverWrapper);

        let popoverContent = document.createElement("span");
        popoverContent.classList.add("popover_content");
        popoverWrapper.appendChild(popoverContent);

        if (this.isSearchable) {
            let searchInput = document.createElement("input");
            searchInput.setAttribute("type", "search");
            searchInput.setAttribute("placeholder", window.WEBOOK_MESSAGES?.search || "Search...");
            searchInput.classList.add("form-control", "mb-1");
            
            searchInput.addEventListener("input", (event) => { 
                this._search( event.target.value );
            });

            popoverContent.appendChild(searchInput);
        }

        let treeElement = document.createElement("div");
        popoverContent.appendChild(treeElement);

        let submitButtonInsidePopoverElement = document.createElement("button");
        submitButtonInsidePopoverElement.setAttribute("type", "button");
        submitButtonInsidePopoverElement.innerText = this.popoverSaveChoicesButtonText;
        submitButtonInsidePopoverElement.classList.add("btn", "wb-btn-main", "float-end", "mt-2");
        submitButtonInsidePopoverElement.onclick = () => { 
            const selected = $(this._jsTreeElement).jstree("get_selected", true)[0];
            this._setSelectedValue(selected.id, selected.text, selected.parent);

            this._popover.show(); //hide --toggle
        };
        popoverContent.appendChild(submitButtonInsidePopoverElement);
        
        this._jsTreeElement = treeElement;

        this._loadTreeJson()
            .then(treeValidObj => {
                this._jsTree = $(treeElement).jstree({
                    'checkbox': {
                        "three_state": false,
                        "cascade": "up+undetermined",
                    },
                    'plugins': [ 'checkbox',  'search',], 
                    'core': {
                        'data': treeValidObj,
                        'multiple': false,
                    }
                });

                $(treeElement).on('loaded.jstree', () => {
                    if (this.selected !== null) {
                        this._jsTreeSet();
                    }
                });
                $(treeElement).on('changed.jstree', (e, data) => {
                    if (typeof this.onValueSet === "function")
                        this.onValueSet(data);
                });
            });

        this._popover = new Popover({
            triggerElement: buttonElement,
            wrapperElement: popoverWrapper,
        });

        return wrapper;
    }

    /**
     * Compose the various parts of the component, and render it into the given "base" element of the component.
     */
    _render() {
        let wrapper = document.createElement("div");
        wrapper.classList.add("border", "border-1", "p-2", "ps-3", "pe-3", "rounded-2", "d-flex");
        wrapper.style = "align-items:center; justify-content: space-between;";
        this._labelElement = this._generateLabelElement();
        wrapper.append( this._labelElement, this._generateJsTreeTriggerElement() );

        this.element.appendChild(wrapper);
    }

    /**
     * Get the JsTree tree object from the defined srcUrl
     * The srcUrl endpoint should be able to provide Json in a structure
     * that is acceptable to JsTree.
     * @returns An object
     */
    async _loadTreeJson() {
        return fetch(this.srcUrl, {
            method: 'GET'
        }).then(response => response.json())
    }
}