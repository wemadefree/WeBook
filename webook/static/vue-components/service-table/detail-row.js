import EmailList from "./email-list.js";

export default {
    components: {
        EmailList
    },
    props: {
        service: Object,
    },
    data() {
        return {}
    },
    computed: {},
    template: `
        <tr>
        <td>
            <table class='table'>
                <tbody>
                    <tr class='h3'>
                        <td>
                            <i class='fas fa-arrow-down'></i>
                            <span class='badge badge-info me-2 ms-3'>
                                0
                            </span>
                            {{ service.name }}
                        </td>
                        <td>
                            <div class='btn-group shadow-0'>
                                <button class='btn wb-btn-secondary'>Slett</button>
                                <button class='btn wb-btn-main'>Rediger</button>
                            </div>
                        </td>
                    </tr>
                    <tr>
                        <td>
                            <email-list :emails="service.emails"></email-list>
                        </td>
                    </tr>
                </tbody>
            </table>
        </td>
        </tr>
    `
}