export default {
    props: {
        columns: Array,
        data: Array
    },
    computed: {
        columns() {
            return this.compendColumns();
        }
    },
    methods: {
        compendColumns() {
            if (!this.data.length)
                throw Error("Data must be set before columns can be compended.");
            
            let result = {};
            for (const property in data[0]) {
                result.push(property);
            }

            return result;
        }
    },
    mounted() {
        console.log("table.mounted", this)
    },
    /*html*/
    template: `
        <div class='table table-responsive'>
            <thead>
                <tr>
                    <th v-for="column in columns">{{ column }}</th>
                </tr>
            </thead>
            <tbody>
                <tr v-for="item in data">
                    <td v-for="prop in item">
                        {{prop}}
                    </td>
                </tr>
            </tbody>
        </div>
    `
}