import { HeaderGenerator, ViewClassifiers } from "./calendar_utilities/header_generator.js";
import {
    ArrangementStore, CalendarFilter, FullCalendarBased, LocationStore,
    PersonStore, StandardColorProvider, _FC_EVENT,
    _NATIVE_ARRANGEMENT
} from "./commonLib.js";
// import { FilterDialog } from "./filterDialog.js";

const ARIA_ATTRIBUTE_PATTERN = /^aria-[\w-]*$/i;

export class PlannerCalendar extends FullCalendarBased {

    constructor({ 
        calendarElement, 
        arrangementInspectorUtility,
        eventInspectorUtility,
        eventsSrcUrl, 
        colorProviders=[], 
        initialColorProvider="",
        csrf_token=undefined, 
        licenseKey=undefined,
        navigationHeaderWrapperElement = undefined,
        calendarFilter=undefined,
        useOnclickEvents=true,
        renderContextMenu = true,
        height = null,
        showAdministrativeActionsInContextMenu = false,
        renderPopovers=true, } = {},) {

        super(navigationHeaderWrapperElement);

        this.height = height;

        this.showAdministrativeActionsInContextMenu = showAdministrativeActionsInContextMenu;
        this.useOnclickEvents = useOnclickEvents;
        this.renderContextMenu = renderContextMenu;
        this.renderPopovers = renderPopovers;

        this.viewButtons = new Map([
            [1, {
                "key": 1,
                "title": "Dag",
                "isParent": true,
                "view": "timeGridDay",
                "parent": undefined,
                "weight": 100,
            }],
            [2, {
                "key": 2,
                "title": "Måned",
                "isParent": true,
                "view": "dayGridMonth",
                "parent": undefined,
                "weight": 200,
            }],
            [3, {
                "key": 3,
                "title": "Tidslinje",
                "isParent": false,
                "view": "timelineMonth",
                "parent": 2,
                "weight": undefined,
            }],
            [4, {
                "key": 4,
                "title": "Grid",
                "isParent": false,
                "view": "dayGridMonth",
                "parent": 2,
                "weight": undefined,
            }],
            [5, {
                "key": 5,
                "title": "Uke",
                "isParent": true,
                "view": "timeGridWeek",
                "parent": undefined,
                "weight": 300,
            }],
            [6, {
                "key": 6,
                "title": "År",
                "isParent": false,
                "view": "timelineYear",
                "afterClick": () => {
                    let target = $('.fc-timelineYear-view th.fc-timeline-slot[data-date=' + this._fcCalendar.getDate().toISOString().split("T")[0] + ']')
                    if (target.length) {
                        $(".fc-timelineYear-view div.fc-scroller-liquid-absolute").scrollTo(target);
                    }
                },
                "parent": undefined,
                "weight": 400,
            }],
            [7, {
                "key": 7,
                "title": "Liste",
                "isParent": false,
                "view": "listWeek",
                "parent": 5,
                "weight": undefined,
            }],
            [8, {
                "key": '5',
                "title": "Tidsgrid",
                "isParent": false,
                "view": "timeGridWeek",
                "parent": 5,
                "weight": undefined,
            }],
            [9, {
                "key": '5',
                "title": "Dagsgrid",
                "isParent": false,
                "view": "dayGridWeek",
                "parent": 5,
                "weight": undefined,
            }],


            [10, {
                "key": 10,
                "title": "Liste",
                "isParent": false,
                "view": "listDay",
                "parent": 1,
                "weight": undefined
            }],
            [8, {
                "key": 8,
                "title": "Grid",
                "isParent": false,
                "view": "timeGridDay",
                "parent": 1,
                "weight": 100,
            }],
        ]);

        this.csrf_token = csrf_token;
        this._headerGenerator = new HeaderGenerator(
            { customClassifications: new Map([
                [ "customTimeGridMonth", ViewClassifiers.MONTH ],
                [ "calendarDayGridMonth", ViewClassifiers.MONTH ],
                [ "customTimelineMonth", ViewClassifiers.MONTH ],
                [ "customTimelineYear", ViewClassifiers.YEAR ]
            ]) }
        );
        
        this._fcLicenseKey = licenseKey;
        this._fcCalendar = undefined;
        this._calendarElement = calendarElement;
        this._eventsSrcUrl = eventsSrcUrl;

        this._filteredAudiences = [];
        this._filteredArrangementTypes = [];

        this._colorProviders = new Map();
        this._colorProviders.set("DEFAULT", new StandardColorProvider());

        colorProviders.forEach( (bundle) => {
            this._colorProviders.set(bundle.key, bundle.provider)
        });

        // If user has not supplied an active color provider key we use default color provider as active.
        this.activeColorProvider = initialColorProvider !== undefined && this._colorProviders.has(initialColorProvider) ? this._colorProviders.get(initialColorProvider) : this._colorProviders.get("DEFAULT");
        this._ARRANGEMENT_STORE = new ArrangementStore(this.activeColorProvider, this._eventsSrcUrl);
        this._LOCATIONS_STORE = new LocationStore(this);
        this._PEOPLE_STORE = new PersonStore(this);

        this.filter = calendarFilter ?? new CalendarFilter( /* OnFilterUpdated: */ (filter) => this.init() );

        this.init();

        this.arrangementInspectorUtility = arrangementInspectorUtility;
        this.eventInspectorUtility = eventInspectorUtility;
        // this.filterDialog = new FilterDialog();

        this._listenToInspectArrangementEvents();
        this._listenToInspectEvent();
    }

    getFcCalendar() {
        return this._fcCalendar;
    }

    _listenToInspectArrangementEvents() {
        document.addEventListener("plannerCalendar.inspectThisArrangement", (e) => {
            let arrangement = this._ARRANGEMENT_STORE.get({
                pk: e.detail.event_pk,
                get_as: _NATIVE_ARRANGEMENT
            });
    
            this.arrangementInspectorUtility.inspect(arrangement);
        })
    }

    _listenToInspectEvent() {
        document.addEventListener("plannerCalendar.inspectEvent", (e) => {
            this.eventInspectorUtility.inspect(e.detail.event_pk);
        })
    }

    /**
     * Set a new active color provider, identified by the given key. 
     * Set color provider must have been registered on initialization of planner calendar.
     * @param {*} key 
     */
    setActiveColorProvider(key) {
        if (this._colorProviders.has(key)) {
            this.activeColorProvider = key;
        }
        else {
            console.error(`Color provider with the given key: '${this.key}' does not exist.`)
        }
    }

    // /**
    //  * Get the currently active color provider instance
    //  * @returns active color provider
    //  */
    _getColorProvider() {
        return this._colorProviders.get(this.activeColorProvider);
    }

    /**
     * Bind popover with arrangement info to elementToBindWith
     * @param {*} elementToBindWith 
     */
    _bindPopover (elementToBindWith) {
        let pk = this._findEventPkFromEl(elementToBindWith);        
        let arrangement = this._ARRANGEMENT_STORE.get({
            pk: pk,
            get_as: _NATIVE_ARRANGEMENT
        });

        if (arrangement === undefined) {
            console.error(`Could not bind popover for arrangement with pk ${pk}`);
            return;
        }

        let start = new Date(arrangement.starts)
        let end = new Date(arrangement.ends)
        start = `${
            (start.getMonth()+1).toString().padStart(2, '0')}/${
            start.getDate().toString().padStart(2, '0')}/${
            start.getFullYear().toString().padStart(4, '0')} ${
            start.getHours().toString().padStart(2, '0')}:${
            start.getMinutes().toString().padStart(2, '0')}:${
            start.getSeconds().toString().padStart(2, '0')}`
        end = `${
            (end.getMonth()+1).toString().padStart(2, '0')}/${
            end.getDate().toString().padStart(2, '0')}/${
            end.getFullYear().toString().padStart(4, '0')} ${
            end.getHours().toString().padStart(2, '0')}:${
            end.getMinutes().toString().padStart(2, '0')}:${
            end.getSeconds().toString().padStart(2, '0')}`


        let roomsListHtml = "<div>";
        arrangement.room_names.forEach( (roomName) => {
            if (roomName !== null) {
                roomsListHtml += "<span class='chip'>" + roomName + "</span>";
            }
        });
        roomsListHtml += "</div>";
        if (roomsListHtml !== "<div></div>") {
            roomsListHtml = "<h6><i class='fas fa-building'></i>&nbsp; Rom:</h6>" + roomsListHtml
        }

        let peopleListHtml = "<div>";
        arrangement.people_names.forEach( (personName) => {
            if (personName !== null) {
                peopleListHtml += "<span class='chip'>" + personName + "</span>";
            }
        })
        peopleListHtml += "</div>";
        if (peopleListHtml !== "<div></div>") {
            peopleListHtml = "<h6><i class='fas fa-users'></i>&nbsp; Personer:</h6>" + peopleListHtml;
        }

        let badgesHtml = "";
        if (arrangement.evserie_id !== null) {
            badgesHtml += `<span class="badge badge-secondary"><i class='fas fa-sync'></i></span>`;
        }
        else if (arrangement.evserie_id === null && arrangement.association_type === "degraded_from_serie") {
            badgesHtml += `
            <span class="badge badge-warning">
                <i class='fas fa-sync'></i> <i class='fas fa-times'></i>
            </span>`
        }
        else {
            badgesHtml += `
            <span class="badge badge-success">
                <i class='fas fa-calendar'></i>
            </span>`
        }

        let statusForegroundTextColor = "black";
        if (arrangement.status_color) {
            const contrast_rating = new Color(arrangement.status_color).contrast(new Color("black"), "WCAG21");
            if (contrast_rating > 3)
                statusForegroundTextColor = "white";
        }

        new mdb.Popover(elementToBindWith, {
            trigger: "hover",
            allowList: {
                '*': ['class', 'dir', 'id', 'lang', 'role', ARIA_ATTRIBUTE_PATTERN],
                a: ['target', 'href', 'title', 'rel'],
                area: [],
                b: [],
                br: [],
                col: [],
                code: [],
                div: ['style'],
                em: [],
                hr: [],
                h1: [],
                h2: [],
                h3: [],
                h4: [],
                h5: [],
                h6: [],
                i: [],
                img: ['src', 'srcset', 'alt', 'title', 'width', 'height'],
                li: [],
                ol: [],
                p: [],
                pre: [],
                s: [],
                small: [],
                span: [],
                sub: [],
                sup: [],
                strong: [],
                u: [],
                ul: [],
            },
            content: `
                <h5 class='mb-0 mt-2 fw-bold'>${arrangement.name}</h5>
                <div>
                    ${arrangement.arrangement_name}
                </div>
                <em class='small'>${start} - ${end}</em>

                ${badgesHtml}

                <hr>
                <div class='row'>
                    <div class='col-6 text-center'>
                        <div class='text-center'>
                            <i class='fas fa-theater-masks'></i>&nbsp;
                        </div>
                        ${arrangement.audience}
                    </div>
                    <div class='col-6 text-center'>
                        <div class='text-center'>
                            <i class='fas fa-user'></i>&nbsp;
                        </div>
                        ${arrangement.mainplannername}
                    </div>
                    <div class='col-6 mt-2 text-center'>
                        <div class='text-center'>
                            <i class='fas fa-building'></i>&nbsp; 
                        </div>
                        ${arrangement.location}
                    </div>
                    <div class='col-6 mt-2 text-center'>
                        <div class='text-center'>
                            <i class='fas fa-cog'></i>&nbsp;
                        </div>
                        ${arrangement.arrangement_type}
                    </div>
                    <div class='text-end mt-2'>
                        <i>Forventet antall besøkende:</i> ${arrangement.expected_visitors}
                    </div>
                    <div class='col-12 text-center mt-2'>
                        <div class='border border-1 p-2 rounded-pill fw-bold' style='background-color: ${arrangement.status_color};color:${statusForegroundTextColor};'>
                            ${ arrangement.status_name ?? "Ingen status" }
                        </div>
                    </div>
                </div>
                <hr>

                ${roomsListHtml}
                
                ${peopleListHtml}

                <div class='text-end small'>
                    <em>Opprettet ${arrangement.created_when}</em>
                </div>
                `,
            html: true,
        })
    }

    _bindInspectorTrigger (elementToBindWith) {
        let _this = this;
        $(elementToBindWith).on('click', (ev) => {
            let pk = _this._findEventPkFromEl(ev.currentTarget);
            this.eventInspectorUtility.inspect(pk);
        })
    }


    refresh() {
        this.init()
    }

    /**
     * First-time initialize the calendar
     */
    async init() {
        let _this = this;

        let initialView = 'dayGridMonth';

        if (this._fcCalendar === undefined) {
            this._fcCalendar = new FullCalendar.Calendar(this._calendarElement, {
                schedulerLicenseKey: this._fcLicenseKey,
                stickyFooterToolbar: true,
                initialView: initialView,
                selectable: true,
                weekNumbers: true,
                navLinks: true,
                minTime: "06:00",
                height: this.height,
                maxTime: "23:00",
                slotEventOverlap: false,
                locale: 'nb',
                views: {
                    customTimeGridMonth: {
                        type: "timeGrid",
                        duration: { month: 1 },
                        buttonText: "Tidsgrid Måned"
                    },
                    calendarDayGridMonth: {
                        type: 'dayGridMonth',
                        buttonText: 'Kalender'
                    },
                    customTimelineMonth: {
                        type: 'timelineMonth',
                        buttonText: 'Tidslinje - Måned'
                    },
                    customTimelineYear: {
                        type: 'timelineYear',
                        buttonText: 'Tidslinje - År'
                    }
                },
                datesSet: (dateInfo) => {
                    if (dateInfo.view.type == "dayGridDay") {
                        document.dispatchEvent(
                            new CustomEvent(this._instanceUUID + "_callForFullCalendarViewRender", { "detail": { "view": "timeGridDay" } })
                        );
                    }
                    if (dateInfo.view.type == "dayGridWeek") {
                        $('.fc-daygrid-day-number, .fc-daygrid-week-number').hide();
                        document.dispatchEvent(
                            new CustomEvent(this._instanceUUID + "_callForFullCalendarViewRender", { "detail": { "view": "dayGridWeek" } })
                        );
                    }
                    if (dateInfo.view.type == "dayGridMonth") {
                        document.dispatchEvent(
                            new CustomEvent(this._instanceUUID + "_callForFullCalendarViewRender", { "detail": { "view": "dayGridMonth" } })
                        )
                    }

                    $('#plannerCalendarHeader').text("");
                    $(".popover").popover('hide');
                    $('#plannerCalendarHeader').text(this._headerGenerator.generate(
                        dateInfo.view.type,
                        this._fcCalendar.getDate(),
                    ));
                },
                customButtons: {
                    filterButton: {
                        text: 'Filtrering',
                        click: () => {
                            // this.filterDialog.openFilterDialog();
                        }
                    },
                },
                eventContent: function (arg) {
                    const formatTime = function (text) {
                        if (text.length == 1 || text.length == 3)
                            text = "0" + text
                        if (text.length == 2)
                            text += ":00"
                            
                        return text;
                    }

                    if (arg.backgroundColor === "prussianblue") {
                        if (arg.view.type == "dayGridMonth" || arg.view.type == "dayGridWeek") {
                            return { html: `<div><span class='d-block float-end me-3 fw-bold'>${arg.event.title}</strong></div>` };
                        }
                        else {
                            return { html: `<div><span class='d-block fw-bold'>${arg.event.title}</strong></div>` };
                        }
                    }

                    if (arg.view.type === "dayGridMonth" || arg.view.type === "dayGridWeek") {
                        let nodes = [];

                        const eventIsSameDay = (arg.event.start !== null && arg.event.end !== null) &&
                            arg.event.start.getFullYear() === arg.event.end.getFullYear() &&
                            arg.event.start.getMonth() === arg.event.end.getMonth() &&
                            arg.event.start.getDate() === arg.event.end.getDate();

                        let colorDot = document.createElement('div');
                        colorDot.classList.add("fc-daygrid-event-dot");
                        colorDot.style = "border-color: " + arg.backgroundColor;
                        if (eventIsSameDay === true)
                            nodes.push(colorDot);

                        let timeText = document.createElement('strong');
                        timeText.style="font-family: 'Roboto Mono';"
                        timeText.innerText = `${formatTime(arg.timeText)}`;
                        nodes.push(timeText);

                        let iconsRail = document.createElement('span');
                        nodes.push(iconsRail);

                        let hasIcon = false;

                        if (arg.event.extendedProps.isRigging === true) {
                            let riggingIconEl = document.createElement('i');
                            riggingIconEl.classList.add("fas", "fa-hammer", "fa-fw", "ms-2", "me-1");
                            nodes.push(riggingIconEl);
                            hasIcon = true;
                        }
                        if (arg.event.extendedProps.isSerie === true) {
                            let serieIconEl = document.createElement('i');
                            serieIconEl.classList.add("fas", "fa-sync", "fa-fw", "ms-2", "me-1");
                            nodes.push(serieIconEl);
                            hasIcon = true;
                        }

                        if (hasIcon === false) {
                            let spacerElement = document.createElement("i")
                            spacerElement.classList.add("fas", "fa-sync", "fa-fw", "ms-2", "me-1");
                            spacerElement.style = "visibility: hidden!important;"
                            nodes.push(spacerElement);
                        }

                        let eventTitle = document.createElement('span');
                        eventTitle.classList.add("ms-1", "event-title-text");
                        eventTitle.innerText = arg.event.title;
                        nodes.push(eventTitle);

                        return { domNodes: nodes };
                    }
                    if (arg.view.type === "timelineMonth" || arg.view.type === "timelineYear") {
                        let nodes = [];

                        let timeText = document.createElement('strong');
                        timeText.classList.add('d-block');
                        timeText.innerText = `(${formatTime(arg.timeText)})`;
                        nodes.push(timeText);

                        let iconsRail = document.createElement('div');
                        nodes.push(iconsRail);

                        if (arg.event.extendedProps.isRigging === true) {
                            let riggingIconEl = document.createElement('i');
                            riggingIconEl.classList.add("fas", "fa-hammer");
                            iconsRail.appendChild(riggingIconEl);
                        }
                        if (arg.event.extendedProps.isSerie === true) {
                            let serieIconEl = document.createElement('i');
                            serieIconEl.classList.add("fas", "fa-sync");
                            iconsRail.appendChild(serieIconEl);
                        }

                        let eventTitle = document.createElement('span');
                        eventTitle.classList.add("event-title-text")
                        eventTitle.innerText = arg.event.title;
                        nodes.push(eventTitle);

                        return { domNodes: nodes };
                    }
                    if (arg.view.type === "timeGridDay" || arg.view.type === "timeGridWeek") {
                        let nodes = [];

                        let wrapper = document.createElement('div');
                        wrapper.classList.add("p-2");

                        let iconsRail = document.createElement('div');
                        wrapper.appendChild(iconsRail);

                        if (arg.event.extendedProps.isRigging === true) {
                            let riggingIconEl = document.createElement('i');
                            riggingIconEl.classList.add("fas", "fa-hammer");
                            iconsRail.appendChild(riggingIconEl);
                        }
                        if (arg.event.extendedProps.isSerie === true) {
                            let serieIconEl = document.createElement('i');
                            serieIconEl.classList.add("fas", "fa-sync");
                            iconsRail.appendChild(serieIconEl);
                        }

                        let timeText = document.createElement('strong');
                        timeText.classList.add('d-block');
                        timeText.innerText = `(${formatTime(arg.timeText)})`;
                        wrapper.appendChild(timeText);

                        let eventTitle = document.createElement('strong');
                        eventTitle.classList.add("mb-2", "event-title-text");
                        eventTitle.innerText = arg.event.title;
                        wrapper.appendChild(eventTitle);

                        nodes.push(wrapper);

                        return { domNodes: nodes };
                    }
                    if (arg.view.type === "listWeek") {
                        let nodes = [];

                        if (arg.event.extendedProps.isRigging === true ||
                            arg.event.extendedProps.isSerie === true) {
                                
                            let iconsRail = document.createElement('span');
                            iconsRail.classList.add("me-2");
                            if (arg.event.extendedProps.isRigging === true) {
                                let riggingIconEl = document.createElement('i');
                                riggingIconEl.classList.add("fas", "fa-hammer");
                                iconsRail.appendChild(riggingIconEl);
                            }
                            if (arg.event.extendedProps.isSerie === true) {
                                let serieIconEl = document.createElement('i');
                                serieIconEl.classList.add("fas", "fa-sync");
                                iconsRail.appendChild(serieIconEl);
                            }
                            nodes.push(iconsRail);
                        }

                        let titleElement = document.createElement('span');
                        titleElement.innerText = arg.event.title;
                        titleElement.classList.add("event-title-text");
                        nodes.push(titleElement);

                        return { domNodes: nodes };
                    }
                },
                headerToolbar: { left: '' , center: '', right: '' },
                eventSources: [
                    {
                        events: async (start, end, startStr, endStr, timezone) => {
                            return await _this._ARRANGEMENT_STORE._refreshStore(start, end)
                                .then(_ => _this._ARRANGEMENT_STORE.get_all(
                                    { 
                                        get_as: _FC_EVENT, 
                                        locations: this.filter.locations,
                                        arrangement_types: this.filter.arrangementTypes,
                                        statuses: this.filter.statuses,
                                        audience_types: this.filter.audiences,
                                        filterSet: this.filter.rooms,
                                    }
                                ));
                        }
                    },
                    {
                        url: "/static/holidays.json",
                        color: "prussianblue",
                        display: "background",
                        textColor: "white",
                    }
                ],

                loading: function( isLoading ) {
                    if (isLoading === false) {
                        $(".popover").popover('hide');
                    }
                },
                eventAfterAllRender: function (view) {
   
                },
                eventDidMount: (arg) => {
                    if (arg.backgroundColor == "prussianblue") {
                        return;
                    }

                    if (this.renderPopovers === true)
                        this._bindPopover(arg.el);
                    if (this.useOnclickEvents)
                        this._bindInspectorTrigger(arg.el);
                }
            })

            if (this.renderContextMenu) {
                let items = {
                    arrangement_inspector: {
                        name: "<i class='fas fa-search'></i>&nbsp; Inspiser arrangement",
                        isHtmlName: true,
                        callback: (key, opt) => {
                            if (!opt.event || opt.event.backgroundColor !== "prussianblue") {
                                let pk = _this._findEventPkFromEl(opt.$trigger[0]);
                                let arrangement = _this._ARRANGEMENT_STORE.get({
                                    pk: pk,
                                    get_as: _NATIVE_ARRANGEMENT
                                });
                        
                                this.arrangementInspectorUtility.inspect(arrangement);
                            }

                        }
                    },
                    event_inspector: {
                        name: "<i class='fas fa-search'></i>&nbsp; Inspiser tidspunkt",
                        isHtmlName: true,
                        callback: (key, opt) => {
                            if (!opt.event || opt.event.backgroundColor !== "prussianblue") {
                                let pk = _this._findEventPkFromEl(opt.$trigger[0]);
                                this.eventInspectorUtility.inspect(pk);
                            }
                        }
                    },
                }

                if (this.showAdministrativeActionsInContextMenu) {
                    items["section_sep_1"] = "---------";
                    items["delete_arrangement"] = {
                        name: "<i class='fas fa-trash'></i>&nbsp; Slett arrangement",
                        isHtmlName: true,
                        callback: (key, opt) => {
                            Swal.fire({
                                title: 'Er du sikker?',
                                text: "Arrangementet og underliggende aktiviteter vil bli fjernet, og kan ikke hentes tilbake.",
                                icon: 'warning',
                                showCancelButton: true,
                                confirmButtonColor: '#3085d6',
                                cancelButtonColor: '#d33',
                                confirmButtonText: 'Ja',
                                cancelButtonText: 'Avbryt'
                            }).then((result) => {
                                if (result.isConfirmed) {
                                    let slug = _this._findSlugFromEl(opt.$trigger[0]);
                                    fetch('/arrangement/arrangement/delete/' + slug, {
                                        method: 'DELETE',
                                        headers: {
                                            "X-CSRFToken": this.csrf_token
                                        }
                                    }).then(_ => {
                                        document.dispatchEvent(new Event("plannerCalendar.refreshNeeded")); // Tell the planner calendar that it needs to refresh the event set
                                    });
                                }
                            })
                        }
                    };
                    items["delete_event"] = {
                        name: "<i class='fas fa-trash'></i>&nbsp; Slett aktivitet",
                        isHtmlName: true,
                        callback: (key, opt) => {
                            Swal.fire({
                                title: 'Er du sikker?',
                                text: "Hendelsen kan ikke hentes tilbake.",
                                icon: 'warning',
                                showCancelButton: true,
                                confirmButtonColor: '#3085d6',
                                cancelButtonColor: '#d33',
                                confirmButtonText: 'Ja',
                                cancelButtonText: 'Avbryt'
                            }).then((result) => {
                                if (result.isConfirmed) {
                                    let pk = _this._findEventPkFromEl(opt.$trigger[0]);

                                    let formData = new FormData();
                                    formData.append("eventIds", String(pk));

                                    fetch('/arrangement/planner/delete_events/', {
                                        method: 'POST',
                                        body: formData,
                                        headers: {
                                            "X-CSRFToken": this.csrf_token,
                                        }
                                    }).then(_ => { 
                                        document.dispatchEvent(new Event("plannerCalendar.refreshNeeded")); // Tell the planner calendar that it needs to refresh the event set
                                    });
                                }
                            })
                        }
                    }
                }


                $.contextMenu({
                    className: "",
                    selector: ".fc-event",
                    items: items
                });
            }
        }
        else {
            // initialView = this._fcCalendar.view.type;
            this._fcCalendar.refetchEvents();
        }

        this._fcCalendar.render();
    }
}