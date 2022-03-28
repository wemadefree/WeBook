class DateExtensions {
    /* Overwrite the time values for one Date instance with the value of a time field (as a str) */
    static OverwriteDateTimeWithTimeInputValue(date_to_write_time_to, time_input_val_as_str) {

        let times = time_input_val_as_str.split(':');
        let date = new Date(date_to_write_time_to);

        date.setHours(times[0]);
        date.setMinutes(times[1]);

        return date;
    }
}

function getUuidFromEventDomNode(eventDomNode) {
    let eventId = undefined;

    for (let y = 0; y < eventDomNode.classList.length; y++) {
        let css_class = eventDomNode.classList[y];
        if (css_class === undefined || css_class.split("_").length !== 2)
        {
            continue;
        }

        let split = css_class.split("_");

        if (split[0] === "uuid") {
            eventId = split[1];
            break;
        }
    }

    return eventId;
}

function parseEvent(eventObjToParse) {
    return {
        pk: eventObjToParse.pk,
        title: eventObjToParse.fields.title,
        from: new Date(eventObjToParse.fields.start),
        to: new Date(eventObjToParse.fields.end),
        color: (eventObjToParse.fields.color !== undefined &&  eventObjToParse.fields.color !== null && eventObjToParse.fields.color !== "" ? eventObjToParse.fields.color : "blue"),
        people: eventObjToParse.fields.people,
        rooms: eventObjToParse.fields.rooms,
        loose_requisitions: eventObjToParse.fields.loose_requisitions,
        sequence_guid: eventObjToParse.fields.sequence_guid,
        extra_classes: eventObjToParse.extra_classes !== undefined ? eventObjToParse.extra_classes : []
    }
}

Date.prototype.addDays = function(days) {
    var date = new Date(this.valueOf());
    date.setDate(date.getDate() + days);
    return date;
}


class LoadingHintComponent {
    constructor() {

    }
}

class EventsLoadingHintComponent {

}

/*
    Top level.
*/
class Planner {
    constructor({ 
        onClickEditButton, 
        onClickInfoButton, 
        onClickOrderServiceButton, 
        onSelectionCopied, 
        csrf_token,
        csrf_token2, // TODO: remove this
        arrangement_id, 
        $serviceRequisitionsWrapperEl=undefined,
        $peopleRequisitionsWrapperEl=undefined,
        $peopleToRequisitionWrapperEl=undefined,
        texts = undefined } = {}) {

        this.local_context = new LocalPlannerContext(this);
        this._isLoading = false;
        
        this.renderer_manager = new RendererManager({
            context: this.local_context,
            renderers: undefined,
            onClickEditButton: onClickEditButton,
            onClickInfoButton: onClickInfoButton,
            onClickOrderServiceButton: onClickOrderServiceButton,
            planner:this,
        });

        this.loaderHint = new LoadingHint(document.getElementById('loaderHint'))
        
        this.arrangement_id = arrangement_id;
        this.csrf_token = csrf_token;
        this.csrf_token2 = csrf_token2;

        if ($serviceRequisitionsWrapperEl !== undefined) {
            this.loose_requisitions_component = new LooseRequisitionsComponentManager(
                $serviceRequisitionsWrapperEl,
                this
            );
        }
        if ($peopleRequisitionsWrapperEl !== undefined) {
            this.people_requisitions_component = new PeopleRequisitionsComponentManager(
                $peopleRequisitionsWrapperEl,
                this
            );
        }
        if ($peopleToRequisitionWrapperEl !== undefined) {
            this.people_to_requisition_component = new PeopleToRequisitionComponentManager(
                $peopleToRequisitionWrapperEl,
                this
            );
        }


        this.collision_analyzer = new CollisionAnalyzer(this);
        
        this.clipboard = new EventClipboard(onSelectionCopied);
        
        this.textLib = new Map([
            ["create", "Create"],
            ["delete", "Delete"],
            ["edit", "Edit"],
            ["info", "Info"]
        ]);

        if (texts !== undefined) {
            this.textLib = new Map([...this.textLib, ...texts ]);
        }

        this.synchronizer = new ContextSynchronicityManager(csrf_token, arrangement_id, this)
        this.synchronizer.getEventsOnSource();
        

        this.local_context.onSeriesChanged = function ({ planner, eventsAffected, changeType } = {}) {
            console.log("=> Serie added")
        }

        this.local_context.onEventCreated = function ({ createdEvent, planner} = {}) {
            console.log("=> Event created")

            if (createdEvent.is_shadow !== true) {
                planner.synchronizer.pushEvent(createdEvent);
            }

            planner.init();
        }

        this.local_context.onEventsCreated = function ({eventsCreated, planner} = {}) {
            console.log("=> Events created")
            planner.synchronizer.pushEvents(eventsCreated);
            planner.init();
        }

        this.local_context.onEventUpdated = function ({ eventAfterUpdate, planner } = {}) {
            console.log("==> Event updated")
            planner.synchronizer.pushEvent(eventAfterUpdate);
            planner.init();
        }
        
        this.local_context.onEventsUpdated = function ({ eventsAfterUpdate, planner} = {}) {
            console.log("==> Events updated")
            planner.synchronizer.pushEvents(eventsAfterUpdate);
            planner.init();
        }

        this.local_context.onEventsDeleted = function ({ deletedEvents, planner } = {}) {
            console.log("=> Events deleted")
            planner.synchronizer.deleteEvents(deletedEvents);
            planner.init();
        }

        this.local_context.onEventDeleted = function ({ deletedEvent, planner } = {}) {
            console.log("=> Event deleted")
            console.log(deletedEvent);
            planner.synchronizer.deleteEvent(deletedEvent);
            planner.init();
        }
    }

    /**
     * Activates the loading hin
     */
    _isLoading() {
        this._isLoading = true;


    }

    /**
     * Removes the loading hint
     */
    _isDoneLoading() {

    }

    init() {
        this.renderer_manager.render(Array.from(this.local_context.events.values()));
    }
}

class LooseRequisitionsComponentManager {
    constructor($tbodyElement, planner) {
        this._planner = planner;
        this._$element = $tbodyElement;
        this._load();
    }

    _bind() {
        $('.requisitionServiceBtn').on("click", function () {
            var pk =  $(this).attr("value");
            location.href="/arrangement/requisition/" + pk + "/order?lreq_id=" + pk
        });
    }

    _load() {
        let _this = this;
        this._$element.load('/arrangement/planner/loose_service_requisitions_table?arrangement_id=' + this._planner.arrangement_id, function () {
           _this._bind(); 
        });
    }

    refresh() {
        this._load();
    }
}

class PeopleRequisitionsComponentManager {
    constructor ($element, planner) {
        this._planner = planner;
        this._$element = $element;
        this._load();
    }

    _load() {
        this._$element.load('/arrangement/planner/people_requisitions_table?arrangement_id=' + this._planner.arrangement_id)
    }

    refresh() {
        this._load();
    }
}

class PeopleToRequisitionComponentManager {
    constructor ($element, planner) {
        this._planner = planner;
        this._$element = $element;
        this._load();
    }

    _bind() {
        let _this = this;
        $('.initiatePersonRequisitionBtn').on("click", function () {
            var pk =  $(this).attr("value");
            var formData = new FormData();
            formData.append("person_id", pk)
            formData.append("arrangement_id", _this._planner.arrangement_id);

            fetch("/arrangement/requisition/requisition_person", {
                method: 'POST',
                body: formData,
                headers: {
                    "X-CSRFToken": _this._planner.csrf_token2
                }
            }).then(_this.refresh());
        });
    }

    _load() {
        let _this = this;
        this._$element.load("/arrangement/planner/people_to_requisition_table?arrangement_id=" + this._planner.arrangement_id, function () {
            _this._bind()
        });
    }

    refresh() {
        this._load();
    }
}

class CollisionAnalyzer {
    constructor (planner) {
        this._planner = planner;

        this.$collisionAnalysisWrapper = $('#collisionAnalysisWrapper');
        this.$collisionAnalysisLoader = $('#collisionAnalysisLoader');
        this.$collisionAnalysisBody = $('#collisionAnalysisBody');
    }

    requestCollisionAnalysis () {

        this.showLoader();

        fetch ( "/arrangement/planner/get_collision_analysis?arrangement=" + this._planner.arrangement_id )
            .then(response => response.json())
            .then(respJson => JSON.parse(respJson))
            .then(obj => {
                for (let i = 0; i < obj.length; i++) {
                    var parsedEvent = parseEvent(obj[i]);
                    parsedEvent.color = "#f5f5f5";
                    parsedEvent.borderColor = "red";
                    parsedEvent.is_shadow = true;
                    parsedEvent.textColor="black";
                    parsedEvent.editable = false;
                    parsedEvent.extra_classes.push("collision_analysis_shadow_event")
                    this._planner.local_context.add_event(parsedEvent);
                }
                return obj.length;
            }).then(a => this.renderBody(a))
            .then(obj => {
                calendarManager.ds.removeSelectables(document.querySelectorAll(".collision_analysis_shadow_event"))
            })
    }

    reset () {
        this.$collisionAnalysisWrapper.hide();
        this.$collisionAnalysisLoader.hide();
        
        this.$collisionAnalysisBody.html("");
        this.$collisionAnalysisBody.hide();

        this._planner.local_context.remove_shadowed_events();
    }

    showLoader() {
        this.$collisionAnalysisWrapper.show();
        this.$collisionAnalysisLoader.show();
        this.$collisionAnalysisBody.hide();
    }

    bindCleanupBtn() {
        let _this = this;
        $('#cleanupAnalysisBtn').on('click', function () {
            _this.reset();
        })
    }

    renderBody (resultCount) {
        this.$collisionAnalysisWrapper.show();
        this.$collisionAnalysisLoader.hide();
        
        this.$collisionAnalysisBody
            .append( $('<em> <span class="text-danger fw-bold">' + resultCount + '</span> kollisjoner funnet. Disse har blitt speilet inn i kalenderen.</em>') )
            .append( $('<button class="btn btn-block btn-outline-dark" id="cleanupAnalysisBtn">Fjern analyse og speilinger</button>') );
        this.bindCleanupBtn();
        this.$collisionAnalysisBody.show();
    }
}

class EventClipboard {
    constructor (onClipboardUpdated) {
        this.events = []
        this.deltasMap = new Map();
        this.mode = undefined;
        this.onClipboardUpdated = onClipboardUpdated;

        this.modeHtmlClassMap = new Map([
            ["cut", "cut-highlight-daygrid-event"],
            ["copy", ""],
        ])
    }

    setClipboard (events, startTime, operationType) {
        this.clearClipboard();
        
        let baseStartTime = new Date(startTime.getTime())
        baseStartTime.setHours(1)
        baseStartTime.setMinutes(0);
        baseStartTime.setSeconds(0);

        for (let i = 0; i < events.length; i++) {
            let delta = events[i].from.getTime() - baseStartTime.getTime();
            this.deltasMap.set(events[i].id, delta)
            $(events[i].el).addClass(this.modeHtmlClassMap.get(operationType));
        }

        this.mode = operationType;
        this.events = events;

        this.onClipboardUpdated(this);
    }

    computePaste(baseTimeForPaste) {
        let computedEvents = [];

        for (let i = 0; i < this.events.length; i++) {
            let newEventAsPasted = Object.assign({}, this.events[i]);
            let delta = this.deltasMap.get(newEventAsPasted.id) * 1;
            let diffDelta = newEventAsPasted.to - newEventAsPasted.from;

            let newStart = new Date(baseTimeForPaste.getTime() + delta );
            let newEnd = new Date(newStart.getTime() + diffDelta);

            newEventAsPasted.from = newStart;
            newEventAsPasted.to = newEnd;
            newEventAsPasted.id = crypto.randomUUID();

            computedEvents.push(newEventAsPasted);
        }

        return computedEvents;
    }

    clearClipboard() {
        for (let i = 0; i < this.events.length; i++) {
            $(this.events[i].el).removeClass(this.modeHtmlClassMap.get(this.mode));
        }

        this.events = [];
        this.deltasMap.clear();
    }
}

/* handle synchronizing data between multiple contexts */
class ContextSynchronicityManager {
    constructor (csrf_token, arrangement_id, planner) {
        this.uuid_to_id_map = new Map();

        let wrap = document.createElement("span");
        wrap.innerHTML = csrf_token
        this.csrf_token = wrap.children[0].value;
        this.planner = planner;
        this.arrangement_id = arrangement_id;
    }

    /* Retrieve all events from upstream, and push into planner */
    getEventsOnSource () {
        let planner = this.planner;
        let id_map = this.uuid_to_id_map;
        planner.loaderHint.startHinting({
            hintMessage: "Loading events...",
            hintType: "success"
        });
        fetch('/arrangement/planner/get_events?arrangement_id=' + this.arrangement_id)
            .then(response => response.json() )
            .then(data => {
                let events = JSON.parse(data);
                events.forEach(function (ev) {
                    let converted_event = {
                        pk: ev.pk,
                        title: ev.fields.title,
                        from: new Date(ev.fields.start),
                        to: new Date(ev.fields.end),
                        color: (ev.fields.color !== undefined &&  ev.fields.color !== null && ev.fields.color !== "" ? ev.fields.color : "blue"),
                        people: ev.fields.people,
                        rooms: ev.fields.rooms,
                        loose_requisitions: ev.fields.loose_requisitions,
                        sequence_guid: ev.fields.sequence_guid,
                    };
                    let uuid = planner.local_context.add_event(converted_event, false);
                    id_map.set(uuid, ev.pk);
                });
            })
            .then(a => { planner.init(); planner.loaderHint.finishHinting(); })
    }

    /** Convert a given event to a legally upsertable object */
    _convertEvent(id, event, arrangement_id) {
        let convertedEvent = {
            id: (id === undefined ? 0 : id),
            title: event.title,
            start: event.from.toISOString(),
            end: event.to.toISOString(),
            color: event.color,
            arrangement: arrangement_id,
            people: (event.people === undefined ? [] : event.people),
            rooms: (event.rooms === undefined ? [] : event.rooms),
            loose_requisitions: (event.loose_requisitions === undefined ? [] : event.loose_requisitions)
        }

        if (event.serie_uuid !== undefined) {
            convertedEvent.sequence_guid = event.serie_uuid;
        }

        return convertedEvent;
    }

    pushEvents (events) {
        let formData = new FormData();

        for (let i = 0; i < events.length; i++) {
            let id = this.uuid_to_id_map.get(event.id);
            let convertedEvent  = this._convertEvent(id, events[i], this.arrangement_id)
            for (var key in convertedEvent) {
                formData.append("events[" + i + "]." + key, convertedEvent[key]);
            }
        }

        planner.local_context.events.clear();
        fetch("/arrangement/planner/create_events/", {
            method:"POST",
            body: formData,
            headers: {
                "X-CSRFToken": this.csrf_token
            },
            credentials: 'same-origin',
        }).then(a => { this.getEventsOnSource() });
    }

    pushEvent (event) {
        let id = this.uuid_to_id_map.get(event.id);

        let _this = this;
        let createFormData = function (event, arrangement_id) {
            let data = new FormData();

            let ev = _this._convertEvent(id,  event, arrangement_id)
            for (let key in ev) {
                data.append(key, ev[key]);
            }

            return data;
        }

        if (id !== undefined) {
            fetch('/arrangement/planner/update_event/' + id, {
                method: 'POST',
                body: createFormData(event, this.arrangement_id, this.csrf_token),
                headers: {
                    "X-CSRFToken": this.csrf_token
                },
                credentials: 'same-origin',
            });
        }
        else {
            fetch('/arrangement/planner/create_event', {
                method: 'POST',
                body: createFormData(event, this.arrangement_id, this.csrf_token),
                headers: {
                    "X-CSRFToken": this.csrf_token
                },
                credentials: 'same-origin',
            }).then(response => response.json())
              .then(data => {
                  this.uuid_to_id_map.set(event.id, data.id);
              });

        }
    }

    deleteEvent (event) {
        let id = this.uuid_to_id_map.get(event.id);

        if (id === undefined) {
            throw "Event does not exist upstream, or we do not know about it.";
        }
        
        let data = new FormData();
        data.append('csrfmiddlewaretoken', this.csrf_token);

        fetch("/arrangement/planner/delete_event/" + id, {
            method: 'DELETE',
            headers: {
                'X-CSRFToken': this.csrf_token
            },
            credentials: "same-origin"
        });
    }

    deleteEvents(events) {
        let data = new FormData();
        let eventIds = events.map((event) => this.uuid_to_id_map.get(event.id));
        let planner = this.planner;

        data.append("eventIds", eventIds);
        data.append("csrfmiddlewaretoken", this.csrf_token);

        planner.loaderHint.startHinting({ 
            hintMessage: "Deleting events...",
            hintType: 'danger',
        })

        fetch("/arrangement/planner/delete_events/", {
            method: 'POST',
            headers: {
                'X-CSRFToken': this.csrf_token
            },
            credentials: 'same-origin',
            body: data
        }).then(response => { planner.loaderHint.finishHinting(); });
    }
}


class StrategyExecutorAbstraction {
    constructor ({function_to_run, parameter_obj}={}) {
        this.function_to_run = function_to_run
        
        this.parameters = {}
        if (parameter_obj !== undefined) {
            this.add_object_keyvals_as_params(parameter_obj);
        }
    }

    add_object_keyvals_as_params(obj) {
        for (let [key, value] of Object.entries(obj)) {
            this.parameters[key] = value;
        }
    }

    run(extra_params=undefined) {
        if (extra_params !== undefined) {
            this.add_object_keyvals_as_params(extra_params);
        }

        return this.function_to_run(this.parameters);
    }
}

/**
 * Local planner context interface. Serves as the data interface, and publishes events
 */
class LocalPlannerContext {
    constructor(planner_backref) {
        this.series = new Map();
        this.events = new Map();

        this.planner = planner_backref

        this.onEventsChanged = function (events) { };
        this.onSeriesChanged = function (events) { };
    }

    remove_shadowed_events() {
        var _events = this.events;
        
        this.events.forEach(function (value, key, map) {
            if (value.is_shadow === true) {
                _events.delete(key);
            }
        })

        this.planner.init();
    }

    add_serie(serie) {
        let serie_uuid = crypto.randomUUID();
        serie.id = serie_uuid;
        this.series.set(serie_uuid, serie);
        let generatedEvents = this.SeriesUtil.calculate_serie(serie);
        this.add_events(generatedEvents, serie_uuid);
        this.onSeriesChanged({planner: this.planner, eventsAffected: this.generatedEvents, changeType: "create" });
    }

    /**
     * Add a new event.
     * @param {object} event - The event to add
     * @param {bool} triggerEvent -
     * @returns 
     */
    add_event(event, triggerEvent=true) {
        let uuid = crypto.randomUUID();
        event.id = uuid;
        this.events.set(uuid, event);
        if (triggerEvent === true) {
            this.onEventCreated({ createdEvent: event, planner: this.planner });
        }
        return uuid;
    }

    /**
     * Update an existing event
     * @param {*} event - The event
     * @param {*} uuid  - The UUID of the event which to update. 
     */
    update_event(event, uuid) {
        this.events.set(uuid, event);
        event.id = uuid;
        this.onEventUpdated({ eventAfterUpdate: event, planner: this.planner });
    }

    update_events(events) {
        for (let i = 0; i < events.length; i++) {
            let ev = events[i];
            this.events.set(ev.id, ev);
        }
        this.onEventsUpdated({ eventsAfterUpdate: events, planner: this.planner });
        // this.onEventUpdated({ eventAfterUpdate: events[events.length-1], planner: this.planner });
    }

    /**
     * Add a list of events, with the option to "serie" them.
     * @param {Array} events - The events which to add
     * @param {*} serie_uuid - The serie_uuid which is to be attached to these events.
     */
    add_events(events, serie_uuid=undefined) {
        if (serie_uuid !== undefined) {
            events.forEach(function (event) {
                event.serie_uuid = serie_uuid;
            })
        }

        for (let i = 0; i < events.length; i++) {
            let event_uuid = crypto.randomUUID();
            let ev = events[i];
            ev.id = event_uuid;
            this.events.set(event_uuid, ev);
        }

        this.onEventsCreated({ eventsCreated: events, planner: this.planner });
    }

    /**
     * Delete a serie. Will remove the serie, and its events.
     * @param {string} serie_uuid  - The UUID of the serie which we are to delete.
     */
    delete_serie(serie_uuid) {
        for (let i = 0; i < this.events.values().length; i++) {
            let event = this.events.values()[i];
            if (event.serie_uuid === serie_uuid) {
                this.remove_event(i.id);
            }
        }

        this.series.delete(serie_uuid, 1);
        this.onSeriesChanged({ planner: this.planner, eventsAffected: this.events, changeType: "delete" });
        this.onEventsDeleted({ deletedEvents: this.events, planner: this.planner });
    }

    /**
     * Remove an event
     * @param {string} uuid - The UUID of the event which to remove
     */
    remove_event(uuid) {
        let delete_event = this.events.get(uuid);

        this.events.delete(uuid);
        this.onEventDeleted({ deletedEvent: delete_event, planner: this.planner });
    }

    remove_events(events) {
        for (let i = 0; i < events.length; i++) {
            this.events.delete(events[i].id);
        }

        this.onEventsDeleted({ deletedEvents: events, planner: this.planner });
    }

    /**
     * @inner
     */
    SeriesUtil = class SeriesUtil {

        static calculate_serie (serie) {
            const pattern_strategies = new Map();
            pattern_strategies.set(
                "daily__every_x_day", 
                new StrategyExecutorAbstraction({
                    function_to_run: this.daily__every_x_day,
                    parameter_obj: serie.pattern
                })
            );
            pattern_strategies.set(
                "daily__every_weekday",
                new StrategyExecutorAbstraction({
                    function_to_run: this.daily__every_weekday,
                    parameter_obj: {},
                })
            );
            pattern_strategies.set(
                "weekly__standard",
                new StrategyExecutorAbstraction({
                    function_to_run: this.weekly_standard,
                    parameter_obj: serie.pattern,
                })
            );
            pattern_strategies.set(
                "month__every_x_day_every_y_month",
                new StrategyExecutorAbstraction({
                    function_to_run: this.month__every_x_day_every_y_month,
                    parameter_obj: serie.pattern,
                })
            );
            pattern_strategies.set(
                "month__every_arbitrary_date_of_month", 
                new StrategyExecutorAbstraction({
                    function_to_run: this.month__every_arbitrary_date_of_month,
                    parameter_obj: serie.pattern,
                }));
            pattern_strategies.set(
                "yearly__every_x_of_month", 
                new StrategyExecutorAbstraction({
                    function_to_run: this.yearly__every_x_of_month,
                    parameter_obj: serie.pattern,
                })
            );
            pattern_strategies.set(
                "yearly__every_arbitrary_weekday_in_month",
                new StrategyExecutorAbstraction({
                    function_to_run: this.yearly__every_arbitrary_weekday_in_month,
                    parameter_obj: serie.pattern,
                })
            );

            const area_strategies = new Map();
            area_strategies.set(
                "StopWithin", 
                new StrategyExecutorAbstraction(
                    {
                        function_to_run: this.area__stop_within, 
                        parameter_obj: {
                            stop_within_date: DateExtensions.OverwriteDateTimeWithTimeInputValue(serie.time_area.stop_within, "23:59")
                        }
                    }
                )
            );
            area_strategies.set(
                "StopAfterXInstances", 
                new StrategyExecutorAbstraction(
                    {
                        function_to_run: this.area__stop_after_x_instances,
                        parameter_obj: serie.time_area,
                    }
                )    
            );
            area_strategies.set(
                "NoStopDate", 
                new StrategyExecutorAbstraction(
                    {
                        function_to_run: this.area__no_stop_date,
                        parameter_obj: serie.time_area,
                    }
                )
            );

            let area_strategy = area_strategies.get(serie.time_area.method_name);
            let scope = area_strategy.run({ start_date: serie.time_area.start_date });
            
            let pattern_strategy = pattern_strategies.get(serie.pattern.pattern_routine);

            let events = [];

            let date_cursor = scope.start_date;
            let instance_cursor = 0;
            let cycle_cursor = 0;

            let event_sample = {
                title: serie.time.title,
                start: serie.time.start,
                end: serie.time.end,
                color: serie.time.color,
            }
            while ((scope.stop_within_date !== undefined && date_cursor < scope.stop_within_date) || (scope.instance_limit !== 0 && scope.instance_limit >= instance_cursor)) {

                /* 
                    There are two ways we monitor our "progress" here. One is by the date cursor, and one is by instances.
                    In some cases we only want to do the repetition pattern until a set date, other times we wish do it X times. 
                    Hence we need to have this "cycle manager" to handle the repeating for us - and alleviate the strategies from 
                    having to concern themselves with this. This in turn means that a repetition pattern/strategy is run in cycles - as one may see in their
                    respective implementations, and this does to some degree dictate implementations.
                    This does put the onus of managing the end of the series/repetition on the cycle manager (which is what this is.)
                */
                event_sample = Object.assign({}, event_sample);
                let result = pattern_strategy.run({cycle: cycle_cursor, start_date: date_cursor, event: event_sample});

                if (result === undefined || (Array.isArray(result) && result.length == 0)) {
                    cycle_cursor++;
                    continue;
                }

                if (scope.stop_within_date !== undefined) {
                    if (result.from >= scope.stop_within_date) {
                        break;
                    }
                }
                if (scope.instance_limit !== undefined &&  scope.instance_limit !== undefined) {
                    if (instance_cursor > scope.instance_limit) {
                        break;
                    }
                }

                let move_cursor_to = date_cursor
                if (Array.isArray(result)) {
                    move_cursor_to = result[result.length - 1].to
                }
                else {
                    move_cursor_to = result.to
                }

                date_cursor = move_cursor_to
                date_cursor = date_cursor.addDays(1)

                if (scope.instance_limit !== 0) {
                    instance_cursor++;
                }

                if (Array.isArray(result)) {
                    events = events.concat(result);
                }
                else {
                    events.push(result);
                }

                cycle_cursor++;
            }

            return events;
        }

        static area__stop_within({start_date, stop_within_date} = {}) {
            return {
                start_date: new Date(start_date),
                stop_within_date: new Date(stop_within_date),
                instance_limit: 0,
            }
        }

        static area__stop_after_x_instances({start_date, instances} = {}) {
            return {
                start_date: new Date(start_date),
                stop_within_date: undefined,
                instance_limit: instances,
            }
        }

        static area__no_stop_date({start_date, projectionDistanceInMonths} = {}) {
            start_date = new Date(start_date)

            let stop_within_date = new Date(start_date)
            let month = start_date.getMonth();
            stop_within_date.setMonth(parseInt(month) + parseInt(projectionDistanceInMonths));
            return {
                start_date: start_date,
                stop_within_date: stop_within_date,
                instance_limit: 0
            }
        }

        static daily__every_x_day({cycle, start_date, event, interval}={}) {
            if (cycle != 0) {
                start_date = start_date.addDays(interval - 1); // -1 to account for the "move-forward" padding done in cycler
            }

            event.from = DateExtensions.OverwriteDateTimeWithTimeInputValue(start_date, event.start);
            event.to = DateExtensions.OverwriteDateTimeWithTimeInputValue(start_date, event.end);

            return event;
        }

        static daily__every_weekday({cycle, event, start_date}={}) {
            while ([0,6].includes(start_date.getDay())) {
                start_date = start_date.addDays(1);
            }

            event.from = DateExtensions.OverwriteDateTimeWithTimeInputValue(start_date, event.start);
            event.to = DateExtensions.OverwriteDateTimeWithTimeInputValue(start_date, event.end);

            return event;
        }

        static weekly_standard({cycle, start_date, event, week_interval, days}={}) {
            if (cycle != 0) {
                /* 
                We need to make sure that we always work with monday as base excepting when we are running the first cycle (0), as
                the user can specify a start_date in the middle of a week. The end, as is the standard in the other strategies, is 
                the responsibility of the cycle runner, so we don't care about that here.
                */
                if (start_date.getDay() !== 1) {
                    if (start_date.getDay != 0) {
                        start_date = start_date.addDays( (start_date.getDay() - 1) * -1)
                    }
                    else if (start_date.getDay == 0) {
                        start_date = start_date.addDays(1)
                    }
                }

                start_date = start_date.addDays(7 * week_interval)
            }

            let events = [];
            let y = 0;
            for (let i = start_date.getDay(); i < 6; i++) {
                let day = days.get(i)
                if (day === true) {
                    let adjusted_date = (new Date(start_date)).addDays(y);
                    let ev_copy = Object.assign({}, event);
                    ev_copy.from = DateExtensions.OverwriteDateTimeWithTimeInputValue(adjusted_date, event.start)
                    ev_copy.to = DateExtensions.OverwriteDateTimeWithTimeInputValue(adjusted_date, event.end);

                    events.push(ev_copy);
                }

                y++;
            }

            return events;
        }

        static month__every_x_day_every_y_month({cycle, start_date, day_of_month, event, interval}={}) {
            if (cycle !== 0)  {
                start_date.setMonth(start_date.getMonth() + parseInt(interval))
                start_date.setDate(1);
            }

            if (day_of_month > start_date.getDate()) {
                return;
            }

            let adjusted_date = (new Date(start_date)).setDate(day_of_month);
            event.from = DateExtensions.OverwriteDateTimeWithTimeInputValue(adjusted_date, event.start);
            event.to = DateExtensions.OverwriteDateTimeWithTimeInputValue(adjusted_date, event.end);

            return event;
        }

        static arbitrator_find(start_date, arbitrator, weekday) {
           // helps us parse from 1,2,3,4,5,6,7 to 0,1,2,3,4,5,6 that JS uses
           let weekDayParseReverseMap = new Map([
               [0, 7],
               [6, 6],
               [5, 5],
               [4, 4],
               [3, 3],
               [2, 2],
               [1, 1],
           ]);

           // Before we can do anything we need to find the first occurrence of weekday 
           // in the month

           let month = start_date.getMonth();

           let date = new Date(start_date);
           date.setDate(1);
           let first_weekday_of_month = date.getDay();
           if (weekDayParseReverseMap.get(first_weekday_of_month) > weekday) { // not present in first week, go to second
               date = date.addDays(7);
           }

           // go to the first instance of weekday
           let weekdaydiff = parseInt(weekDayParseReverseMap.get(date.getDay())) - parseInt(weekday);
           date = date.addDays(weekdaydiff * (weekdaydiff > 0 ? -1 : 1));

           // go to the desired position, as determined by the arbitrator (is that even the right word? :D)
           date = date.addDays(arbitrator * 7);
           if (arbitrator == 5) {
               if (date.getMonth() !== month) { // last instance of weekday is in week 4
                   date = date.addDays(4 * 7);
               }
           }

           return date;
        }

        static month__every_arbitrary_date_of_month({cycle, event, start_date, arbitrator, weekday, interval}={}) {
            if (cycle != 0) {
                start_date.setDate(1);
                let month = start_date.getMonth();
                start_date.setMonth(month + parseInt(interval));
            }

            let date = SeriesUtil.arbitrator_find(start_date, arbitrator, weekday);
            event.from = DateExtensions.OverwriteDateTimeWithTimeInputValue(date, event.start);
            event.to = DateExtensions.OverwriteDateTimeWithTimeInputValue(date, event.end)

            return event;
        }

        static yearly__every_x_of_month ({cycle, start_date, event, day_index, year_interval, month}={}) {
            if (cycle !== 0)  {
                start_date.setFullYear ( start_date.getFullYear() + parseInt(year_interval) )
            }

            let date = new Date(start_date.getFullYear() + "-" + month + "-" + day_index);
            event.from = DateExtensions.OverwriteDateTimeWithTimeInputValue(date, event.start);
            event.to = DateExtensions.OverwriteDateTimeWithTimeInputValue(date, event.end);

            return event;
        }
        
        static yearly__every_arbitrary_weekday_in_month ({cycle, start_date, event, arbitrator, weekday, year_interval, month}={}) {
            if (cycle != 0) {
                start_date.setFullYear ( start_date.getFullYear() + parseInt(year_interval) )
            }

            let date = new Date(start_date.getFullYear() + "-" + month + "-01");
            
            // use the "day-seek" algo to find the correct day, according to the arbitrator
            date = SeriesUtil.arbitrator_find(date, arbitrator, weekday);
            
            event.from = DateExtensions.OverwriteDateTimeWithTimeInputValue(date, event.start);
            event.to = DateExtensions.OverwriteDateTimeWithTimeInputValue(date, event.end);

            return event;
        }
    };
}

class RendererManager {
    constructor({context, 
                renderers = undefined, 
                onClickEditButton = undefined, 
                onClickInfoButton = undefined,
                onClickOrderServiceButton = undefined, 
                planner=undefined} = {}) {

        if (typeof (renderers) !== "array") {
            renderers = [];
        }

        this.renderers = renderers;
        this.planner = planner;

        this.onClickEditButton = onClickEditButton;
        this.onClickInfoButton = onClickInfoButton;
        this.onClickOrderServiceButton = onClickOrderServiceButton;

        this.onClickDeleteSeriesButton = function (series_uuid) {
            context.delete_serie(series_uuid);
        }

        this.onClickDeleteButton = function (eventId) {
            context.remove_event(eventId)
        }

        context.onEventsChanged = function (events) {
            if (this.renderers !== undefined) {
                this.renderers.forEach(element => {
                    element.render(events);
                });
            }
        }
        context.onSeriesChanged = function (events) {
            if (this.renderers !== undefined) {
                this.renderers.forEach(element => {
                    element.render(events);
                });
            }
        }
    }

    add_renderer(renderer) {
        renderer.onClickEditButton = this.onClickEditButton;
        renderer.onClickDeleteButton = this.onClickDeleteButton;
        renderer.onClickDeleteSeriesButton = this.onClickDeleteSeriesButton;
        renderer.onClickOrderServiceButton = this.onClickOrderServiceButton;
        renderer.planner = this.planner;

        this.renderers.push(renderer);
    }

    render(events) {
        this.renderers.forEach(element => {
            element.render(events);
        });
    }

}

class RendererBase {
    /**
     * @abstract
     */
    constructor() {
        if (this.constructor == RendererManager) {
            throw new Error("Abstract classes can't be instantiated");
        }
    }

    /**
        Force the renderer to render itself
        @abstract
    */
    render() {
        throw new Error("Method 'render()' must be implemented");
    }
}

/* 
    Provides utilities to wrap around and manage a FullCalendar calendar instance fluidly
*/

let focused_event_uuid = undefined;
let focused_serie_uuid = undefined;

/**
 * @classdesc Calendar renderer and manager to work with FullCalendar.
 */
class CalendarManager extends RendererBase {

    constructor(element_id, fc_options) {
        super(RendererBase);
        this.element_id = element_id;
        this.fc_options = fc_options;
        this.calendar = undefined;
        this.rememberedInitialView = "dayGridMonth";
        this._serie_is_marked = false;

        let self = this;
    
        this.setup_cell_select(fc_options.initialView)
        
        hotkeys('ctrl+c, ctrl+x, ctrl+v, del', function (event, handler) {
            event.preventDefault();
            self.handle_hotkey(handler.key);
        });

        this.dsEventSelector = ".fc-event, .fc-daygrid-event";
        this.ds = new DragSelect({
            area: document.getElementById(this.element_id)
        });
        this.setup_dragselect()

        this.fc_options.eventContent = (arg) => {
            let rootNode = this.RenderingUtilities.renderEventForView(arg.view.type, arg);
            return { 
                html: rootNode.outerHTML
            };
        }

        this.fc_options.eventResize = (eventResizeInfo) => {
            let event = {
                id: eventResizeInfo.event.extendedProps.event_uuid,
                title: eventResizeInfo.event.title,
                from: eventResizeInfo.event.start,
                to: eventResizeInfo.event.end,
                color: eventResizeInfo.event.backgroundColor,
            };

            this.planner.local_context.update_event(event, event.id);
        }

        this.fc_options.selectAllow = (info) => {
            let selected = document.querySelectorAll('.ds-selected');
            return false;
        }

        this.fc_options.eventDragStart = (info) => {
            if (document.querySelectorAll('.ds-selected').length === 1) {
                this.ds.stop();
                this.dsIsGood=false;
            }
        }

        this.fc_options.eventDragStop = (info) => {
            if (this.dsIsGood === false) {
                this.setup_dragselect();
            }
        }

        this.fc_options.eventDrop = (eventDropInfo) => {
            let selectedNodes = document.querySelectorAll(".ds-selected");
            
            let addDelta = function ({delta, add_to}) {
                add_to = add_to.addDays(delta.days);
                add_to = new Date(add_to.setMonth(add_to.getMonth() + delta.months))
                add_to = new Date(add_to.setFullYear(add_to.getFullYear() + delta.years))

                return add_to;
            }

            for (let i = 0; i < selectedNodes.length; i++) {
                let eventId = getUuidFromEventDomNode(selectedNodes[i]);

                let ev = this.planner.local_context.events.get(eventId);
                ev.from = addDelta({delta: eventDropInfo.delta, add_to: ev.from});
                ev.to = addDelta({ delta: eventDropInfo.delta, add_to: ev.to });

                this.planner.local_context.update_event(ev, ev.id);
            }
            
            let event = {
                id: eventDropInfo.event.extendedProps.event_uuid,
                title: eventDropInfo.event.title,
                from: eventDropInfo.event.start,
                to: eventDropInfo.event.end,
                color: eventDropInfo.event.backgroundColor,
            };

            if (this.dsIsGood === false) {
                this.setup_dragselect();
            }
            
            this.planner.local_context.update_event(event, event.id);
        }

        this.fc_options.eventDidMount = (arg) => {
            let selSeq = this.select_sequence;
            let onClickEditButton = this.onClickEditButton;
            let onClickDeleteButton = this.onClickDeleteButton;
            let uuid = getUuidFromEventDomNode(arg.el);

            let splitOutUuid = function (str) {
                return str.split(" ")[0].split("_")[1];
            }

            let ctxMenuItems = {
                order_service: {
                    name: "<i class='fas fa-comments-dollar text-success'></i> Bestill tjeneste",
                    isHtmlName: true,
                    callback: function (key, opt) {
                        let events = [];
                        let selectedNodes = document.querySelectorAll(".ds-selected");
                        for (let i = 0; i < selectedNodes.length; i++) {
                            events.push(planner.local_context.events.get(getUuidFromEventDomNode(selectedNodes[i])))
                        }

                        planner.renderer_manager.onClickOrderServiceButton(events);
                    }
                },
                edit: {
                    name: "<i class='fas fa-edit text-success'></i> " + this.planner.textLib.get("edit"),
                    isHtmlName: true,
                    callback: function (key, opt) {
                        onClickEditButton(splitOutUuid(opt.selector));
                    }
                },
                delete: {
                    name: "<i class='fas fa-trash text-danger'></i> " + this.planner.textLib.get("delete"),
                    isHtmlName: true,
                    callback: function (key, opt) {
                        onClickDeleteButton(splitOutUuid(opt.selector));
                    }
                },
            };

            if (planner.local_context.events.get(uuid).sequence_guid !== undefined) {
                ctxMenuItems.markSequence = {
                    name: "<i class='fas fa-hand-pointer'></i>&nbsp; Marker serie",
                    isHtmlName: true,
                    callback: function (key, opt) {
                        selSeq(planner.local_context.events.get(splitOutUuid(opt.selector)).sequence_guid);
                    }
                }
            }

            $.contextMenu({
                selector: ".uuid_" + uuid + " :not(ds-selected)",
                items: ctxMenuItems,
            })

            this.ds.addSelectables(document.querySelectorAll(this.dsEventSelector));
        }
    }

    setup_cell_select (view) {
        let self = this;

        console.log(">> View: " + view)
        if (view === "dayGridMonth") {
            this.cellSel = new this.MonthGridCellSelect({
                onCellSelected: (cellEl) => {
                    cellEl.addEventListener('contextmenu', (jsEvent) => {
                        jsEvent.preventDefault();
        
                        $.contextMenu({
                            className: "",
                            selector: '.focused-cell',
                            items: {
                                paste: {
                                    name: "<i class='fas fa-paste'></i>&nbsp; Lim inn",
                                    isHtmlName: true,
                                    callback: function () {
                                        self.handle_hotkey("ctrl+v");
                                    }
                                }
                            }
                        });
                    });
                }}
            );
        }
        if (view === "timeGridWeek" || view === "timeGridDay") {
            this.cellSel = new this.TimeGridCellSelect({
                onCellSelected: (cellEl) => {
                    cellEl.addEventListener('contextmenu', (jsEvent) => {
                        jsEvent.preventDefault();
        
                        $.contextMenu({
                            className: "",
                            selector: '.focused-cell',
                            items: {
                                paste: {
                                    name: "<i class='fas fa-paste'></i>&nbsp; Lim inn",
                                    isHtmlName: true,
                                    callback: function () {
                                        self.handle_hotkey("ctrl+v");
                                    }
                                }
                            }
                        });
                    });
                }
            });
        }
    }

    select_sequence(sequence_guid) {
        document.querySelectorAll(".seq_" + sequence_guid).forEach(function (el) {
            el.style="background-color: #acacff; color:white; border:solid 1px;";
            el.classList.add("ds-selected");
        });
    }

    allocate_people_to_selection (peopleIds) {
        let selectedNodes = document.querySelectorAll(".ds-selected");

        for (let i = 0; i < selectedNodes.length; i++) {
            let event = this.planner.local_context.events.get(getUuidFromEventDomNode(selectedNodes[i]));
            event.people = Array.isArray(event.people) ? event.people.concat(peopleIds) : peopleIds;
            this.planner.local_context.update_event(event, event.id);
        }
    }

    allocate_rooms_to_selection (roomIds) {
        let selectedNodes = document.querySelectorAll(".ds-selected");
        
        for (let i = 0; i < selectedNodes.length; i++) {
            let event = this.planner.local_context.events.get(getUuidFromEventDomNode(selectedNodes[i]));
            event.rooms = Array.isArray(event.rooms) ? event.rooms.concat(roomIds) : roomIds;
            this.planner.local_context.update_event(event, event.id);
        }
    }

    handle_hotkey(key) {
        let selectedEvents = [];
        let selectedEventsDomNodes = document.querySelectorAll(".ds-selected");
        let newEvs = [];

        for (let i = 0; i < selectedEventsDomNodes.length; i++) {
            if (!selectedEventsDomNodes[i].classList.contains("collision_analysis_shadow_event")) {
                newEvs.push(selectedEventsDomNodes[i]);
            }
        }

        selectedEventsDomNodes = newEvs;

        for (let i = 0; i < selectedEventsDomNodes.length; i++) {
            let selectedEvent = this.planner.local_context.events.get(getUuidFromEventDomNode(selectedEventsDomNodes[i]));

            if (selectedEvent !== undefined) {
                selectedEvent.el = selectedEventsDomNodes[i];
                selectedEvents.push(selectedEvent);
            }
        }

        let getStartTime = function (view) {
            let startTime = 0;

            for (let i = 0; i < selectedEvents.length; i++) {
                if (selectedEvents[i].from.getTime() > startTime) {
                    startTime = selectedEvents[i].from;
                }
            }
            
            return startTime;
        }

        if (key === "ctrl+c" || key === "ctrl+x") {
            toastr["success"](selectedEventsDomNodes.length + " hendelser kopiert til utklippstavle!");
        }

        switch (key) {
            case 'ctrl+c': 
                console.log("ctrl+c")
                this.planner.clipboard.setClipboard(selectedEvents, getStartTime("dayGridMonth"), "copy")

                for (let i = 0; i < selectedEventsDomNodes.length; i++) {
                    let ev = selectedEventsDomNodes[i];
                    $(ev).fadeOut(100).fadeIn(100).fadeOut(100).fadeIn(100);
                }
                break;
                
            case 'ctrl+x':
                this.planner.clipboard.setClipboard(selectedEvents, getStartTime("dayGridMonth"), "cut")
                break;

            case 'ctrl+v':
                let date = new Date(this.cellSel.getSelectedDate())
                let pasteComputed = this.planner.clipboard.computePaste(date)
                this.planner.local_context.add_events(pasteComputed);

                if (planner.clipboard.mode === "cut") {
                    this.planner.local_context.remove_events(planner.clipboard.events);
                }
                break;
                
            case 'del':
                this.planner.local_context.remove_events(selectedEvents);
                toastr["warning"](selectedEvents.length + " hendelser slettet!")
                break;
        }
    }

    RenderingUtilities = class RenderingUtilities {

        static renderEventForView(view_name, ev_info) {
            let viewsToRendererMap = new Map([
                ["dayGridMonth", this.renderDayGridMonth_Event],
                ["timeGridWeek", this.renderWeek_Event],
                ["timeGridDay", this.renderWeek_Event],
            ]);
            this.viewsToRendererMap = viewsToRendererMap;

            let renderer_function = this.viewsToRendererMap.get(view_name)
            if (renderer_function === undefined) {
                throw "No event renderer for this view -> (" + view_name + ")";
            }

            return renderer_function(ev_info, this.get_icons_html(ev_info))
        }

        static get_icons_html(info) {
            let icons_wrapper = document.createElement('span');

            if (info.event.extendedProps.sequence_guid !== undefined && info.event.extendedProps.sequence_guid !== null) {
                console.log(info.event.extendedProps.sequence_guid)
                let icon = document.createElement('i');
                icon.classList.add('fas', 'fa-link', 'text-success');
                icons_wrapper.appendChild(icon);
            }
            if (info.event.extendedProps.hasRoom === true) {
                let icon = document.createElement('i');
                icon.classList.add('fas', 'fa-building', 'text-success');
                icons_wrapper.appendChild(icon);
            } 
            if (info.event.extendedProps.hasPeople === true) {
                let icon = document.createElement('i');
                icon.classList.add('fas', 'fa-user', 'text-success');
                icons_wrapper.appendChild(icon);
            }
            if (info.event.extendedProps.hasLooseRequisition === true) {
                let icon = document.createElement('i');
                icon.classList.add('fas', 'fa-dollar-sign', 'text-success');
                icons_wrapper.appendChild(icon);
            }

            return icons_wrapper.outerHTML;
        }

        static renderDayGridMonth_Event(info, icons_html) {
            let rootWrapperNode = document.createElement("span");

            rootWrapperNode.style="overflow:hidden;text-overflow:ellipsis;white-space:nowrap;"
            rootWrapperNode.innerHTML = "&nbsp;<span><i class='fas fa-circle' style='color: " + info.backgroundColor + "'></i></span>&nbsp; <strong>(" + info.timeText + ")</strong> " + info.event.title + "&nbsp;&nbsp;";
            rootWrapperNode.innerHTML += icons_html;            

            return rootWrapperNode;
        }

        static renderWeek_Event(info, icons_html) {
            let rootWrapperNode = document.createElement("span");

            rootWrapperNode.innerHTML = "<strong>" + info.timeText + "</strong>" + icons_html + "<div>" + info.event.title + "</div>"
            
            return rootWrapperNode;
        }
    }

    setup_dragselect() {
        this.ds.start();

        this.ds.subscribe('callback', ({ items, event }) => {
            if (items !== undefined && items.length == 0) {
                let allNodes = document.querySelectorAll(this.dsEventSelector);
                for (let i = 0; i < allNodes.length; i++) {
                    allNodes[i].style="";
                }
            }

            let planner = this.planner;
            let self = this;

            for (let i = 0; i < items.length; i++) {
                if ($(items[i]).hasClass("shadow-event")) {
                    continue;
                }

                items[i].addEventListener("contextmenu", (jsEvent) => {
                    jsEvent.preventDefault();

                    let items = {
                        batch_comment: {
                            name: "<i class='fas fa-comment text-success'></i>&nbsp; Kommenter på seleksjon",
                            isHtmlName: true,
                            callback: function () {}
                        },
                        batch_order: {
                            name: "<i class='fas fa-comments-dollar text-success'></i>&nbsp; Bestill tjeneste for seleksjon",
                            isHtmlName: true,
                            callback: function () { 
                                let events = [];
                                let selectedNodes = document.querySelectorAll(".ds-selected");
                                for (let i = 0; i < selectedNodes.length; i++) {
                                    events.push(planner.local_context.events.get(getUuidFromEventDomNode(selectedNodes[i])))
                                }

                                planner.renderer_manager.onClickOrderServiceButton(events);
                            }
                        },
                        batch_allocate_person: {
                            name: "<i class='fas fa-user text-info'></i>&nbsp; Alloker personressurser for selekterte hendelser",
                            isHtmlName: true,
                            callback: function () { loadAllocatePeopleDialog(); }
                        },
                        batch_allocate_room: {
                            name: "<i class='fas fa-building text-info'></i>&nbsp; Alloker romressurser for selekterte hendelser",
                            isHtmlName: true,
                            callback: function () { loadAllocateRoomsDialog(); }
                        },
                        batch_color: {
                            name: "<i class='fas fa-palette text-secondary'></i>&nbsp; Fargelegg seleksjon",
                            isHtmlName: true,
                            callback: function () {
                                colorEventsDialog.save = function (newColor) {
                                    console.log(">> Save")
                                    let events = [];
                                    let selectedNodes = document.querySelectorAll(".ds-selected");
                                    for (let i = 0; i < selectedNodes.length; i++) {
                                        events.push(planner.local_context.events.get(getUuidFromEventDomNode(selectedNodes[i])))
                                    }

                                    for (let i = 0; i < events.length; i++) {
                                        events[i].color = newColor;
                                    }

                                    planner.local_context.update_events(events);
                                }

                                colorEventsDialog.open();
                            }
                        },
                        "sep1": "---------",
                        copy_batch: {
                            name: "<i class='fas fa-copy text-success'></i>&nbsp; Kopier seleksjon",
                            isHtmlName: true,
                            callback: function () {
                                self.handle_hotkey("ctrl+c");
                            }
                        },
                        cut_batch: {
                            name: "<i class='fas fa-cut text-warning'></i>&nbsp; Kutt seleksjon",
                            isHtmlName: true,
                            callback: function () {
                                self.handle_hotkey("ctrl+x");
                            }
                        },
                        batch_delete: {
                            name: "<i class='fas fa-trash text-danger'></i>&nbsp; Slett seleksjon",
                            isHtmlName: true,
                            callback: function () {
                                self.handle_hotkey("del");
                            }
                        },
                    };
                    
                    $.contextMenu({
                        className: 'webook-context-menu',
                        selector: '.fc-event-main, .fc-daygrid-event',
                        items: items,
                    })
                })
            }
        });

        this.ds.subscribe('predragstart', ({ isDragging, isDraggingKeyboard}) => {
            // If a serie has been marked through the custom marking functionality through the context menu,
            // then we need to clean it up before DragSelect initiates. This due to inconsistencies.
            document.querySelectorAll(".ds-selected").forEach(function (el) {
                el.classList.remove(".ds-selected");
            })
            
        })

        this.ds.subscribe('dragmove', ({items, event, isDragging}) => {
            let allNodes = document.querySelectorAll(this.dsEventSelector);

            for (let i = 0; i < allNodes.length; i++) {
                allNodes[i].style="";
            }

            let selectedNodes = this.ds.getSelection();
            
            let visibleCounter = 0;
            for (let i = 0; i < selectedNodes.length; i++) {
                if (document.body.contains(selectedNodes[i])) {
                    visibleCounter++;
                }
                selectedNodes[i].style="background-color: #acacff; color:white; border:solid 1px;";
                if (isDragging === true) {
                    if (selectedNodes.length === 1) {
                        $(selectedNodes).offset({left: event.pageX, top: event.pageY });
                    }
                    else {
                        let rect = $(selectedNodes[i])[0].getBoundingClientRect();
                        $(selectedNodes[i]).offset({ left: event.pageX, top: event.pageY + (visibleCounter * 35)});
                    }
                }
            }
        });

        this.dsIsGood = true;
    }

    teardown_dragselect() {
        this.ds.stop()
        this.dsIsGood = false;
    }

    go_to_year(year) {
        this.calendar.gotoDate(new Date(this.calendar.getDate().setFullYear(year)));
    }

    go_to_month(month) {
        this.calendar.gotoDate(new Date(this.calendar.getDate().setMonth(month)));
    }

    convert_events(events) {
        let fc_events = []
        console.log(events);
        for (let i = 0; i < events.length; i++) {
            let event = events[i];
            var classNames = ["uuid_" + event.id, (event.sequence_guid !== undefined ? "seq_" + event.sequence_guid : "")]
            if (event.extra_classes !== undefined) {
                classNames = classNames.concat(event.extra_classes);
            }
            fc_events.push({
                "id": event.id,
                "title": event.title,
                "start": event.from,
                "editable": event.editable === undefined ? true : event.editable,
                "textColor": event.textColor === undefined ? "" : event.textColor,
                "end": event.to,
                "classNames": classNames,
                "extendedProps": {
                    "event_uuid": event.id,
                    "serie_uuid": event.serie_uuid,
                    "is_shadow": event.is_shadow !== undefined ? event.is_shadow : false,
                    "hasRoom": event.rooms !== undefined ? event.rooms.length > 0 : false,
                    "hasPeople": event.people !== undefined ? event.people.length > 0 : false,
                    "hasLooseRequisition": event.loose_requisitions === undefined ? false : event.loose_requisitions.length > 0,
                    "sequence_guid": event.sequence_guid,
                },
                "backgroundColor": event.color,
            })
        }

        return fc_events;
    }

    TimeGridCellSelect = class CellSelect {
        constructor ({ onCellSelected=undefined } = {}) {
            this.currentlySelectedCell = undefined;
            this.currentlySelectedCellTextWrapper = undefined;
            this.onCellSelected = onCellSelected;
        }

        getSelectedDate() {
            console.log(this.currentlySelectedCell)
            console.log(this.currentlySelectedCell.attr("data-date"))
            return this.currentlySelectedCell.attr("data-date");
        }

        generateHintTextElement() {
            let hintEl = document.createElement("span");
            hintEl.innerText = "CTRL-V for å lime inn kopierte hendelser her"
            
            return hintEl;
        }

        selectCell(el) {
            this.unselectCell();

            el.addClass('focused-cell ');
            this.currentlySelectedCell = el;
            let textContainer = el[0].querySelectorAll(".fc-daygrid-day-bg");
            this.currentlySelectedCellTextWrapper = textContainer[0];

            this.onCellSelected(el[0])
        }

        unselectCell() {
            $(this.currentlySelectedCell).removeClass("focused-cell ");
            if (this.currentlySelectedCell !== undefined) {
                this.currentlySelectedCell = undefined;
                this.currentlySelectedCellTextWrapper.innerHTML = "";
                this.currentlySelectedCellTextWrapper = undefined;
            }
        }
    }

    MonthGridCellSelect = class CellSelect {
        constructor ({ onCellSelected=undefined } = {}) {
            this.currentlySelectedCell = undefined;
            this.currentlySelectedCellTextWrapper = undefined;
            this.onCellSelected = onCellSelected;
        }

        getSelectedDate() {
            return this.currentlySelectedCell.attr("data-date");
        }

        generateHintTextElement() {
            let hintEl = document.createElement("span");
            hintEl.innerText = "CTRL-V for å lime inn kopierte hendelser her"

            return hintEl;
        }

        selectCell(el) {
            this.unselectCell();

            el.addClass('focused-cell ');
            this.currentlySelectedCell = el;
            let textContainer = el[0].querySelectorAll(".fc-daygrid-day-bg");
            this.currentlySelectedCellTextWrapper = textContainer[0];

            this.onCellSelected(el[0])
        }

        unselectCell() {
            $(this.currentlySelectedCell).removeClass("focused-cell ");
            if (this.currentlySelectedCell !== undefined) {
                this.currentlySelectedCell = undefined;
                this.currentlySelectedCellTextWrapper.innerHTML = "";
                this.currentlySelectedCellTextWrapper = undefined;
            }
        }
    }

    redraw() {
        this.calendar.render();
    }

    render(events) {
        let calendar_element = document.getElementById(this.element_id);

        let fc_events = this.convert_events(events);
        this.fc_options.events = fc_events;

        if (this.calendar !== undefined) {
            this.fc_options.initialView = this.calendar.view.type;
            this.fc_options.initialDate = this.calendar.getDate();
        }

        this.calendar = new FullCalendar.Calendar(calendar_element, this.fc_options);
        this.calendar.render();

        this.ds.addSelectables(document.querySelectorAll(this.dsEventSelector));
    }
}

class TimeLineManager extends RendererBase {

    constructor(timeline_element_id) {
        super(RendererBase);
        this.timeline_element = document.getElementById(timeline_element_id);
        this.options = {};
        this.timeline = undefined;   
        this.dataset = new vis.DataSet();
    }

    flush_dataset() {
        this.dataset.clear();
    }

    read_in_events(events) {
        let events_converted = [];

        for (let i = 0; i < events.length; i++) {
            let event = events[i];
            events_converted.push({
                id: i,
                content: event.title,
                start: event.from.toISOString(),
                end: event.to.toISOString(),
                style: "background-color:" + event.color + ";",
            })
        }

        this.flush_dataset();
        this.dataset.add(events_converted);
    }

    render (events) {
        this.read_in_events(events);
        if (this.timeline === undefined) {
            this.timeline = new vis.Timeline(this.timeline_element, this.dataset, this.options);
        }
        else {
            this.timeline.redraw();
            this.timeline.fit();
        }
    }
}

/* 
    Provides utilities to wrap around and manage a simple HTML table
*/
class SimpleTableManager extends RendererBase {

    constructor(table_element_id, onClickDeleteButton, onClickEditButton, onClickInfoButton) {
        super(RendererBase);
        this.table_element_id = table_element_id;
        this.table_element = document.getElementById(this.table_element_id);
        this.tbody_element = this.table_element.getElementsByTagName('tbody')[0];

        this.onClickDeleteButton = onClickDeleteButton;
        this.onClickEditButton = onClickEditButton;
        this.onClickInfoButton = onClickInfoButton;

        this.primary_render()
    }

    /* 
        Gets all the rows in the current table (as elements)
    */
    get_rows() {
        return this.tbody_element.getElementsByTagName('tr');
    }

    /* 
        Removes all rows from the table
    */
    flush_rows() {
        let rows = this.get_rows();
        for (let i = rows.length; i >= 0; i--) {
            if (rows[i] !== undefined) {
                rows[i].remove();
            }
        }
    }

    add_row(row_element) {
        this.tbody_element.appendChild(row_element);
    }

    convert_event_to_row(event) {
        let row = document.createElement('tr');

        let color_col = document.createElement('td');
        color_col.innerHTML = "";
        color_col.style="background-color:" + event.color + ";";

        let name_col = document.createElement('td');
        name_col.innerText = event.title;

        let time_col = document.createElement('td');
        time_col.innerText = event.from + " " + event.to;

        let options_col = document.createElement('td');

        let onClickEditButton = this.onClickEditButton;
        let onClickDeleteButton = this.onClickDeleteButton;
        let onClickInfoButton = this.onClickInfoButton;

        let edit_button = document.createElement('button');
        edit_button.classList.add('btn', 'btn-success', 'btn-sm', 'btn-block')
        edit_button.onclick = function () { onClickEditButton(event.id); }
        edit_button.innerText = "Edit";
        let delete_button = document.createElement('button');
        delete_button.classList.add('btn', 'btn-danger', 'btn-sm','btn-block')
        delete_button.onclick = function () { onClickDeleteButton(event.id); }
        delete_button.innerText = "Delete";

        options_col.append(edit_button, delete_button);

        row.append(
            color_col,
            name_col,
            time_col,
            options_col
        );

        return row;
    }

    primary_render() {
        let thead_el = this.table_element.getElementsByTagName('thead')[0];
        let tbody_el = this.table_element.getElementsByTagName('tbody')[0];
        let tfoot_el = this.table_element.getElementsByTagName('tfoot')[0];

        let theadRow = document.createElement('tr');

        let theadColorCol = document.createElement('th');

        let theadNameCol = document.createElement('th');
        theadNameCol.innerText = "Name";

        let theadTimeCol = document.createElement('th');
        theadTimeCol.innerText = "Time";

        let theadOptionsCol = document.createElement('th');
        theadOptionsCol.innerText = "Options";

        theadRow.append(theadColorCol, theadNameCol, theadTimeCol, theadOptionsCol);
        thead_el.append(theadRow)
    }

    render(events) {
        this.flush_rows();

        for (let i = 0; i < events.length; i++) {
            this.add_row(this.convert_event_to_row(events[i]));
        }
    }
}