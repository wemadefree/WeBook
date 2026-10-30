class BaseAPIRepository {
    constructor(entityName, friendlyNameSingular, friendlyNamePlural) {
        this.entityName = entityName
        this.friendlyNamePlural = friendlyNamePlural
        this.friendlyNameSingular = friendlyNameSingular
    }

    handle_response(response, operation) {
        if (response.status >= 200 && response.status < 300) {
            return response.json();
        }

        if (response.status === 401) {
            toastr.error('Du er ikke logget inn')
        } else if (response.status === 403) {
            toastr.error('Du har ikke tilgang til denne ressursen')
        } else {
            toastr.error('Noe gikk galt')
        }

        throw new Error(`${operation} failed with status code: ${response.status}`)
    }

    async getById(id, response=null) {
        if (response === null) {
            response = await fetch(`/api/${this.entityName}/get?id=${id}`)
        }

        const responseData = this.handle_response(response, "Get");
        return responseData;
    }

    async create(data, csrf_token, response=null) {
        if (response === null) {
            const response = await fetch(`/api/${this.entityName}/create`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrf_token
                },
                body: JSON.stringify(data)
            });
        }

        const responseData = this.handle_response(response, "Create");
        toastr.success(`${this.friendlyNameSingular} opprettet`)
        return responseData;
    }

    async update(id, data, csrf_token, response=null) {
        if (response === null) {
            response = await fetch(`/api/${this.entityName}/patch?id=${id}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrf_token
                },
                body: JSON.stringify(data)
            });
        }

        const responseData = this.handle_response(response, "Update");
        toastr.success(`${this.friendlyNameSingular} oppdatert`)
        return responseData;
    }

    async archive(id, csrf_token, response=null) {
        if (response === null) {
            response = await fetch(`/api/${this.entityName}/delete?id=${id}`, {
                method: 'DELETE',
                headers: {
                    'X-CSRFToken': csrf_token
                }
            });
        }

        const responseData = this.handle_response(response, "Archive");
        toastr.success(`${this.friendlyNameSingular} arkivert`)
        return responseData;
    }
}


class SchoolAPIRepository extends BaseAPIRepository {
    constructor() {
        super('school', 'Skole', 'Skoler')
    }

    async getById(id) {
        const response = await fetch(`/api/onlinebooking/school/get?id=${id}`)
        return response.json()
    }

    async archive(id, csrf_token) {
        const response = await fetch(`/api/onlinebooking/school/delete?id=${id}`, {
            method: 'DELETE',
            headers: {
                'X-CSRFToken': csrf_token
            }
        });

        return super.archive(id, csrf_token, response);
    }

    async create(data, csrf_token) {
        const response = await fetch(`/api/onlinebooking/school/create`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrf_token
            },
            body: JSON.stringify(data)
        });

        return super.create(data, csrf_token, response);
    }

    async update(id, data, csrf_token) {
        const response = await fetch(`/api/onlinebooking/school/patch?id=${id}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrf_token
            },
            body: JSON.stringify(data)
        });

        return super.update(id, data, csrf_token, response);
    }

    async archive(id, csrf_token) {
        return await Swal.fire({
            title: 'Er du sikker?',
            text: "Ved arkivering av skole vil også alle underliggende bookinger bli arkivert.",
            icon: 'warning',
            showCancelButton: true,
            confirmButtonColor: '#3085d6',
            cancelButtonColor: '#d33',
            confirmButtonText: "Ja, arkiver",
            cancelButtonText: "Avbryt"
        }).then(async response => {
            if (response.value) {
                const response = await fetch(`/api/onlinebooking/school/delete?id=${id}`, {
                    method: 'DELETE',
                    headers: {
                        'X-CSRFToken': csrf_token
                    }
                });
        
                return super.archive(id, csrf_token, response);
            }

            return null;
        });
    }
}

class CountyAPIRepository extends BaseAPIRepository {
    constructor() {
        super('county', 'Fylke', 'Fylker')
    }

    async getById(id) {
        const response = await fetch(`/api/onlinebooking/county/get?id=${id}`)
        return response.json()
    }

    async create(data, csrf_token) {
        const response = await fetch(`/api/onlinebooking/county/create`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrf_token
            },
            body: JSON.stringify(data)
        });

        return super.create(data, csrf_token, response);
    }

    async update(id, data, csrf_token) {
        const response = await fetch(`/api/onlinebooking/county/patch?id=${id}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrf_token
            },
            body: JSON.stringify(data)
        });

        return super.update(id, data, csrf_token, response);
    }

    async archive(id, csrf_token) {
        return await Swal.fire({
            title: 'Er du sikker?',
            text: "Ved arkivering av fylke vil også alle underliggende skoler, bookinger og bydeler bli arkivert.",
            icon: 'warning',
            showCancelButton: true,
            confirmButtonColor: '#3085d6',
            cancelButtonColor: '#d33',
            confirmButtonText: "Ja, arkiver",
            cancelButtonText: "Avbryt"
        }).then(async response => {
            if (response.value) {
                const response = await fetch(`/api/onlinebooking/county/delete?id=${id}`, {
                    method: 'DELETE',
                    headers: {
                        'X-CSRFToken': csrf_token
                    }
                });
        
                return super.archive(id, csrf_token, response);
            }

            return null;
        });
    }
}

class CitySegmentAPIRepository extends BaseAPIRepository {
    constructor () {
        super('citysegment', 'Bydel', 'Bydeler')
    }

    async getById(id) {
        const response = await fetch(`/api/onlinebooking/city_segment/get?id=${id}`)
        return response.json()
    }

    async create(data, csrf_token) {
        const response = await fetch(`/api/onlinebooking/city_segment/create`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrf_token
            },
            body: JSON.stringify(data)
        });

        return super.create(data, csrf_token, response);
    }

    async update(id, data, csrf_token) {
        const response = await fetch(`/api/onlinebooking/city_segment/patch?id=${id}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrf_token
            },
            body: JSON.stringify(data)
        });

        return super.update(id, data, csrf_token, response);
    }

    async archive(id, csrf_token) {
        return await Swal.fire({
            title: 'Er du sikker?',
            text: "Ved arkivering av bydel vil også alle skoler og bookinger tilknyttet bydelen bli arkivert.",
            icon: 'warning',
            showCancelButton: true,
            confirmButtonColor: '#3085d6',
            cancelButtonColor: '#d33',
            confirmButtonText: "Ja, arkiver",
            cancelButtonText: "Avbryt"
        }).then(async response => {
            if (response.value) {
                const response = await fetch(`/api/onlinebooking/city_segment/delete?id=${id}`, {
                    method: 'DELETE',
                    headers: {
                        'X-CSRFToken': csrf_token
                    }
                });
        
                return super.archive(id, csrf_token, response);
            }

            return null;
        });
    }
}

class OnlineBookingAPIRepository extends BaseAPIRepository {
    constructor() {
        super('onlinebooking', 'Booking', 'Bookinger')
    }

    async getById(id) {
        const response = await fetch(`/api/onlinebooking/online_booking/get?id=${id}`)
        return response.json()
    }

    async create(data, csrf_token) {
        const response = await fetch(`/api/onlinebooking/online_booking/create`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrf_token
            },
            body: JSON.stringify(data)
        });

        return super.create(data, csrf_token, response);
    }

    async update(id, data, csrf_token) {
        const response = await fetch(`/api/onlinebooking/online_booking/patch?id=${id}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrf_token
            },
            body: JSON.stringify(data)
        });

        return super.update(id, data, csrf_token, response);
    }

    async archive(id, csrf_token) {
        return await Swal.fire({
            title: 'Er du sikker?',
            text: "Ved arkivering vil bookingen bli fjernet fra planleggingskalenderen.",
            icon: 'warning',
            showCancelButton: true,
            confirmButtonColor: '#3085d6',
            cancelButtonColor: '#d33',
            confirmButtonText: "Ja, arkiver",
            cancelButtonText: "Avbryt"
        }).then(async response => {
            if (response.value) {
                const response = await fetch(`/api/onlinebooking/online_booking/delete?id=${id}`, {
                    method: 'DELETE',
                    headers: {
                        'X-CSRFToken': csrf_token
                    }
                });
        
                return super.archive(id, csrf_token, response);
            }

            return null;
        });
    }
}