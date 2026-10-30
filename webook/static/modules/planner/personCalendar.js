import { HeaderGenerator } from "./calendar_utilities/header_generator.js";
import { ArrangementStore, CalendarFilter, FullCalendarBased, PersonStore, StandardColorProvider, _FC_EVENT, _FC_RESOURCE, _NATIVE_ARRANGEMENT } from "./commonLib.js";

export class PersonCalendar extends FullCalendarBased {

    constructor ( {calendarElement, 
        initialColorProvider = "", 
        arrangementInspector,
        eventInspector,
        colorProviders=[],
        navigationHeaderWrapperElement = undefined,
        licenseKey=undefined,
        calendarFilter = undefined, } = {} ) {
        super(navigationHeaderWrapperElement);

        this.viewButtons = new Map([
            [
                1, {
                    "key": 1,
                    "title": "Måned",
                    "isParent": false,
                    "view": "resourceTimelineMonth",
                    "parent": undefined,
                    "weight": 100,
                }
            ],
            [
                2, {
                    "key": 2,
                    "title": "Uke",
                    "isParent": false,
                    "view": "resourceTimelineWeek",
                    "parent": undefined,
                    "weight": 200,
                }
            ]
        ])

        this._fcLicenseKey = licenseKey;
        this._fcCalendar = undefined;
        this._calendarElement = calendarElement;
        
        this._headerGenerator = new HeaderGenerator();

        this.arrangementInspector = arrangementInspector;
        this.eventInspector = eventInspector;
        
        this._colorProviders = new Map();
        this._colorProviders.set("DEFAULT", new StandardColorProvider());

        colorProviders.forEach( (bundle) => {
            this._colorProviders.set(bundle.key, bundle.provider)
        });

        this.filter = calendarFilter ?? new CalendarFilter( /* OnFilterUpdated: */ (filter) => this.init() );

        this._ARRANGEMENT_STORE = new ArrangementStore(this._colorProviders.get("arrangement"));
        this._STORE = new PersonStore(this);

        this.init()
    }

    getFcCalendar() {
        return this._fcCalendar;
    }

    refresh() {
        this.init()
    }

    _bindInspectorTrigger (elementToBindWith) {
        let _this = this;
        $(elementToBindWith).on('click', (ev) => {
            let pk = _this._findEventPkFromEl(ev.currentTarget);
            this.eventInspectorUtility.inspect(pk);
        })
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
            badgesHtml += `<span class="badge badge-secondary"><i class='fas fa-redo'></i></span>`;
        }
        else if (arrangement.evserie_id === null && arrangement.association_type === "degraded_from_serie") {
            badgesHtml += `
            <span class="badge badge-warning">
                <i class='fas fa-redo'></i> <i class='fas fa-times'></i>
            </span>`
        }
        else {
            badgesHtml += `
            <span class="badge badge-success">
                <i class='fas fa-calendar'></i>
            </span>`
        }

        new mdb.Popover(elementToBindWith, {
            trigger: "hover",
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

    async init() {
        let _this = this;

        if (this._fcCalendar === undefined) {
            this._fcCalendar = new FullCalendar.Calendar(_this._calendarElement, {
                schedulerLicenseKey: this._fcLicenseKey,
                headerToolbar: { left: '' , center: '', right: '' },
                initialView: 'resourceTimelineMonth',
                selectable: true,
                customButtons: {
                    filterButton: {
                        text: 'Filtrering',
                        click: () => {
                            this.filterDialog.openFilterDialog();
                        }
                    },
                },
                views: {
                    resourceTimelineMonth: {
                      type: 'resourceTimeline',
                      duration: { month: 1 }
                    }
                },
                eventDidMount: (arg) => {
                    this._bindPopover(arg.el);
                    this._bindInspectorTrigger(arg.el);

                    $.contextMenu({
                        className: "",
                        selector: "#peoplePlannerCalendar .fc-event",
                        items: {
                            arrangement_inspector: {
                                name: `<i class='fas fa-search'></i>&nbsp; ${window.WEBOOK_MESSAGES?.contextInspectArrangement || "Inspect arrangement"}`,
                                isHtmlName: true,
                                callback: (key, opt) => {
                                    let pk = parseInt(_this._findEventPkFromEl(opt.$trigger[0]));

                                    let arrangement = _this._ARRANGEMENT_STORE.get({
                                        pk: parseInt(pk),
                                        get_as: _NATIVE_ARRANGEMENT
                                    });
                            
                                    this.arrangementInspector.inspect(arrangement);
                                }
                            },
                            event_inspector: {
                                name: `<i class='fas fa-search'></i>&nbsp; ${window.WEBOOK_MESSAGES?.contextInspectTime || "Inspect time"}`,
                                isHtmlName: true,
                                callback: (key, opt) => {
                                    let pk = _this._findEventPkFromEl(opt.$trigger[0]);
                                    this.eventInspector.inspect(pk);
                                }
                            },
                            "section_sep_1": "---------",
                            delete_arrangement: {
                                name: `<i class='fas fa-trash'></i>&nbsp; ${window.WEBOOK_MESSAGES?.contextDeleteArrangement || "Delete arrangement"}`,
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
                            },
                            delete_event: {
                                name: `<i class='fas fa-trash'></i>&nbsp; ${window.WEBOOK_MESSAGES?.contextDeleteActivity || "Delete activity"}`,
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
                    });
                },
                eventRender: function (event, element, view) {
                    $(element).find(".fc-list-item-title").append("<div>" + event.resourceId + "</div>");
                },
                navLinks: false,
                locale: document.documentElement.lang || navigator.language || 'en',
                eventSources: [
                    {
                        events: async (start, end, startStr, endStr, timezone) => {
                            return await _this._ARRANGEMENT_STORE._refreshStore(start, end)
                                .then(_ => _this._ARRANGEMENT_STORE.get_all(
                                    { 
                                        get_as: _FC_EVENT, 
                                        locations: this.filter.locations,
                                        arrangement_types: this.filter.arrangementTypes,
                                        audience_types: this.filter.audiences,
                                        filterSet: this.filter.rooms,
                                    }
                                ));
                        },
                    }
                ],
                loading: function( isLoading ) {
                    if (isLoading === false) {
                        $(".popover").popover('hide');
                    }
                },
                datesSet: (dateInfo) => {
                    $('#plannerCalendarHeader').text("");
                    $(".popover").popover('hide');
    
                    $('#plannerCalendarHeader').text(this._headerGenerator.generate(
                        dateInfo.view.type,
                        dateInfo.start,
                    ));
                },
                resources: async (fetchInfo, successCallback, failureCallback) => {
                    await _this._STORE._refreshStore();
                    successCallback(_this._STORE.getAll({ get_as: _FC_RESOURCE }));
                },
            });
        }
        else {
            this._fcCalendar.refetchEvents();
        }

        this._fcCalendar.render();
    }
}