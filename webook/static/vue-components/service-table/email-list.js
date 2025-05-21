export default {
    props: {
        emails: Array,
        serviceId: Number,
        isDisabled: Boolean
    },
    data() {
        return {
            emailToAdd: "",
        }
    },
    methods: {
        addEmail() {
            if (!this.isDisabled)
                this.$emit("addEmail", this.serviceId, this.emailToAdd);
        },
        deleteEmail(emailToDelete) {
            if (!this.isDisabled)
                this.$emit("deleteEmail", this.serviceId, emailToDelete)
        }
    },
    mounted() {
    },
    template: `

    <table class='table'>
        <tbody>
            <tr>
                <td colspan="2">
                    <div class='input-group'>
                        <input
                            v-model="emailToAdd"
                            type="text"
                            class="form-control"
                            :disabled="isDisabled"
                            placeholder="epost@epost.no"
                            aria-label="Recipient's username"
                            aria-describedby="button-addon2"
                        />
                        <button class='btn wb-btn-main' @click="addEmail"><i class='fas fa-plus'></i></button>
                    </div>
                </td>
            </tr>

            <tr v-for="email in emails">
                <td>{{ email }}</td>
                <td> 
                    <button class='btn wb-btn-secondary' @click="deleteEmail( email )" v-if="isDisabled === false">Slett</button> 
                </td>
            </tr>
        </tbody>
    </table>
    `
}