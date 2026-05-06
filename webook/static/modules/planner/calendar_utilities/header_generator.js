/**
 * header_generator.js
 * Utility for generating friendly and informative headers, based on the FullCalendar view.
 */

export class ViewClassifiers {
    static YEAR = Symbol("year");
    static MONTH = Symbol("month");
    static WEEK = Symbol("week");
    static DAY  = Symbol("day");
}

export class StandardGenerator {
    CLASSIFIER_MAP = new Map([
        [ViewClassifiers.YEAR, this.year],
        [ViewClassifiers.MONTH, this.month],
        [ViewClassifiers.WEEK, this.week],
        [ViewClassifiers.DAY, this.day],
    ])

    generate(classifier, date) {
        if (date instanceof Date === false) {
            throw "Not a valid date";
        }
        if (this.CLASSIFIER_MAP.has(classifier) === false) {
            throw "Classifier not recognized";
        }

        let gen_func = this.CLASSIFIER_MAP.get(classifier);
        
        if (gen_func instanceof Function === false) {
            throw "Generation function retrieved from CLASSIFIER_MAP is not a valid callable function.";
        }

        return gen_func(date);
    }

    year (date) {
        return `${date.getFullYear()}`;
    }

    month(date) {
        let text = `${date.toLocaleString("default", { month: "long" })} ${date.getFullYear()}`;
        text = text.replace(/^./, text[0].toUpperCase());
        return text;
    }

    week(date) {
        var target  = new Date(date.valueOf());
        var dayNr   = (date.getDay() + 6) % 7;
        target.setDate(target.getDate() - dayNr + 3);
        var firstThursday = target.valueOf();
        target.setMonth(0, 1);
        if (target.getDay() != 4) {
            target.setMonth(0, 1 + ((4 - target.getDay()) + 7) % 7);
        }

        const weekNum = 1 + Math.ceil((firstThursday - target) / 604800000);

        return `Uke ${weekNum}, ${date.toLocaleString("default", { month: "long" })} ${date.getFullYear()}`;
    }

    day(date) {
        return [
            String(date.getDate()).padStart(2, "0"),
            String(date.getMonth() + 1).padStart(2, "0"),
            date.getFullYear(),
        ].join(".");
    }
}

const BaseViewClassifications = new Map([
    /* DayGrid */
    [
        "dayGridDay",
        ViewClassifiers.DAY
    ],
    [
        "dayGridWeek",
        ViewClassifiers.WEEK
    ],
    [
        "dayGridMonth",
        ViewClassifiers.MONTH
    ],
    /* List */
    [
        "listDay",
        ViewClassifiers.DAY
    ],
    [
        "listWeek",
        ViewClassifiers.WEEK
    ],
    [
        "listMonth",
        ViewClassifiers.MONTH
    ],
    [
        "listYear",
        ViewClassifiers.YEAR
    ],
    /* Timegrid */
    [
        "timeGridDay",
        ViewClassifiers.DAY
    ],
    [
        "timeGridWeek",
        ViewClassifiers.WEEK,
    ],
    /* Timeline */
    [
        "timelineDay",
        ViewClassifiers.DAY
    ],
    [
        "timelineWeek",
        ViewClassifiers.WEEK
    ],
    [
        "timelineMonth",
        ViewClassifiers.MONTH
    ],
    [
        "timelineYear",
        ViewClassifiers.YEAR
    ],
    /* Resourcetimeline */
    [
        "resourceTimelineDay",
        ViewClassifiers.DAY
    ],
    [
        "resourceTimelineWeek",
        ViewClassifiers.WEEK
    ],
    [
        "resourceTimelineMonth",
        ViewClassifiers.MONTH
    ],
    [
        "resourceTimelineYear",
        ViewClassifiers.YEAR
    ]
]);

export class HeaderGenerator {
    constructor({ generator, customClassifications = undefined } = {}) {
        if (generator instanceof StandardGenerator === false) {
            if (generator !== undefined) {
                console.warn("Given generator is not an instance of StandardGenerator.");
            }

            this.generator = new StandardGenerator();
        }
        else {
            this.generator = generator;
        }

        this.classifiers = BaseViewClassifications;

        if (customClassifications instanceof Map) {
            this.classifiers = new Map( [...this.classifiers].concat([...customClassifications]) );
        }
    }

    generate(viewName, date) {
        return this.generator.generate(
            this.classifiers.get(viewName),
            date,
        );
    }
}