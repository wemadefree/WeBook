export const _FC_EVENT = Symbol('EVENT');
export const _FC_RESOURCE = Symbol("RESOURCE");
export const _NATIVE_ARRANGEMENT = Symbol("NATIVE_ARRANGEMENT");
export const _NATIVE_LOCATION = Symbol("NATIVE_LOCATION");
export const _NATIVE_PERSON = Symbol("NATIVE_PERSON");

export class FullCalendarEvent {
    constructor ({title,
                 start,
                 end,
                 color="",
                 classNames=[],
                 extendedProps={}} = {}) 
    {
        this.title = title;
        this.start = start;
        this.end = end;
        this.color = color;
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
    
    getAll({ get_as } = {}) {
        var resources = _getStoreAsArray();

        if (get_as === _FC_RESOURCE) {
            let fcResources = [];
            for (let i = 0; i < resources.length; i++) {
                fcResources.push(this._mapToFullCalendarResource(resources[i]));
            }
            return fcResources;
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
        var resources = _getStoreAsArray();
        
        if (get_as === _FC_RESOURCE) {
            let fcResources = [];
            for (let i = 0; i < resources.length; i++) {
                fcResources.push(this._mapToFullCalendarResource(resources[i]));
            }
            return fcResources;
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
    constructor (plannerCalendar) {
        super();

        this._store = new Map(); 
        this._refreshStore();
        this.plannerCalendar = plannerCalendar;
    }

    /**
     * Refreshes the store and returns this so you can chain in a get.
     */
    _refreshStore(start, end) {
        this._flushStore();
        return fetch(`/arrangement/planner/arrangements_in_period?start=${start}&end=${end}`)
            .then(response => response.json())
            .then(obj => { obj.forEach((arrangement) => {
                this._store.set(arrangement.slug, arrangement);
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
        let _this = this;
        let slugClass = writeSlugClass(arrangement.slug);
        return new FullCalendarEvent({
            title: arrangement.name,
            start: arrangement.starts,
            end: arrangement.ends,
            color: _this.plannerCalendar._getColorProvider().getColor(arrangement),
            classNames: [ slugClass ],
            extendedProps: {
                location_name: arrangement.location,
                location_slug: arrangement.location_slug,
                icon: arrangement.audience_icon, 
                starts: arrangement.starts, 
                ends: arrangement.ends,
                arrangementType: arrangement.arrangement_type,
            },
        });
    }

    /**
     * Get arrangement by the given slug
     * @param {*} slug 
     */
    get({ slug, get_as } = {}) {
        if (this._store.has(slug) === false) {
            console.error(`Can not get arrangement with slug '${slug}' as slug is not known.`)
            return;
        }

        var arrangement = this._store.get(slug);
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
    get_all({ get_as, locations=undefined, arrangement_types=undefined, audience_types=undefined } = {}) {
        var arrangements = this._getStoreAsArray();
        var filteredArrangements = [];

        var locationsMap =          locations !== undefined && locations.length > 0 ? new Map(locations.map(i => [i, true])) : undefined;
        var arrangementTypesMap =   arrangement_types !== undefined && arrangement_types.length > 0 ? new Map(arrangement_types.map(i => [i, true])) : undefined;
        var audienceTypesMap =      audience_types !== undefined && audience_types.length > 0 ? new Map(audience_types.map(i => [i, true])) : undefined;

        arrangements.forEach ( (arrangement) => {
            var isWithinFilter =
                (locationsMap === undefined         || locationsMap.has(arrangement.location_slug) === true) &&
                (arrangementTypesMap === undefined  || arrangementTypesMap.has(arrangement.arrangement_type_slug) === true) &&
                (audienceTypesMap === undefined     || audienceTypesMap.has(arrangement.audience_slug) === true);
            if (isWithinFilter === true) {
                filteredArrangements.push(arrangement);
            }
        });
        
        arrangements = filteredArrangements;

        if (get_as === _FC_EVENT) {
            var mappedEvents = [];
            arrangements.forEach( (arrangement) => {
                mappedEvents.push( this._mapArrangementToFullCalendarEvent(arrangement) );
            });

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

        }
        else {
            console.error(`Can not remove arrangement with slug '${slug}', as slug is not known.`)
        }
    }
}

export class FullCalendarBased {

    _findSlugFromEl(el) { 
        var slug = undefined;

        el.classList.forEach((classToEvaluate) => {
            var classSplit = classToEvaluate.split(":");
        
            if (classSplit.length > 1 && classSplit[0] == "slug") {
                slug = classSplit[1];
            }
        });

        if (slug === undefined) {
            console.error("Element does not have a valid slug.")
            console.error(el);
            return undefined;
        }

        return slug;
    }

    refresh() { 
        this.init();
    }

    teardown() { }
    init() { }

}

export function writeSlugClass(slug) {
    return `slug:${slug}`;
}
