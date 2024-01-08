export const _FC_EVENT = Symbol('EVENT');
export const _FC_RESOURCE = Symbol("RESOURCE");
export const _NATIVE_ARRANGEMENT = Symbol("NATIVE_ARRANGEMENT");
export const _NATIVE_LOCATION = Symbol("NATIVE_LOCATION");
export const _NATIVE_PERSON = Symbol("NATIVE_PERSON");



/**
 * The standard calendar color provider
 */
export class StandardColorProvider {
    getColor(arrangement) {
        return "green";
    }
}

export class FullCalendarEvent {
    constructor ({title,
                 start,
                 end,
                 resourceIds=[],
                 color="",
                 display="",
                 textColor="",
                 classNames=[],
                 extendedProps={}} = {}) 
    {
        this.title = title;
        this.start = start;
        this.end = end;
        this.color = color;
        this.display = display;
        this.resourceIds = resourceIds;
        this.textColor = textColor;
        this.classNames = classNames;
        this.extendedProps = extendedProps;
    }
}

export class FullCalendarResource {
    constructor ({ title,
                   id,
                   slug,
                   parentId,
                   extendedProps,
                   children = []}) {
        this.title = title;
        this.id = id;
        this.parentId = parentId;
        this.extendedProps = extendedProps;
        this.extendedProps.slug = slug;
    }
}

export class CalendarDataStore {
    _refresh()  {}
    _flush()    {}
    get()       {}
    getAll()    {}
    remove()    {}
}


class BaseStore {
    constructor () {
        this._store = new Map();
    }
    _getStoreAsArray() {
        return Array.from(this._store.values());
    }
}

export class LocationStore extends BaseStore {
    constructor (calendarBase) {
        super();

        this._store = new Map();
        this._refreshStore();
        this._calendar = calendarBase;
    }

    async _refreshStore() {
        this._flushStore();
        return await fetch("/arrangement/location/calendar_resources")
            .then(response => response.json())
            .then(obj => { obj.forEach((location) => {
                this._store.set(location.slug, location);
            })});
    }

    _mapToFullCalendarResource (nativeLocation) {
        return new FullCalendarResource({
            title: nativeLocation.title,
            id: nativeLocation.id,
            slug: nativeLocation.slug,
            children: nativeLocation.children,
            parentId: nativeLocation.parentId,
            extendedProps: nativeLocation.extendedProps,
        });
    }

    _flushStore() {
        this._store = new Map();
    }
    
    getAll({ get_as, filteredLocations, filteredRooms } = {}) {
        let resources = this._getStoreAsArray();

        console.log("locationStore.getAll -> ", filteredLocations, filteredRooms);

        if (filteredLocations.length > 0) {
            let slugsToIgnoreMap = new Map(filteredLocations.concat(filteredRooms).map(x => [x, true]))
            resources = resources.filter(x => slugsToIgnoreMap.has(x.id));
        }

        if (get_as === _FC_RESOURCE) {
            return resources.map((nativeResource) => this._mapToFullCalendarResource(nativeResource));
        }
        else if (get_as === _NATIVE_LOCATION) {
            return resources;
        }
    }
}

export class PersonStore extends BaseStore {
    constructor (calendarBase) {
        super();

        this._store = new Map();
        this._refreshStore();
        this._calendar = calendarBase;
    }

    async _refreshStore() {
        this._flushStore();
        return await fetch("/arrangement/person/calendar_resources")
            .then(response => response.json())
            .then(obj => { obj.forEach((person) => {
                this._store.set(person.slug, person);
            })});
    }

    _mapToFullCalendarResource (nativePerson) {
        return new FullCalendarResource({
            title: nativePerson.title,
            id: nativePerson.id,
            slug: nativePerson.slug,
            children: nativePerson.children,
            parentId: nativePerson.parentId,
            extendedProps: nativePerson.extendedProps,
        });
    }

    _flushStore() {
        this._store = new Map();
    }

    getAll({ get_as } = {}) {
        let resources = this._getStoreAsArray();
        if (get_as === _FC_RESOURCE) {
            return resources.map( (nativeResource) => this._mapToFullCalendarResource(nativeResource) );
        }
        else if (get_as === _NATIVE_LOCATION) {
            return resources;
        }
    }
}


/**
 * Stores, fetches, and provides an easy interface from which to retrieve arrangements
 */
export class ArrangementStore extends BaseStore {
    constructor (colorProvider, sourceUrl = "/arrangement/planner/arrangements_in_period") {
        super();

        this._sourceUrl = sourceUrl;
        this._store = new Map(); 
        this._refreshStore();
        this.colorProvider = colorProvider;
    }

    /**
     * Refreshes the store and returns this so you can chain in a get.
     */
    _refreshStore(time, end) {
        this._flushStore();

        let query_string = "";
        if (time !== undefined) {
            query_string = `?start=${time.startStr}&end=${time.endStr}`;
        }

        return fetch(this._sourceUrl + query_string)
            .then(response => response.json())
            .then(obj => { obj.forEach((arrangement) => {
                this._store.set(arrangement.event_pk, arrangement);
            })});
    }

    /**
     * Flush the store
     */
    _flushStore() {
        this._store = new Map();
    }

    /**
     * Converts a 'native' arrangement to a fullcalendar event
     * @param {*} arrangement 
     * @returns 
     */
    _mapArrangementToFullCalendarEvent(arrangement) {
        const slugClass = writeSlugClass(arrangement.slug);
        const pkClass = "pk:" + arrangement.event_pk;

        return new FullCalendarEvent({
            title: arrangement.name,
            start: arrangement.starts,
            resourceIds: (arrangement.slug_list || []).concat([ arrangement.location_slug ]),
            end: arrangement.ends,
            color: this.colorProvider.getColor(arrangement),
            classNames: [ slugClass, pkClass ],
            extendedProps: {
                location_name: arrangement.location,
                location_slug: arrangement.location_slug,
                icon: arrangement.audience_icon, 
                starts: arrangement.starts, 
                ends: arrangement.ends,
                arrangementType: arrangement.arrangement_type,
                isSerie: !!arrangement.evserie_id,
                isRigging: arrangement.is_rigging,
            },
        });
    }

    /**
     * Get arrangement by the given slug
     * @param {*} slug 
     */
    get({pk, get_as } = {}) {
        if (this._store.has(parseInt(pk)) === false) {
            console.error(`Can not get arrangement with pk '${pk}' as pk is not known.`)
            return;
        }

        const arrangement = this._store.get(parseInt(pk));
        
        if (get_as === _FC_EVENT) {
            return this._mapArrangementToFullCalendarEvent(arrangement);
        }
        else if (get_as === _NATIVE_ARRANGEMENT) {
            return arrangement;
        }
    }

    /**
     * Get all arrangements in the form designated by get_as param.
     * @param {*} param0 
     * @returns An array of arrangements, whose form depends on get_as param.
     */
    get_all({ get_as, locations=undefined, arrangement_types=undefined, statuses=undefined, audience_types=undefined, filterSet=undefined } = {}) {
        let arrangements = this._getStoreAsArray();
        let filteredArrangements = [];

        let filterMap = new Map(filterSet.map( (slug) => [ slug.id, true ]));

        const mapTypeFilter = (types) => types !== undefined && types.length > 0 ? new Map(types.map(i => [i, true])) : undefined;

        let arrangementTypesMap =   mapTypeFilter(arrangement_types);
        let audienceTypesMap =      mapTypeFilter(audience_types);
        let statusTypesMap =        mapTypeFilter(statuses);
        let locationsMap =          mapTypeFilter(locations);
        
        debugger;

        arrangements.forEach ( (arrangement) => {
            let isWithinFilter =
                (arrangementTypesMap === undefined  || arrangementTypesMap.has(arrangement.arrangement_type_slug) === true) &&
                (audienceTypesMap === undefined     || audienceTypesMap.has(arrangement.audience_slug) === true) &&
                (statusTypesMap === undefined || statusTypesMap.has(arrangement.status_slug) === true) &&
                (locationsMap === undefined || locationsMap.has(arrangement.location_slug) === true);

            if (filterSet.showOnlyEventsWithNoRooms === true && arrangement.room_names.length > 0 && arrangement.room_names[0] !== null) {
                isWithinFilter = false;
            }

            if (filterMap.size > 0) {
                let match = false;
                for (let y = 0; y < arrangement.slug_list.length; y++) {
                    const slug = arrangement.slug_list[y];
                    if (filterMap.has(slug)) {
                        match = true;
                        break;
                    }
                }

                isWithinFilter = match;
            }

            if (isWithinFilter === true) {
                filteredArrangements.push(arrangement);
            }
        });
        
        arrangements = filteredArrangements;

        debugger;

        if (get_as === _FC_EVENT) {
            let mappedEvents = [];
            arrangements.forEach( (arrangement) => {
                mappedEvents.push( this._mapArrangementToFullCalendarEvent(arrangement) );
            });

            console.log("get_all -> ", mappedEvents);

            return mappedEvents;
        }
        else if (get_as === _NATIVE_ARRANGEMENT) {
            return arrangements;
        }
    }

    /**
     * Remove arrangement from the local store. Does not affect upstream.
     * @param {*} slug 
     */
    remove(slug) {
        if (this._store.has(slug)) {
            this._store.remove(slug);
        }
        else {
            console.error(`Can not remove arrangement with slug '${slug}', as slug is not known.`)
        }
    }
}


export class CalendarFilter {
    constructor (onFilterUpdated) {
        this.onFilterUpdated = onFilterUpdated;

        this.locations = [];
        this.rooms = [];
        this.audiences = [];
        this.arrangementTypes = [];
        
        this.showOnlyEventsWithNoRooms = false;
    }

    filterLocations (locationSlugs, runOnFilterUpdate=true) {
        this.locations = locationSlugs;
        if (runOnFilterUpdate)
            this.onFilterUpdated(this);

        console.log("Filtering locations", locationSlugs)
    }

    filterRooms (roomSlugs, runOnFilterUpdate=true) {
        this.rooms = roomSlugs;
        if (runOnFilterUpdate)
            this.onFilterUpdated(this);
    }

    filterStatusTypes(statusSlugs, runOnFilterUpdate=true) {
        this.statuses = statusSlugs;
        if (runOnFilterUpdate)
            this.onFilterUpdated(this);
    }

    filterAudiences (audienceSlugs, runOnFilterUpdate=true) {
        this.audiences = audienceSlugs;
        if (runOnFilterUpdate)
            this.onFilterUpdated(this);
    }

    filterArrangementTypes (arrangementTypeSlugs, runOnFilterUpdate=true) {
        this.arrangementTypes = arrangementTypeSlugs;
        if (runOnFilterUpdate)
            this.onFilterUpdated(this);
    }
}

export class FullCalendarBased {
    constructor(navigationHeaderWrapperElement = undefined) {
        this._instanceUUID = self.crypto.randomUUID();
        this.navigationHeaderWrapperElement = navigationHeaderWrapperElement;

        this.dateCursor = new Date();

        this._listenToRefreshEvents();
        this._listenToViewNavigationEvents();
    }

    renderNavigationButtons() {
        let navigationBundle = this._getNavigationButtons();
        this._navigationButtonElements = navigationBundle.wrapper;
        this._viewsToNavigationButtonsMap = navigationBundle.viewsToButtonMap;
        
        this.navigationHeaderWrapperElement.html("");
        this.navigationHeaderWrapperElement.append(this._navigationButtonElements);
        
        document.dispatchEvent(new CustomEvent(this._instanceUUID + '_callForFullCalendarViewRender', {
            "detail": { "view": this.getFcCalendar().view.type }
        }))
    }

    _getNavigationButtons() {
        const _this = this;

        let buttons = Array.from(this.viewButtons.values());

        const navCompare = (a, b) => {
            if (a.weight < b.weight) {
                return -1;
            }
            if (a.weight > b.weight) {
                return 1;
            }

            return 0;
        }

        buttons.sort( navCompare );

        const renderButtons = (button, buttons, subnesting = false) => {
            let resultingElement = null;

            if (button.isParent) {
                let dropdownWrapperElement = $("<div class='btn-group shadow-0'></div>");
                let mainButton = $("<a class='btn btn-lg wb-btn-white wb-large-btn shadow-0 border' role='button' id='" + _this._instanceUUID + "_" + button.view  + "'>" + button.title + "</a>");
                let dropdownButton = $("<button class='btn btn-lg wb-btn-white wb-large-btn shadow-0 border dropdown-toggle dropdown-toggle-split' data-mdb-toggle='dropdown'></button>")
                let dropdownMenu = $("<ul class='dropdown-menu'></ul>")

                let children = buttons.filter( (a) => a.parent === button.key );
                children.forEach(function (childButton) {
                    dropdownMenu.append(renderButtons(childButton, buttons, true));
                });

                if (mainButton.onclick === undefined) {
                    mainButton.on('click', function (event) {
                        document.dispatchEvent(
                            new CustomEvent(_this._instanceUUID + "_callForFullCalendarViewRender", { "detail": { "view": button.view } })
                        );

                        if (button.afterClick) {
                            button.afterClick();
                        }
                    });
                }
                else {
                    resultingElement.onclick = mainButton.onclick;
                }

                dropdownWrapperElement.append(mainButton, dropdownButton, dropdownMenu);

                return dropdownWrapperElement;
            }
            else if (button.parent !== undefined) {
                resultingElement = $("<li><a class='dropdown-item' id='"  + _this._instanceUUID + "_" + button.view +  "' href='#'>" + button.title + "</a></li>");
            }
            else {
                resultingElement = $("<button class='btn btn-lg wb-btn-white wb-large-btn' id='"  + _this._instanceUUID + "_" + button.view  + "'>" + button.title + "</button>");
            }

            if (button.onclick === undefined) {
                resultingElement.on("click", function (event) {
                    document.dispatchEvent(
                        new CustomEvent(_this._instanceUUID + "_callForFullCalendarViewRender", { "detail": { "view": button.view } })
                    );
                    
                    if (button.afterClick) {
                        button.afterClick();
                    }   
                });
            }
            else {
                resultingElement.onclick = button.onclick;
            }
            
            return resultingElement;
        }

        let wrapper = $("<div class='shadow-0 fc-custom-navigation-buttons'></div>")
        buttons.filter((x) => x.parent === undefined).forEach(function (button) {
            let result = renderButtons(button, buttons);
            wrapper.append(result);
        });

        return { "wrapper": wrapper, "viewsToButtonMap": undefined };
    }

    _listenToRefreshEvents() {
        document.addEventListener("plannerCalendar.refreshNeeded", async () => {
            await this.init();
            /* Remove all shown popovers, if we refresh the events without doing this we'll be "pulling the rug" up from under the popovers, 
            in so far as removing the elements they are anchored/bound to. In effect this puts the popover in a stuck state, in which it can't be hidden or
            removed without refresh. Hence we do this. */
            $(".popover").popover('hide');
        });
    }

    _listenToViewNavigationEvents() {
        document.addEventListener(this._instanceUUID + '_callForFullCalendarViewRender', function(event) {
            for (let i = 0; i < this._navigationButtonElements.children().length > 0; i++) {
                let childEl = this._navigationButtonElements.children()[i];

                if (childEl.tagName === "BUTTON") {
                    childEl.classList.remove("active");
                }
                else {
                    $(childEl).children("a.btn")[0].classList.remove("active");
                }
            }

            let parentTriggerElement = document.getElementById(this._instanceUUID + "_" + event.detail.view)

            let buttonElement = undefined;
            if (parentTriggerElement.tagName === "A") {
                buttonElement = $(parentTriggerElement).closest("div.btn-group").children("a.btn")[0]
            }
            else {
                buttonElement = parentTriggerElement;
            }

            if (buttonElement.classList.contains("active") === false) {
                buttonElement.classList.add("active");
            }

            if (this.getFcCalendar().view.type !== event.detail.view) {
                this.getFcCalendar().changeView(event.detail.view);
            }
        }.bind(this));
    }

    /**
     * Get the view that the calendar is currently in
     */
    _getView() {
        return this.getFcCalendar();
    }

    _findSlugFromEl(el) { 
        let slug = null;

        el.classList.forEach((classToEvaluate) => {
            let classSplit = classToEvaluate.split(":");
        
            if (classSplit.length > 1 && classSplit[0] == "slug") {
                slug = classSplit[1];
            }
        });

        if (slug === null) {
            console.error("Element does not have a valid slug.", el)
            return undefined;
        }

        return slug;
    }

    _findEventPkFromEl(el) {
        let pk = undefined;

        el.classList.forEach((classToEvaluate) => {
            let classSplit = classToEvaluate.split(":");
            if (classSplit.length > 1 && classSplit[0] == "pk") {
                pk = classSplit[1];
            }
        });

        if (pk === undefined) {
            console.error("Element does not have a valid pk.", el)
            return undefined;
        }

        return pk;
    }

    refresh() { 
        this.init();
    }

    /**
     * Get the FullCalendar calendar instance
     */
    getFcCalendar() { }
    teardown() { }
    async init() { }

}

export function writeSlugClass(slug) {
    return `slug:${slug}`;
}

/**
 * Append a given array to the given formData instance
 * @param {*Array} arrayToAppend 
 * @param {*FormData} formDataToAppendTo 
 * @param {*String} key
 */
export function appendArrayToFormData(arrayToAppend, formDataToAppendTo, key) {
    if (Array.isArray(arrayToAppend) !== true) {
        throw "Value of parameter arrayToAppend is not an array", arrayToAppend;
    }

    if (arrayToAppend.length > 0) {
        arrayToAppend.forEach((item) => {
            if (item) {
                formDataToAppendTo.append(key, item);
            }
        });
    }
}

export function convertObjToFormData(obj, convertArraysToList=false) {
    let formData = new FormData();

    for (let key in obj) {
        if (convertArraysToList === true && Array.isArray(obj[key])) {
            appendArrayToFormData(obj[key], formData, key)
            continue;
        }

        if (obj[key] instanceof Date) {
            formData.append(key, obj[key].toISOString());
            continue;
        }

        formData.append(key, obj[key]);
    }
    
    return formData;
}

/**
 * Get the clients timezone
 * @returns string with the clients timezone
 */
export function getClientTimezone() {
    return Intl.DateTimeFormat().resolvedOptions().timeZone;
}