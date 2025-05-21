import EmailList from "./service-table/email-list.js";


export default {
    components: {
        EmailList
    },
    props: {
        services: Array,
    },
    data() {
        return {
            expandedMap: new Map(),
            page: 1,
            pageSize: 10,
        }
    },
    computed: {
        totalPages() {
            return Math.ceil(this.services.length / this.pageSize)
        },
        visibleServices() {
            return this.services.slice((this.page - 1) * this.pageSize, this.page * this.pageSize );
        }
    },
    watch: {
        services() {
            /** When user is searching we need to reset to page 1, otherwise we could be showing page current, which may
             * not contain anything, thereby soft-locking navigation (pages not visible, but back will work) (if not enough results
             * to populate current page)
             */
            this.page = 1;
        }
    },
    methods: {
        triggerAddEmailDialog(id) {
            this.$emit("triggerAddEmailDialog", id);
        },
        triggerAddPersonDialog(id) {
            this.$emit("addPerson", id);
        },
        toggleExpansion(id) {
            this.expandedMap.has(id)
                    ? this.expandedMap.set(id, !this.expandedMap.get(id)) : this.expandedMap.set(id, true);
        },
        isExpanded(id) {
            return !!this.expandedMap.get(id);
        },
        goToDashboard(serviceId) {
            location.href = "/arrangement/service/view/" + serviceId;
        },
        saveEmail(serviceId, email) {
            this.$emit("saveEmail", serviceId, email);
        },
        deleteEmail(serviceId, email) {
            this.$emit("deleteEmail", serviceId, email);
        },
        deactivateService(serviceId) {
            this.$emit("deactivateService", serviceId);
        },
        activateService(serviceId) {
            this.$emit("activateService", serviceId);
        },
        editService(serviceId) {
            this.$emit("editService", serviceId);
        },
        createServiceConfiguration(serviceId) {
            this.$emit("createServiceConfiguration", serviceId);
        }
    },
    beforeUpdated() {
        this.services.forEach((service) => {
            var calendarEl = document.getElementById(service.id + '_calendar');
            var calendar = new FullCalendar.Calendar(calendarEl, {
                initialView: 'dayGridMonth'
            });
            calendar.render();
        })
    },
    async mounted() {

    },
    /*html*/
    template: `
        <table class='table'>
            <tbody>
                <tr v-for="service in visibleServices">
                    <td class='h5'>
                        <span class="fa-stack fa-sm" @click="toggleExpansion(service.id)">
                            <i class="fa fa-circle fa-stack-2x"></i>
                            <i class="fa fa-arrow-down fa-stack-1x fa-inverse" v-if="isExpanded(service.id) === false"></i>
                            <i class="fa fa-arrow-up fa-stack-1x fa-inverse" v-else></i>
                        </span> 

                        <span class='badge badge-danger ms-2 me-2' v-if="service.isArchived === true">Deaktivert</span>

                        <span class='badge badge-info ms-2 me-2'>{{ service.emails.length }}</span>

                        {{ service.name }}

                        <div class="clearfix float-end">
                            <button class='btn wb-btn-secondary' @click="deactivateService(service.id)" v-if="service.isArchived === false">Deaktiver</button>
                            <button class='btn wb-btn-secondary' @click="activateService(service.id)" v-else>Aktiver</button>

                            <button class="btn wb-btn-main ms-1 me-1" @click="goToDashboard(service.id)">Gå til dashboard</button>
                            <button class='btn wb-btn-main' @click="editService(service.id)">Endre navn</button>
                        </div>
                        <div class='p-5 pt-3 pb-3 wb-bg-secondary rounded-3 shadow-3 mt-2' v-if="isExpanded(service.id)">
                            <div class="row">
                                <div class="col-6 p-3 border-end">
                                    <div class="d-flex" style="justify-content: space-between">
                                        <h3>Ressurser</h3>
                                        <button class="btn wb-btn-main mt-2" @click="triggerAddPersonDialog(service.id)">Administrer ressurser</button>
                                    </div>
                                    
                                    <ul>
                                        <li v-for="resource in service.resources">
                                            {{ resource }}
                                        </li>
                                    </ul>
                                </div>
                                <div class="col-6 p-3">
                                    <h3>Koordinasjon</h3>
                                    <email-list 
                                        :emails="service.emails" 
                                        :service-id="service.id"
                                        :is-disabled="service.isArchived"
                                        @add-email="saveEmail"
                                        @delete-email="deleteEmail">
                                    </email-list>
                                </div>
                            </div>
                        </div>
                    </td>
                </tr>
            </tbody>
        </table>

        <nav aria-label="Table pagination or navigation" class="clearfix">
            <ul class="pagination float-end">
                <li class="page-item" :class="{ disabled: page == 1 }"><a class="page-link" href="javascript:void(0)" @click.stop="page--">Forrige</a></li>
                <li class="page-item" :class="{ active: thisPage == page }" v-for="thisPage in totalPages"><a class="page-link" href="#">{{thisPage}}</a></li>
                <li class="page-item" :class="{ disabled: page == totalPages }"><a class="page-link" href="javascript:void(0)" @click.stop="page++">Neste</a></li>
            </ul>
        </nav>
    `
}