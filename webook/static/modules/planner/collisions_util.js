import { serieConvert } from "./serieConvert.js";

export class CollisionState {
    constructor(collision) {
        this.collision = collision;
        this.solution = undefined;
    }
}

/**
 * Helper class to centralize handling of collisions, and back-end querying for collision data.
 */
export class CollisionsUtil {

    /**
     * Sanity checks the returned object and if it is a form error object throws an exception, as opposed
     * to allowing the flow to continue with the mismatch.
     * @param {*} responseObj 
     */
    static async _SanityCheckPostResponse(responseObj) {
        if ("success" in responseObj && responseObj.success == "false") {
            throw "Form data invalid. Object: ", responseObj;
        }
    }

    /**
     * Makes a search to the back-end to analyze the given serie, and identify any collisions that 
     * the serie might incur. 
     * @param {*} serie 
     * @param {*} csrf_token 
     * @returns array of collision records, if any. Alternatively if no collisions an empty array.
     */
    static async GetCollisionsForSerie(formData, csrf_token) {
        let responseObj = await fetch("/arrangement/analysis/analyzeNonExistentSerie", {
            method: 'POST',
            body: formData,
            headers: {
                "X-CSRFToken": csrf_token
            },
            credentials: 'same-origin'
        }).then(response => response.json());

        this._SanityCheckPostResponse(responseObj);

        return responseObj;
    }

    /**
     * Makes a search to the back-end to analyze the given event, and identify if it is in a collision state
     * with any other events, on possible contested resources.
     * @param {*} event 
     * @returns 
     */
    static async GetCollisionsForEvent(formData, csrf_token) {
        let responseObj = await fetch("/arrangement/analysis/analyzeNonExistentEvent", {
            method: 'POST',
            body: formData,
            headers: {
                "X-CSRFToken": csrf_token
            },
            credentials: 'same-origin'
        }).then(response => response.json());

        this._SanityCheckPostResponse(responseObj)

        return responseObj;
    }

    /**
     * Generates html for an unique row corresponding to a collision
     * @param {*} collision 
     * @param {*} uuid 
     * @param {*} name_of_event_to_trigger_on_resolve 
     * @returns 
     */
    static _GenerateCollisionSwalTableRowHtml(collision, uuid, name_of_event_to_trigger_on_resolve) {
        const generateNonResolvedBtnHtmlFunc = function (uuid) {
            return `
                <button class="btn btn-lg btn-success"
                    onclick='document.dispatchEvent(
                        new CustomEvent("${name_of_event_to_trigger_on_resolve}", { "detail": {
                            "collision_uuid": "${uuid}",
                        } })
                    )'> 
                    <i class='fas fa-code-branch'></i> Løs kollisjon 
                </button>
            `
        }

        const generateResolvedBtnHtmlFunc = function () {
            return `
                <div class='alert alert-success fw-bold text-center'>
                    Løst
                </div>
            `
        }

        return `
            <tr>
                <td>
                    <div>
                        ${ collision.is_resolved ? "<i class='fas fa-check text-success h4'></i>" : "<i class='fas fa-times text-danger h4'></i>" }
                    </div>
                </td>
                <td>
                    <div class='row'>
                        <div class='col-5 text-center'>
                            <div>
                                <strong class="h5">${collision.event_a_title}</strong> 
                                <div>(${collision.event_a_start} - ${collision.event_a_end})</div>
                            </div>
                        </div>
                        <div class='col-2'>
                            <div>
                                <h5 class="text-center">
                                    <i class='fas fa-exchange-alt ${ collision.is_resolved ? "text-success" : "text-danger"}'></i>
                                    <h6 class='text-muted text-center'>${collision.contested_resource_name}</h6>
                                </h5>
                            </div>
                        </div>
                        <div class='col-5 text-center'>
                            <strong class="h5">${collision.event_b_title}</strong> 
                            <div>(${collision.event_b_start} - ${collision.event_b_end})</div>
                        </div>
                    </div>
                </td>
                <td>
                    ${ collision.is_resolved ? generateResolvedBtnHtmlFunc() : generateNonResolvedBtnHtmlFunc(uuid) }
                </td>
            </tr>
        `
    }

    static async FireOneToOneCollisionWarningSwal(collision) {
        debugger;

        const generateTimeText = (date_a, date_b, to_locale) => {
            const _getComparableDate = (date) => {
                return date.getFullYear() + "_" + date.getMonth() + "_" + date.getDate()
            }

            let dateCompareText = null;

            const date_options = {
                year: "numeric",
                month: "2-digit",
                day: "2-digit",
            }
            const time_options = {
                hour: "2-digit",
                minute: "2-digit",
            }

            const isSameDay = _getComparableDate(date_a) === _getComparableDate(date_b);
            const locale = document.documentElement.lang || navigator.language || "en";
            if (isSameDay) {
                dateCompareText = `${date_a.toLocaleDateString(locale, date_options)} ${date_a.toLocaleTimeString(locale, time_options)}-${date_b.toLocaleTimeString(locale, time_options)}`;
            }
            else {
                dateCompareText = `${date_a.toLocaleDateString(locale, date_options)} ${date_a.toLocaleTimeString(locale, time_options)} - ${date_b.toLocaleDateString(locale, date_options)} ${date_b.toLocaleTimeString(locale, time_options)}`;
            }

            return dateCompareText;
        }

        const eventAStart   = new Date(collision.event_a_start);
        const eventAEnd     = new Date(collision.event_a_end);
        const eventBStart   = new Date(collision.event_b_start);
        const eventBEnd     = new Date(collision.event_b_end);

        let startTimeText   = generateTimeText(eventAStart, eventAEnd);
        let endTimeText     = generateTimeText(eventBStart, eventBEnd);

        return Swal.fire({
            title: 'Kollisjon',
            width: 600,
            html: 
            `
                Hendelsen kan ikke opprettes da den kolliderer med en eksisterende booking på den eksklusive ressursen ${collision.contested_resource_name}.
                <div class='row mt-3'>
                    <div class='col-5'>
                        <div class='card shadow-4 border'>
                            <div class='card-body'>
                                <span class='fw-bold'>${collision.event_a_title}</span>
                                <div class='small text-muted'>
                                    ${startTimeText}
                                </div>
                            </div>
                        </div>
                    </div>
                    <div class='col-2'>
                        <h2 class='align-middle'> <i class='fas fa-arrow-right'></i> </h2>
                    </div>
                    <div class='col-5'>
                        <div class='card shadow-4 border'>
                            <div class='card-body'>
                                <span class='fw-bold'>${collision.event_b_title}</span>
                                <div class='small text-muted'>
                                    ${endTimeText}
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            `,
            icon: 'error',
        });
    }

    /**
     * Fires a SWAL for collision resolution should the given serie be in a collision-state.
     * @param {*} serie 
     * @param {*} collision_resolution 
     * @param {*} csrf_token 
     * @param {*} name_of_event_to_trigger_on_resolve
     */
    static async FireCollisionsSwal(serie, 
                             collision_resolution, 
                             csrf_token,
                             name_of_event_to_trigger_on_resolve,
                             arrangement_pk,
                             on_confirmed,
                             after_on_confirmed_is_done,) {
        let collisions = [];
        let is_reading_from_resolution_map = false;

        if (collision_resolution.size > 0) {
            collisions = Array.from(collision_resolution.entries());
            is_reading_from_resolution_map = true;
        }
        else {
            collisions = await this.GetCollisionsForSerie(serieConvert(serie, new FormData(), ""), csrf_token);
        }

        /*
            We can be operating in two states;
                1. A resolution is in progress, and the SWAL is re-fired after something else has happened
                2. It is the first time fire of the SWAL, and we are setting up the map for the first time
            In case 1 we need to render the SWAL based on the state of the records in the map, and in case 2 
            we need to set up the map.
        */

        if (collisions.length == 0) {
            return false;
        }

        let trHtml = "";

        console.log("collisions", collisions);

        collisions.forEach(function (collision) {
            let uuid = "";
            let collision_record = undefined;

            if (is_reading_from_resolution_map) {
                uuid = collision[0];
                collision_record = collision[1].collision;
            }
            else {
                uuid = crypto.randomUUID();
                collision_record = collision;
                collision_resolution.set(uuid, new CollisionState(collision_record));
            }

            trHtml += this._GenerateCollisionSwalTableRowHtml(collision_record, uuid, name_of_event_to_trigger_on_resolve);
        }, this);

        Swal.fire({
            title: "Kollisjoner",
            width: 1500,
            showCancelButton: true,
            showDenyButton: true,
            denyButtonText: "Fjern bestridte ressurser og lagre",
            confirmButtonText: "<i class='fas fa-save'></i>&nbsp; Lagre med gjeldende resolusjoner",
            cancelButtonText: "<i class='fas fa-times'></i>&nbsp; Avbryt",
            html: 
            `
                <div class="alert alert-danger text-start">
                    <div class='mb-2'>Den gitte forandringen vil medføre kollisjoner på eksklusive ressurser.</div>

                    <p>Du kan velge å;</p>
                    <ul>
                        <li>Løse kollisjonene</li>
                        <li>Fjerne rommene som kolliderer</li>
                        <li>Lagre uansett</li>
                    </ul>
                    <div>
                        Om du velger å løse kollisjonene så kan du endre rom for hver individuelle kollisjon her, eller 
                        trykke på <strong>avbryt</strong> og gå tilbake til redigering av serie, for så og endre rom for hele serien.
                        Hvis du da endrer rom individuelt her så vil de andre hendelsene som ikke er i kollisjon benytte seg 
                        av det originale valget.
                    </div>
                    <div>
                        Alternativt kan du også velge å fjerne de rommene som er i kollisjon. Da vil disse rommene fjernes hvor de er i tvist, noe
                        som tillater aktiviteten å bli opprettet as-is uten den bestridte ressursen.
                    </div>
                    <div>
                        Du kan også lagre uansett, men da vil de hendelsene som er i kollisjon på en eller flere eksklusive ressurser
                        bli ignorert og dermed ikke opprettet.
                    </div>
                </div>

                <div class="table-responsive">
                    <table class="table table-borderless table-sm">
                        <thead>
                            <tr>
                                <th></th>
                                <th></th>
                                <th></th>
                            </tr>
                        </thead>
                        <tbody>
                            ${trHtml}
                        </tbody>
                    </table>
                </div>
            `,
            icon: 'error',
        }).then(result => {
            if (result.isConfirmed) {
                on_confirmed(
                    serie,
                    csrf_token,
                    arrangement_pk,
                    collision_resolution,
                    0
                )
            }
            if (result.isDenied) {
                on_confirmed(
                    serie,
                    csrf_token,
                    arrangement_pk,
                    collision_resolution,
                    1,
                )
            }
        }).then(_ => after_on_confirmed_is_done() );
        
        return true;
    }
}