_SPINNER_IDENTIFYING_CLASS = "hinterSpinner"
_SPINNER_BASE_CLASSLIST = [ "spinner-grow", _SPINNER_IDENTIFYING_CLASS ]


class LoadingHint {
    constructor (targetElement) {
        this.targetElement = targetElement;
        this.$targetElement = $(this.targetElement);

        this._hintStateClassesMap = new Map([
            ["danger", "text-danger"],
            ["success", "text-success"],
            ["warning", "text-warning"],
            ["info", "text-info"]
        ])

        this.spinnerElement = targetElement.querySelector(".hinterSpinner");
        this.messageElement = targetElement.querySelector(".hinterMessage");
    }

    _constructHintBody (message, hintType) {
        this.messageElement.innerText = message;

        let classes = _SPINNER_BASE_CLASSLIST
        classes.push(this._hintStateClassesMap.get(hintType))

        this.spinnerElement.className = '';
        this.spinnerElement.classList.add(...classes);
    }

    _hideHintElement () {
        this.$targetElement.hide();
    }

    _showHintElement () {
        this.$targetElement.show();
    }

    startHinting({ hintMessage, hintType } = {}) {
        this._constructHintBody(hintMessage, hintType);
        this._showHintElement();
    }

    finishHinting() {
        this._hideHintElement();
    }
}