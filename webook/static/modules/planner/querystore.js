import { convertObjToFormData, getClientTimezone } from "./commonLib.js";
import { serieConvert } from "./serieConvert.js";


const COMMA_SEPARATED_LIST_SPLITS = ["rooms", "people", "display_layouts"];

/**
 * A store of common queries
 */
export class QueryStore {
    /**
     * Save a serie
     * @param {*} serie the serie which we are to save
     * @param {*} csrf_token 
     */
    static async SaveSerie(serie, csrf_token, arrangement_pk = 0) {
        var formData = serieConvert(serie, new FormData(), "");
        formData.append("timezone", getClientTimezone());
        formData.append("arrangementPk", arrangement_pk);
        if ("event_serie_pk" in serie) {
            formData.append("predecessorSerie", serie.event_serie_pk);
        }

        const responseData = await fetch('/arrangement/event/create_serie', {
            method: 'POST',
            body: formData,
            headers: {
                "X-CSRFToken": csrf_token
            },
            credentials: 'same-origin',
        }).then(response => {
            if (!response.ok) {
                toastr.error("Opprettelse av serie feilet. Serveren svarte med feilkode " + response.status);
                throw new Error("Failed creating serie", response);
            }

            return response.json();
        });

        if (responseData.success === false) {
            toastr.error("Opprettelse av serie feilet.");
            throw new Error("Failed creating serie", responseData);
        }

        if ("ordered_services" in serie) {
            serie.ordered_services.filter(x => x.service_order === null).forEach(async (serviceOrder) => {
                console.log("create serie ordered_services", serviceOrder);
                let formData = new FormData();
                if (serviceOrder.applied_preconfiguration)
                    formData.append("applied_preconfiguration", serviceOrder.applied_preconfiguration);
                formData.append("parent_type", "serie");
                formData.append("parent_id", responseData.serie_id);
                formData.append("service_id", serviceOrder.service_id);
                formData.append("freetext_comment", serviceOrder.freetext_comment);
                if (serviceOrder.service_order)
                    formData.append("service_order", serviceOrder.service_order);

                const orderServiceResponse = await fetch('/arrangement/planner/dialogs/order_service/serie/' + responseData.serie_id, {
                    method: 'POST',
                    body: formData,
                    headers: {
                        "X-CSRFToken": csrf_token
                    },
                });

                if (orderServiceResponse.success === false)
                    throw new Error("Failed creating service order", orderServiceResponse);
            });
        }

        return response;
    }

    /**
     * Save an array of events
     * @param {*} events 
     * @param {*} csrf_token 
     * @param {*} preset_formdata Pass a custom FormData instance in to inject values, or let be undefined for standard
     * @returns {*} promise
     */
    static async SaveEvents(events, csrf_token) {
        for (const event of events) {
            const formData = convertObjToFormData(event, true);

            const response = await fetch("/arrangement/event/create", {
                method: "POST",
                body: formData,
                headers: {
                    "X-CSRFToken": csrf_token
                },
                credentials: 'same-origin',
            }).then(response => {
                if (!response.ok) {
                    toastr.error("Opprettelse av aktivitet feilet. Serveren svarte med feilkode " + response.status);
                    throw new Error("Failed creating event", response);
                }

                return response.json();
            });

            if (response.success === false) {
                toastr.error("Opprettelse av aktivitet feilet.");
                throw new Error("Failed creating event", response);
            }

            if ("ordered_services" in event) {
                event.ordered_services.forEach(async (serviceOrder) => {
                    let formData = new FormData();
                    if (serviceOrder.applied_preconfiguration)
                        formData.append("applied_preconfiguration", serviceOrder.applied_preconfiguration);
                    formData.append("parent_type", "event");
                    formData.append("parent_id", response.event_id);
                    formData.append("service_id", serviceOrder.service_id);
                    formData.append("freetext_comment", serviceOrder.freetext_comment);

                    const orderServiceResponse = await fetch('/arrangement/planner/dialogs/order_service/event/' + response.event_id, {
                        method: 'POST',
                        body: formData,
                        headers: {
                            "X-CSRFToken": csrf_token
                        },
                    });

                    if (orderServiceResponse.success === false)
                        throw new Error("Failed creating service order", orderServiceResponse);
                });
            }
        }
    }


    static async UpdateEvents (events, csrf_token) {
        let responses = [];
        for (const formData of events.map((event) => convertObjToFormData(event, true))) {
            let response = await fetch("/arrangement/planner/update_event/" + formData.get("id"), {
                method: "POST",
                body: formData,
                headers: {
                    "X-CSRFToken": csrf_token
                },
                credentials: 'same-origin',
            })
            responses.push(await response.json())
        }
        return responses;
    }


    /**
     * Get the serie manifest for a given serie identified by serie_pk
     * @param {*} serie_pk 
     * @returns 
     */
    static async GetSerieManifest(serie_pk) {
        return await fetch(`/arrangement/eventSerie/${serie_pk}/manifest`, {
            method: "GET"
        }).then(response => response.json());
    }
}