/**
 * @classdesc 
 * Extension class for the MDB (Material Bootstrap) select, allowing for lazy asynchronous server-side searching 
 * in a Select2 like fashion.
*/
class ExtendedSelect {
    /** 
     * Construct a new select extension instance
     * @param {object} jqElement - The element of the select to which to extend
     * @param {string} getUrl - The URL which we are to query when user is searching
     * @param {string} initialSearchValue - The search value to run with on the FIRST load of the select.
     * @param {Array} extraParams - An array of extra parameters to add to the request body
     * @param {Array} extraHeaders - An array of extra headers to add to the request
     * @param {object} dataParser - Function to be used to parse the received data. Implement custom if API returns in a format not covered by the default data parser.
     * @param {int} searchThreshold - How many characters need to be entered before we start searching
    */
    constructor ( { 
        jqElement, 
        getUrl, 
        initialSearchValue="", 
        extraParams=undefined, 
        extraHeaders=undefined,
        dataParser=undefined,
        searchThreshold=3 } = {} ) {

        this.jqElement = jqElement;
        this.getUrl = getUrl;
        this.extraParams = extraParams;
        this.searchThreshold = searchThreshold;
        this.extraHeaders = extraHeaders;
        this.dataParser = (dataParser === undefined ? this.defaultItemParser : dataParser);
        this.currentlySelectedValues = [];

        console.log(this.jqElement);

        this.jqElement[0].addEventListener('open.mdb.select', (e) => {
            this.bindToSearch();
        });

        this.search(initialSearchValue);    // initialize the select, as to populate data
    }

    /**
     * Default item parser for parsing data received from the API. Does not cover secondary_text grouping.
     * @param {object} item - Item to parse
     * @returns Parsed item
     */
    /* default for parsing from a fetched item into a html option element */
    defaultItemParser(item) {
        return {
            value: item.id,
            text: item.text,
            secondary_text: "",
        };
    }

    /**
     * Check if this extension is valid.
     * @returns {bool} - A bool indicating if extending this select is actually possible.
     */
    isValid() {
        return this.jqElement[0].dataset.mdbFilter === "true";
    }

    /**
     * Bind an event listener to the selects search input.
     * @async
     * @returns
    */
    async bindToSearch () {
        let ext = this;
        var observer = new MutationObserver(function (mutations, me) {
            var filterField = document.getElementsByClassName('select-filter-input')[0];
            var delayTimer;
            if (filterField) {
                filterField.addEventListener("input", function () {
                    let searchValue = $(filterField).val();
                    if (ext.searchThreshold <= searchValue.length || searchValue === "") {
                        clearTimeout(delayTimer);
                        delayTimer=setTimeout(function () {
                            ext.search({ term: searchValue });
                        }, 300)   
                    }
                });

                me.disconnect();
                return;
            }
        })

        observer.observe(document, {
            childList: true,
            subtree: true
        })
    }

    /**
     * Query the API
     * @async
     * @param {string} term - The search string
     * @returns {Array} - An array of objects parsed from the query response with the data parser.
     */
    async search( { term } = {} ) {

        let data = {}
        if (term === undefined) {
            term = "";
        }
        if (this.extraParams !== undefined) {
            data = this.extraParams;
        }
        data.term = term;

        let headers = {}
        if (this.extraHeaders !== undefined) {
            headers = this.extraHeaders;
        }
        headers["Content-Type"] = "application/json";

        const response = await fetch(this.getUrl, {
            method: 'POST',
            headers,
            credentials: "same-origin",
            body: JSON.stringify(data)
        });

        let respJson = await response.json();
        let parsedEntities = JSON.parse(respJson);

        let optGroups = this.jqElement[0].querySelectorAll("optgroup");
        for (let i = 0; i < optGroups.length; i++) {
            optGroups[i].remove();
        }

        let options = this.jqElement[0].querySelectorAll("option");
        for (let i = 0; i < options.length; i++) {
            options[i].remove();
        }

        for (let i = 0; i < parsedEntities.length; i++) {
            let item = this.dataParser(parsedEntities[i]);

            let parentEl = this.jqElement;
            
            let isOptgroup = item.options !== undefined && Array.isArray(item.options);
            
            if (isOptgroup) {
                parentEl = document.createElement('optgroup');
                parentEl.setAttribute('label', item.label);
                this.jqElement.append(parentEl);
            }

            let secondary = (item.secondary_text !== undefined && item.secondary_text !== "" ? "data-mdb-secondary-text='" + item.secondary_text + "'" : "")
            parentEl.append("<option value='" + item.value + "'" + secondary + ">" + item.text + "</option>");
        }
        
        return respJson;
    }
}