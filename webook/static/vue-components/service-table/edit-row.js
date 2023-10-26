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
                <table>
                    <tbody>
                        <tr>
                            <td>
                                <input type='text' value='{{ service.name }}' />
                            </td>
                            <td>
                                <div class='btn-group'>
                                    <button class='btn btn-danger'>Slett</button>
                                    <button class='btn btn-success'>Rediger</button>
                                </div>
                            </td>
                        </tr>
                        <tr>
                            <emails-list :emails="service.emails"></emails-list>
                        </tr>
                    </tbody>
                </table>
            </td>
        </tr>
    `
}