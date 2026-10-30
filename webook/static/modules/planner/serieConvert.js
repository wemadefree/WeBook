import { appendArrayToFormData } from "./commonLib.js";


export function serieConvert(serie, formData, keyPrefix=`manifest.`) {
    formData.append(`${keyPrefix}internal_uuid`, serie._uuid);
    formData.append(`${keyPrefix}pattern`, serie.pattern.pattern_type);
    formData.append(`${keyPrefix}patternRoutine`, serie.pattern.pattern_routine);
    formData.append(`${keyPrefix}timeAreaMethod`, serie.time_area.method_name);
    formData.append(`${keyPrefix}startDate`, serie.time_area.start_date);
    formData.append(`${keyPrefix}startTime`, serie.time.start);
    formData.append(`${keyPrefix}endTime`, serie.time.end);
    formData.append(`${keyPrefix}ticketCode`, serie.time.ticket_code );
    formData.append(`${keyPrefix}expectedVisitors`, serie.time.expected_visitors);
    formData.append(`${keyPrefix}title`, serie.time.title);
    formData.append(`${keyPrefix}title_en`, serie.time.title_en);
    if (serie.time.status !== undefined && serie.time.status !== null)
        formData.append(`${keyPrefix}status`, serie.time.status);
    formData.append(`${keyPrefix}audience`, serie.time.audience);
    formData.append(`${keyPrefix}arrangement_type`, serie.time.arrangement_type);
    formData.append(`${keyPrefix}meeting_place`, serie.time.meeting_place);
    formData.append(`${keyPrefix}meeting_place_en`, serie.time.meeting_place_en);
    formData.append(`${keyPrefix}responsible`, serie.time.responsible);
    formData.append(`${keyPrefix}display_text`, serie.time.display_text);
    formData.append(`${keyPrefix}county`, serie.time.county || "");
    formData.append(`${keyPrefix}school`, serie.time.school || "");
    if (serie.collision_resolution_behaviour === undefined)
        serie.collision_resolution_behaviour = 0
    formData.append(`${keyPrefix}collision_resolution_behaviour`, serie.collision_resolution_behaviour);

    if (serie.event_serie_pk)
        formData.append(`${keyPrefix}predecessorSerie`, serie.event_serie_pk);

    appendArrayToFormData(serie.rooms, formData, `${keyPrefix}rooms`);
    appendArrayToFormData(serie.people, formData, `${keyPrefix}people`);
    appendArrayToFormData(serie.display_layouts.split(","), formData, `${keyPrefix}display_layouts`);

    if (serie.buffer) {
        if (serie.buffer.before) {
            formData.append(`${keyPrefix}before_buffer_title`, serie.buffer.before.title);
            formData.append(`${keyPrefix}before_buffer_date_offset`, serie.buffer.before.date_offset);
            formData.append(`${keyPrefix}before_buffer_start`, serie.buffer.before.start);
            formData.append(`${keyPrefix}before_buffer_end`, serie.buffer.before.end);
        }
        if (serie.buffer.after) {
            formData.append(`${keyPrefix}after_buffer_title`, serie.buffer.after.title);
            formData.append(`${keyPrefix}after_buffer_date_offset`, serie.buffer.after.date_offset);
            formData.append(`${keyPrefix}after_buffer_start`, serie.buffer.after.start);
            formData.append(`${keyPrefix}after_buffer_end`, serie.buffer.after.end);
        }
    }

    switch(serie.pattern.pattern_type) {
        case "daily":
            if (serie.pattern.pattern_routine === "daily__every_x_day") {
                formData.append(`${keyPrefix}interval`, serie.pattern.interval);
            }
            break;
        case "weekly":
            formData.append(`${keyPrefix}interval`, serie.pattern.week_interval);
            let count = 0;
            for (const day of ["sunday", "monday", "tuesday", "wednesday", "thursday", "friday", "saturday"]) {
                formData.append(`${keyPrefix}${day}`, serie.pattern.days.get(count));
                count++;
            }
            break;
        case "monthly":
            switch (serie.pattern.pattern_routine) {
                case "month__every_x_day_every_y_month":
                    formData.append(`${keyPrefix}interval`, serie.pattern.interval);
                    formData.append(`${keyPrefix}day_of_month`, serie.pattern.day_of_month);
                    break;
                case "month__every_arbitrary_date_of_month":
                    formData.append(`${keyPrefix}arbitrator`, serie.pattern.arbitrator);
                    formData.append(`${keyPrefix}day_of_week`, serie.pattern.weekday);
                    formData.append(`${keyPrefix}interval`, serie.pattern.interval);
                    break;
            }
            break;
        case "yearly":
            formData.append(`${keyPrefix}interval`, serie.pattern.year_interval);
            switch (serie.pattern.pattern_routine) {
                case "yearly__every_x_of_month":
                    formData.append(`${keyPrefix}day_of_month`, serie.pattern.day_index);
                    formData.append(`${keyPrefix}month`, serie.pattern.month);
                    break;
                case "yearly__every_arbitrary_weekday_in_month":
                    formData.append(`${keyPrefix}day_of_week`, serie.pattern.weekday);
                    formData.append(`${keyPrefix}month`, serie.pattern.month);
                    formData.append(`${keyPrefix}arbitrator`, serie.pattern.arbitrator);
                    break;
            }
            break;
    }
    
    if (serie.time_area.stop_within !== undefined) {
        formData.append(`${keyPrefix}stopWithin`, serie.time_area.stop_within);
    }
    if (serie.time_area.instances !== undefined) {
        formData.append(`${keyPrefix}stopAfterXInstances`, serie.time_area.instances);
    }
    if (serie.time_area.projectionDistanceInMonths !== undefined) {
        formData.append(`${keyPrefix}projectionDistanceInMonths`, serie.time_area.projectionDistanceInMonths);
    }

    return formData;
}