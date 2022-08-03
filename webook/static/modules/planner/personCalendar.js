import { HeaderGenerator } from "./calendar_utilities/header_generator.js";
import { ArrangementStore, FullCalendarBased, PersonStore, StandardColorProvider, _FC_EVENT, _FC_RESOURCE } from "./commonLib.js";

export class PersonCalendar extends FullCalendarBased {

    constructor ( {calendarElement, initialColorProvider="", colorProviders=[], calendarFilter=undefined,  navigationHeaderWrapperElement = undefined } = {} ) {
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


        this._fcCalendar = undefined;
        this._calendarElement = calendarElement;
        
        this._headerGenerator = new HeaderGenerator();
        
        this._colorProviders = new Map();
        this._colorProviders.set("DEFAULT", new StandardColorProvider());

        colorProviders.forEach( (bundle) => {
            this._colorProviders.set(bundle.key, bundle.provider)
        });

        // If user has not supplied an active color provider key we use default color provider as active.
        // this.activeColorProvider = initialColorProvider !== undefined && this._colorProviders.has(initialColorProvider) ? initialColorProvider : this._colorProviders.get("DEFAULT");

        this.calendarFilter = calendarFilter;
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

    _bindPopover() {

    }

    async init() {
        let _this = this;

        if (this._fcCalendar === undefined) {
            this._fcCalendar = new FullCalendar.Calendar(_this._calendarElement, {
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
                eventRender: function (event, element, view) {
                    $(element).find(".fc-list-item-title").append("<div>" + event.resourceId + "</div>");
                },
                navLinks: true,
                locale: 'nb',
                eventSources: [
                    {
                        events: async (start, end, startStr, endStr, timezone) => {
                            return await _this._ARRANGEMENT_STORE._refreshStore(start, end)
                                .then(_ => this.calendarFilter.getFilteredSlugs().map( function (slug) { return { id: slug, name: "" } }))
                                .then(filterSet => _this._ARRANGEMENT_STORE.get_all(
                                    { 
                                        get_as: _FC_EVENT, 
                                        locations: undefined,
                                        arrangement_types: undefined,
                                        audience_types: undefined,
                                        filterSet: undefined
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