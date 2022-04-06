import { FullCalendarEvent, FullCalendarResource, FullCalendarBased, LocationStore, _FC_RESOURCE, PersonStore } from "./commonLib.js";


export class PersonCalendar extends FullCalendarBased {

    constructor ( {calendarElement } = {} ) {
        super();

        this._fcCalendar = undefined;
        this._calendarElement = calendarElement;
        
        this._STORE = new PersonStore(this);

        this.init()
    }

    refresh() {
        this.init()
    }

    _bindPopover() {

    }

    init() {
        let _this = this;

        if (this._fcCalendar === undefined) {
            this._fcCalendar = new FullCalendar.Calendar(_this._calendarElement, {
                headerToolbar: { left: 'arrangementsCalendarButton,locationsCalendarButton,peopleCalendarButton' , center: 'resourceTimelineMonth,resourceTimelineWeek' },
                initialView: 'resourceTimelineMonth',
                selectable: true,
                customButtons: {
                    filterButton: {
                        text: 'Filtrering',
                        click: () => {
                            this.filterDialog.openFilterDialog();
                        }
                    },
                    arrangementsCalendarButton: {
                        text: 'Arrangementer',
                        click: () => {
                            $('#overview-tab').trigger('click');
                        }
                    },
                    locationsCalendarButton: {
                        text: 'Lokasjoner',
                        click: () => {
                            $('#locations-tab').trigger('click');
                        }
                    },
                    peopleCalendarButton: {
                        text: 'Personer',
                        click: () => {
                            $('#people-tab').trigger('click');
                        }
                    }
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
                events: [ { title: "Test Arrangement", start: "2022-03-01", end: "2022-03-30", resourceId: 'lokasjon-3'  } ],
                resources: async (fetchInfo, successCallback, failureCallback) => {
                    await _this._STORE._refreshStore();
                    successCallback(_this._STORE.getAll({ get_as: _FC_RESOURCE }));
                },
            });
        }

        this._fcCalendar.render();
    }
}