export default {
    props: {
        availableServices: [],
    },
    data() {
        return {

        }
    },
    /*html*/
    template: `
        <div class="form-group">
            <label for="selectServices">Tjeneste(r)</label>
            <select class="select" id="selectServices" multiple>
                <option v-for="service in props.availableServices">
                    {{ service }}
                </option>
            </select>
        </div>

        <div class="form-group">
            <div class="accordion accordion-borderless" id="selectedServicesDetailAccordions">
                <div class="accordion-item" v-for="service in selectedServices">
                    <h2 class="accordion-header" :id="'heading-' + service.name">
                        {{ service.name }}
                    </h2>
                    <div class="accordion-collapse collapse show" :id="'body-' + service.name">
                        <label for="">Kommentar til koordinerende part:</label>
                        <textarea>
                        </textarea>
                    </div>
                </div>
            </div>
        </div>`
}
// const props = defineProps(["availableServices"])
// let selectedServices = [];

// const 