
export function PopulateCreateSerieDialogFromSerie(serie, $dialogElement, dialogId, discriminator) {
    if (serie === undefined) {
        console.error("Serie is undefined", serie);
        debugger;
    }

    [
        { target: '#countySelect', value: serie.time.county },
        { target: '#initialSchoolValue', value: serie.time.school },
        { target: '#serie_uuid', value: serie._uuid },
        { target: '#serie_title', value: serie.time.title },
        { target: '#serie_title_en', value: serie.time.title_en },
        { target: '#serie_start', value: serie.time.start },
        { target: '#serie_end', value: serie.time.end },
        { target: '#serie_ticket_code', value: serie.time.ticket_code },
        { target: '#serie_expected_visitors', value: serie.time.expected_visitors },
        { target: '#area_start_date', value: serie.time_area.start_date },
        { target: '#buffer_before_title', value: serie.buffer.before?.title },
        { target: '#buffer_before_date_offset', value: serie.buffer.before?.date_offset },
        { target: '#buffer_before_start', value: serie.buffer.before?.start },
        { target: '#buffer_before_end', value: serie.buffer.before?.end },
        { target: '#buffer_after_title', value: serie.buffer.after?.title },
        { target: '#buffer_after_date_offset', value: serie.buffer.after?.date_offset },
        { target: '#buffer_after_start', value: serie.buffer.after?.start },
        { target: '#buffer_after_end', value: serie.buffer.after?.end },
        { target: '#_statusTypeId', value: serie.time.status },
        { target: '#_backingArrangementTypeId', value: serie.time.arrangement_type },
        { target: '#_backingAudienceId', value: serie.time.audience },
        { target: '#id_meeting_place', value: serie.time.meeting_place },
        { target: '#id_meeting_place_en', value: serie.time.meeting_place_en },
        { target: '#id_display_text', value: serie.time.display_text },
        { target: '#id_display_text_en', value: serie.time.display_text_en },
    ].forEach( (mapping) => {
        $dialogElement.find( mapping.target ).val( mapping.value );
        window.MessagesFacility.send(dialogId, mapping.value, evName);
    } );

    console.log("serie", serie);

    if (serie.planner_payload) {
        window.MessagesFacility.send(dialogId, serie.planner_payload, "setPlanner");
    }
    if (serie.room_payload) {
        window.MessagesFacility.send(dialogId, serie.room_payload, "roomsSelected");
    }
    if (serie.people_payload) {
        window.MessagesFacility.send(dialogId, serie.people_payload, "peopleSelected");
    }

    serie.display_layouts.split(",").forEach(element => {
        $dialogElement.find('#id_display_layouts_serie_planner_' + element).prop( "checked", true );
    });

    switch(serie.time_area.method_name) {
        case "StopWithin":
            $dialogElement.find('#radio_timeAreaMethod_stopWithin').prop("checked", true);
            $dialogElement.find('#area_stopWithin').val(serie.time_area.stop_within);
            $dialogElement.find('#area_stopWithin')[0].disabled = false;
            break;
        case "StopAfterXInstances":
            $dialogElement.find('#radio_timeAreaMethod_stopAfterXInstances').prop("checked", true);
            $dialogElement.find('#area_stopAfterXInstances').val(serie.time_area.instances);
            $dialogElement.find('#area_stopAfterXInstances')[0].disabled = false;
            break;
        case "NoStopDate":
            $dialogElement.find('#radio_timeAreaMethod_noStopDate').prop("checked", true);
            $dialogElement.find('#area_noStop_projectXMonths').val(serie.time_area.projectionDistanceInMonths);
            $dialogElement.find('#area_noStop_projectXMonths')[0].disabled = false;
            break;
    }

    switch(serie.pattern.pattern_type) {
        case "daily":
            $dialogElement.find('#radio_pattern_daily').prop("checked", true);
            switch(serie.pattern.pattern_routine) {
                case "daily__every_x_day":
                    $dialogElement.find('#radio_pattern_daily_every_x_day_subroute').prop("checked", true);
                    $dialogElement.find('#every_x_day__interval').val(parseInt(serie.pattern.interval));
                    break;
                case "daily__every_weekday":
                    $dialogElement.find('#radio_pattern_daily_every_weekday_subroute').prop("checked", true);
                    break;
            }
            break;
        case "weekly":
            $dialogElement.find('#radio_pattern_weekly').prop("checked", true);
            $dialogElement.find("#week_interval").val(serie.pattern.week_interval);

            const days = [
                $dialogElement.find("#monday"),
                $dialogElement.find("#tuesday"),
                $dialogElement.find("#wednesday"),
                $dialogElement.find("#thursday"),
                $dialogElement.find("#friday"),
                $dialogElement.find("#saturday"),
                $dialogElement.find("#sunday"),
            ]

            for (let i = 1; i < 8; i++) {
                if (serie.pattern.days.get(i) === true) {
                    days[i - 1].attr("checked", true);
                }
            }
            break;
        case "monthly":
            $dialogElement.find('#radio_pattern_monthly').prop("checked", true).click();

            switch(serie.pattern.pattern_routine) {
                case "month__every_x_day_every_y_month":
                    $dialogElement.find('#every_x_day_every_y_month__day_of_month_radio').prop("checked", true);
                    $dialogElement.find('#every_x_day_every_y_month__day_of_month').val(serie.pattern.day_of_month);
                    $dialogElement.find('#every_x_day_every_y_month__month_interval').val(serie.pattern.interval);
                    break;
                case "month__every_arbitrary_date_of_month":
                    $dialogElement.find('#every_x_day_every_y_month__month_interval_radio').prop("checked", true);
                    $dialogElement.find("#every_dynamic_date_of_month__arbitrator").attr("init_value", serie.pattern.arbitrator);
                    $dialogElement.find("#every_dynamic_date_of_month__weekday").attr("init_value", serie.pattern.weekday);
                    $dialogElement.find("#every_dynamic_date_of_month__month_interval").val(serie.pattern.interval);
                    break;
            }

            break;
        case "yearly":
            $dialogElement.find('#radio_pattern_yearly').prop("checked", true);
            $dialogElement.find('#pattern_yearly_const__year_interval').val(serie.pattern.year_interval);

            switch(serie.pattern.pattern_routine) {
                case "yearly__every_x_of_month":
                    $dialogElement.find('#every_x_datemonth_of_year_radio').prop("checked", true);
                    $dialogElement.find('#every_x_of_month__date').val(serie.pattern.day_index);
                    $dialogElement.find("#every_x_of_month__month").attr("init_value", serie.pattern.month);
                    break;
                case "yearly__every_arbitrary_weekday_in_month":
                    $dialogElement.find('#every_x_dynamic_day_in_month_radio').prop("checked", true);
                    $dialogElement.find("#every_arbitrary_weekday_in_month__arbitrator").attr("init_value", serie.pattern.arbitrator);
                    $dialogElement.find("#every_arbitrary_weekday_in_month__weekday").attr("init_value", serie.pattern.weekday);
                    $dialogElement.find("#every_arbitrary_weekday_in_month__month").attr("init_value", serie.pattern.month);
                    $dialogElement("#every_arbitrary_weekday_in_month__month").val(serie.pattern.month);
                    break;
            }

            break;
    }

    // This is a bad solution to a pesky bug where the "daily" strategy choices appear when selecting
    // weekly/monthly/yearly. Should be fixed on createSerieDialog when time allows.
    if (serie.pattern.pattern_type !== "daily") {
        $dialogElement.find('#patternRoute_daily').hide();
    }
}

/**
 *
 * @param {*} manifest
 */
export function PopulateCreateSerieDialogFromManifest(manifest, serie_uuid, $dialogElement, dialogId) {
    [
        { to: "#serie_uuid", value: serie_uuid },
        { to: "#serie_title", value: manifest.title },
        { to: "#serie_title_en", value: manifest.title_en },
        { to: "#serie_expected_visitors", value: manifest.expected_visitors },
        { to: "#serie_start", value: manifest.start_time },
        { to: "#serie_end", value: manifest.end_time },
        { to: "#serie_ticket_code", value: manifest.ticket_code },
        { to: "#area_start_date", value: manifest.start_date },
        { to: "#id_meeting_place", value: manifest.meeting_place },
        { to: "#id_meeting_place_en", value: manifest.meeting_place_en },
        { to: '#_statusTypeId', value: manifest.status },
        { to: '#id_display_text', value: manifest.display_text },
        { to: '#id_display_text_en', value: manifest.display_text_en },
        { to: '#buffer_before_title', value: manifest.before_buffer_title },
        { to: '#buffer_before_date_offset', value: manifest.before_buffer_date_offset },
        { to: '#buffer_before_start', value: manifest.before_buffer_start },
        { to: '#buffer_before_end', value: manifest.before_buffer_end },
        { to: '#buffer_after_title', value: manifest.after_buffer_title },
        { to: '#buffer_after_date_offset', value: manifest.after_buffer_date_offset },
        { to: '#buffer_after_start', value: manifest.after_buffer_start },
        { to: '#buffer_after_end', value: manifest.after_buffer_end },
        { to: "#countySelect", value: manifest.county },
        { to: "#initialSchoolValue", value: manifest.school },
    ].forEach( (mapping) => { 
        $dialogElement.find(mapping.to).val(mapping.value ).trigger('change'); 
        const evName = "set_" + mapping.to.replace("#", "");
        window.MessagesFacility.send(dialogId, mapping.value, evName);
    } );

    console.log("PopulateCreateSerieDialogFromManifest", manifest);

    window.MessagesFacility.send(dialogId, manifest.audience, "setAudienceFromParent");
    window.MessagesFacility.send(dialogId, manifest.county, "setCountyFromParent");
    window.MessagesFacility.send(dialogId, manifest.school, "setSchoolFromParent");
    window.MessagesFacility.send(dialogId, manifest.arrangement_type, "setArrangementTypeFromParent");
    window.MessagesFacility.send(dialogId, manifest.status, "setStatusFromParent");

    if (manifest.rooms) {
        manifest.rooms.allPresets = new Map([
            Object.entries(manifest.rooms.allPresets).map(x => [ x, manifest.rooms.allPresets[x]] )
        ]);

        window.MessagesFacility.send(dialogId, manifest.rooms, "roomsSelected");
    }
    if (manifest.people) {
        window.MessagesFacility.send(dialogId, manifest.people, "peopleSelected");
    }
    if (manifest.responsible)
        window.MessagesFacility.send(dialogId, manifest.responsible, "setPlanner");
    
    manifest.display_layouts.forEach(display_layout => {
        $dialogElement.find('#id_display_layouts_serie_planner_' + display_layout.id).prop( "checked", true );
    })

    switch(manifest.recurrence_strategy) {
        case "StopWithin":
            $dialogElement.find('#radio_timeAreaMethod_stopWithin').prop("checked", true).click();
            $dialogElement.find('#area_stopWithin').val(manifest.stop_within);
            $dialogElement.find('#area_stopWithin').removeAttr("disabled");
            break;
        case "StopAfterXInstances":
            $dialogElement.find('#radio_timeAreaMethod_stopAfterXInstances').prop("checked", true).click();
            $dialogElement.find('#area_stopAfterXInstances').val(manifest.stop_after_x_occurences);
            $dialogElement.find('#area_stopAfterXInstances').removeAttr("disabled");
            break;
        case "NoStopDate":
            $dialogElement.find('#radio_timeAreaMethod_noStopDate').prop("checked", true).click();
            $dialogElement.find('#area_noStop_projectXMonths').val(manifest.project_x_months_into_future);
            $dialogElement.find('#area_noStop_projectXMonths').removeAttr("disabled");
            break;
    }

    switch (manifest.pattern) {
        case "daily":
            $dialogElement.find('#radio_pattern_daily').prop("checked", true).click();

            switch(manifest.pattern_strategy) {
                case "daily__every_x_day":
                    $dialogElement.find('#radio_pattern_daily_every_x_day_subroute').prop("checked", true);
                    $dialogElement.find('#every_x_day__interval').val(parseInt(manifest.strategy_specific.interval));
                    $dialogElement.find('#every_x_day__interval').removeAttr("disabled");
                    break;
                case "daily__every_weekday":
                    $dialogElement.find('#radio_pattern_daily_every_weekday_subroute').prop("checked", true);
                    break;
            }
            break;
        case "weekly":
            $dialogElement.find('#radio_pattern_weekly').prop("checked", true).click();
            $dialogElement.find("#week_interval").val(parseInt(manifest.strategy_specific.interval));

            const days = [
                $dialogElement.find("#monday"),
                $dialogElement.find("#tuesday"),
                $dialogElement.find("#wednesday"),
                $dialogElement.find("#thursday"),
                $dialogElement.find("#friday"),
                $dialogElement.find("#saturday"),
                $dialogElement.find("#sunday"),
            ]

            for (let i = 0; i < manifest.strategy_specific.days.length; i++) {
                if (manifest.strategy_specific.days[i] == true) {
                    days[i].attr("checked", true);
                }
            }

            break;
        case "monthly":
            $dialogElement.find('#radio_pattern_monthly').prop("checked", true).click();
            switch(manifest.pattern_strategy) {
                case "month__every_x_day_every_y_month":
                    $dialogElement.find('#every_x_day_every_y_month__day_of_month_radio').prop("checked", true);
                    $dialogElement.find('#every_x_day_every_y_month__day_of_month').val(manifest.strategy_specific.day_of_month);
                    $dialogElement.find("#every_x_day_every_y_month__month_interval").val(parseInt(manifest.strategy_specific.interval));
                    break;
                case "month__every_arbitrary_date_of_month":
                    $dialogElement.find('#every_x_day_every_y_month__month_interval_radio').prop("checked", true);
                    $dialogElement.find('#every_dynamic_date_of_month__arbitrator').val(manifest.strategy_specific.arbitrator);
                    $dialogElement.find('#every_dynamic_date_of_month__weekday').val(manifest.strategy_specific.day_of_week);
                    $dialogElement.find('#every_dynamic_date_of_month__month_interval').val(manifest.strategy_specific.interval);
                    break;
            }
            break;
        case "yearly":
            $dialogElement.find('#radio_pattern_yearly').prop("checked", true).click();
            $dialogElement.find('#pattern_yearly_const__year_interval').val(manifest.strategy_specific.interval);
            switch(manifest.pattern_strategy) {
                case "yearly__every_x_of_month":
                    $dialogElement.find('#every_x_datemonth_of_year_radio').prop("checked", true);
                    $dialogElement.find('#every_x_of_month__date').val(manifest.strategy_specific.day_of_month);
                    $dialogElement.find('#every_x_of_month__month').val(manifest.strategy_specific.month);
                    break;
                case "yearly__every_arbitrary_weekday_in_month":
                    $dialogElement.find('#every_x_dynamic_day_in_month_radio').prop("checked", true);
                    $dialogElement.find('#every_arbitrary_weekday_in_month__arbitrator').val(manifest.strategy_specific.arbitrator);
                    $dialogElement.find('#every_arbitrary_weekday_in_month__weekday').val(manifest.strategy_specific.day_of_week);
                    $dialogElement.find('#every_arbitrary_weekday_in_month__month').val(manifest.strategy_specific.month);
                    break;
            }

            break;
    }

    if (manifest.pattern !== "daily") {
        $dialogElement.find('#patternRoute_daily').hide();
    }
}

/**
 * Populate a Create Event dialog based on a collision resolution and a serie
 * This is then the "break-out" dialogs that are used when one is resolving a collision, so the dataset differs to some degree
 * from the normal from-activity or from-in-mem-activity states normally encountered.
 * @param {*} event 
 * @param {*} $dialogElement 
 * @param {*} dialogId 
 * @param {*} collisionResolution 
 * @param {*} serie 
 */
export function PopulateCreateEventDialogFromCollisionResolution($dialogElement, dialogId, collisionRecord, serie) {
    serie.display_layouts.split(",")
        .forEach(checkboxElement => {
            $dialogElement.find(`#${checkboxElement.value}_dlcheck`)
                .prop( "checked", true );
        });

    let parseDateOrStringToArtifacts = function (dateOrString) {
        if (dateOrString instanceof String || typeof(dateOrString) === "string")
            return Utils.splitStrDate(dateOrString);
        else if (dateOrString instanceof Date)
            return Utils.splitDateIntoDateAndTimeStrings(dateOrString);
        else throw "Invalid value or type"
    }

    let [ fromDate, fromTime ]  = parseDateOrStringToArtifacts(collisionRecord.event_a_start);
    let [ toDate, toTime ]      = parseDateOrStringToArtifacts(collisionRecord.event_a_end);

    [
        { target: '#title_before_collision_resolution', value: serie.time.title },
        { target: "#start_before_collision_resolution", value: collisionRecord.event_a_start },
        { target: "#end_before_collision_resolution", value: collisionRecord.event_a_end },
        { target: "#_serie_reference", value: serie._uuid },
        { target: "#_serie_position_hash", value: collisionRecord.my_serie_position_hash },
        { target: "#_parent_serie_position_hash", value: collisionRecord.parent_serie_position_hash },
        { target: "#ticket_code", value: serie.time.ticket_code },
        { target: "#title", value: collisionRecord.event_a_title },
        { target: "#expected_visitors", value: serie.time.expected_visitors },
        { target: "#fromDate", value: fromDate },
        { target: "#fromTime", value: fromTime },
        { target: "#toDate", value: toDate },
        { target: "#toTime", value: toTime },
    ].forEach( (mapping) => {
        $dialogElement.find(mapping.target).val(mapping.value);
    });

    window.MessagesFacility.send(dialogId, serie.time.audience, "setAudienceFromParent");
    window.MessagesFacility.send(dialogId, serie.time.arrangement_type, "setArrangementTypeFromParent");
    window.MessagesFacility.send(dialogId, serie.time.status, "setStatusFromParent");

    if (serie.planner_payload)
        window.MessagesFacility.send(dialogId, serie.planner_payload, "setPlanner");
    if (serie.room_payload)
        window.MessagesFacility.send(dialogId, serie.room_payload, "roomsSelected");
    if (serie.people_payload)
        window.MessagesFacility.send(dialogId, serie.people_payload, "peopleSelected");
}

/**
 *
 * @param {*} event
 */
export function PopulateCreateEventDialog(event, $dialogElement, dialogId) {
    let parseDateOrStringToArtifacts = function (dateOrString) {
        if (dateOrString instanceof String || typeof(dateOrString) === "string")
            return Utils.splitStrDate(dateOrString);
        else if (dateOrString instanceof Date)
            return Utils.splitDateIntoDateAndTimeStrings(dateOrString);
        else throw "Invalid value or type"
    }

    let [fromDate, fromTime]    = parseDateOrStringToArtifacts(event.start);
    let [toDate, toTime]        = parseDateOrStringToArtifacts(event.end);

    [
        { target: '#countySelect', value: event.county },
        { target: '#initialSchoolValue', value: event.school },
        { target: "#event_uuid", value: event._uuid },
        { target: "#title", value: event.title },
        { target: "#title_en", value: event.title_en },
        { target: "#ticket_code", value: event.ticket_code },
        { target: '#expected_visitors', value: event.expected_visitors },
        { target: '#fromDate', value: fromDate },
        { target: '#fromTime', value: fromTime },
        { target: '#toDate', value: toDate },
        { target: '#toTime', value: toTime },
        { target: '#buffer_before_title', value: event.before_buffer_title },
        { target: '#buffer_before_date', value: event.before_buffer_date },
        { target: '#buffer_before_start', value: event.before_buffer_start },
        { target: '#buffer_before_end', value: event.before_buffer_end },
        { target: '#buffer_after_title', value: event.after_buffer_title },
        { target: '#buffer_after_date', value: event.after_buffer_date },
        { target: '#buffer_after_start', value: event.after_buffer_start },
        { target: '#buffer_after_end', value: event.after_buffer_end },
        { target: '#_backingAudienceId', value: event.audience },
        { target: '#_backingArrangementTypeId', value: event.arrangement_type },
        { target: '#id_meeting_place', value: event.meeting_place },
        { target: '#id_meeting_place_en', value: event.meeting_place_en },
        { target: '#_statusTypeId', value: event.status },
        { target: '#id_display_text', value: event.display_text },
        { target: '#id_display_text_en', value: event.display_text_en },
    ].forEach( (mapping) => {
        $dialogElement.find( mapping.target ).val( mapping.value );
    } )

    if (Array.isArray(event.display_layouts)) {
        event.display_layouts.forEach(element => {
            $dialogElement.find(`#${String(parseInt(element))}_dlcheck`).prop( "checked", true );
        })
    }
    else {
        throw "Display layouts must be an array";
    }

    if (event.people_payload)
        window.MessagesFacility.send(dialogId, event.people_payload, "peopleSelected");
    if (event.room_payload)
        window.MessagesFacility.send(dialogId, event.room_payload, "roomsSelected");
    if (event.planner_payload)
        window.MessagesFacility.send(dialogId, event.planner_payload, "setPlanner");
}
