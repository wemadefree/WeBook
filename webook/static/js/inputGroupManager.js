/* 
InputGroupManager is a manager class/utility aimed to help with working with a group of
inputs in cohesion. In practice it makes working with a group of inputs (writing to, reading from, flushing)
easier and more "sugar"-y in the code.
One of the conventions required is that you use the attribute code-qualified-name on the input elements you
use in the InputGroupManager. This is the name you will use to interact with the element through the manager 
in the code - so it is important that it does never change in the future (unless you want to change it!)

Example usage: 

<input type='text' id='my_text_el' code-qualified-name='starlight' />

let inputGroupManager = InputGroupManager(
    [document.getElementById('my_text_el')]
)

inputGroupManager.starlight.value = "Starlight"

---- 
Quite cool.
*/
class InputGroupManager {
    constructor (input_elements) {
        this.origin = input_elements;
        for (let i = 0; i < input_elements.length; i++) {
            let element = input_elements[i];
            this[this.get_element_qualified_name(element, true)] = element;
        }
    }

    /* 
    Convert this input group into a key/value "object" 
    */
    to_object() {
        let produced_obj = {}

        for(let i=0; i < this.origin.length; i++) {
            let origin_el = this.origin[i];
            let qualified_code_name_of_el = get_element_qualified_name(origin_el, true);
            produced_obj[qualified_code_name_of_el] = this[qualified_code_name_of_el].value;
        }
        
        return produced_obj;
    }

    /* 
    Get the qualified "code name" of an element

    el: Element of which to get the code name
    throw_on_none: Dictates if we should raise an exception if the read name is invalid

    Returns, ideally, a string with the qualified code name.
    */
    get_element_qualified_name(el, throw_on_none=false) {
        let code_qualified_name_of_el = el.getAttribute("code-qualified-name");

        if (throw_on_none === true && (code_qualified_name_of_el === undefined || code_qualified_name_of_el === "")) {
            throw "When using an input with InputGroupManager you must define the code-qualified-name attribute!"
        }

        return code_qualified_name_of_el;
    }

    /* 
    Empty the values of all inputs in the group
    */
    flush() {
        for (let i = 0; i < origin.length; i++) {
            let el = this.origin[i];
            if (el !== undefined && el.id !== undefined) {
                if ($(el).attr("advanced-select")) {
                    let instance = mdb.Select.getInstance($(el)[0])
                    instance._handleClear();
                }

                this[el.id].value = "";
            }
        }
    }
}