

export class FilterDialog {
    constructor () {
    }

    openFilterDialog( ) {
        this._flush();
        this._injectDialog();
        this._spawnDialog();
    }

    _flush() {
        $("#filterDialog").remove();
    }

    _injectDialog() {
        $('body').append(this._fabricateDialog());
    }

    _spawnDialog() {
        $( "#filterTabs" ).tabs();
        $( "#filterDialog" ).dialog({  height: 400, width: 600});

        new mdb.Select(document.getElementById('arrangementTypeFilterSelect'), { filter: true });
        new mdb.Select(document.getElementById('audienceFilterSelect'), { filter: true });
        new mdb.Select(document.getElementById('plannersFilterSelect'), { filter: true });
        new mdb.Select(document.getElementById('locationsFilterSelect'), { filter: true });
        new mdb.Select(document.getElementById('peopleFilterSelect'), { filter: true });
    }

    _fabricateDialog() {
        return `
            <div id="filterDialog" title="Filtrering">
                <span class='text-muted small'>
                    Bare arrangementer med de angitte lokasjoner og personer vil vises.
                </span>

                <div class='form-group mb-2'>
                    <label>Arrangementstype</label>
                    <select id='arrangementTypeFilterSelect' class='select form-control' multiple>
                        <option value='0'>ARrangementstype</option>
                    </select>
                </div>

                <div class='form-group mb-2'>
                    <label>Audiens</label>
                    <select id='audienceFilterSelect' class='select form-control' multiple>
                        <option value='0'>Audiens</option>
                    </select>
                </div>

                <div class='form-group mb-2'>
                    <label>Planleggere</label>
                    <select id='plannersFilterSelect' class="select" multiple>
                        <option value='0'>Planlegger</option>
                    </select>
                </div>

                <div class='form-group mb-2'>
                    <label>Lokasjoner</label>
                    <select id='locationsFilterSelect' class="select" multiple>
                        <option value='0'>Planlegger</option>
                    </select>
                </div>

                <div class='form-group mb-2'>
                    <label>Personer</label>
                    <select id='peopleFilterSelect' class="select" multiple>
                        <option value='0'>Planlegger</option>
                    </select>
                </div>
            </div>
            `;
    }
}