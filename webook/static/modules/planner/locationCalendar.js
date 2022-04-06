import { FullCalendarEvent, FullCalendarResource, FullCalendarBased, LocationStore, _FC_RESOURCE } from "./commonLib.js";


export class LocationCalendar extends FullCalendarBased {

    constructor ( {calendarElement } = {} ) {
        super();

        this._fcCalendar = undefined;
        this._calendarElement = calendarElement;
        
        this._LOCATIONS_STORE = new LocationStore(this);

        this.init()
    }

    refresh() {
        console.info("HIT REFRESH")
        this.init()
    }

    _bindPopover() {

    }

    init() {
        let _this = this;

        if (this._fcCalendar === undefined) {
            this._fcCalendar = new FullCalendar.Calendar(_this._calendarElement, {
                initialView: 'resourceTimelineMonth',
                headerToolbar: { left: 'arrangementsCalendarButton,locationsCalendarButton,peopleCalendarButton', center: 'resourceTimelineMonth,resourceTimelineWeek' },
                // themeSystem: 'bootstrap',
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
                    await _this._LOCATIONS_STORE._refreshStore();
                    successCallback(_this._LOCATIONS_STORE.getAll({ get_as: _FC_RESOURCE }));
                },
                resourceLabelContent: function (arg) {
                    var domNodes = [];

                    console.log(arg)

                    var name = document.createElement("span");
                    name.innerText = arg.resource.title;

                    if (arg.resource.extendedProps.resourceType === "location") {
                        name.classList.add("fw-bolder");
                    }
                    else {
                        
                        name.innerHTML = `${name.innerText} <abbr title="Maks kapasitet på dette rommet"><em class='small text-muted'>(${arg.resource.extendedProps.maxCapacity})</em></abbr>`;
                    }

                    domNodes.push(name);

                    if (arg.resource.extendedProps.resourceType === "location") {
                        var linkWrapper = document.createElement("span")
                        linkWrapper.innerHTML=`<a href='/arrangement/location/${arg.resource.id}' class='ms-3'><i class='fas fa-arrow-right'></i></a>`;
                        domNodes.push(linkWrapper);
                    }

                    return { domNodes: domNodes };
                }
            });
        }

        this._fcCalendar.render();
    }
}