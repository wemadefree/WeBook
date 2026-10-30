class Recipient {
    constructor(name) {
        this.name = name;
        this._messages = new Map();
    }

    leaveMessage(messageKey, message) {
        if (!messageKey)
            messageKey = crypto.randomUUID();

        this._messages.set(messageKey, message);
    }

    getMessage(messageKey) {
        return this._messages.get(messageKey);
    }

    allMessages() {
        return Array.from(this._messages.values());
    }

    clear() {
        this._messages = new Map();
    }
}

export class MessagesFacility {
    constructor() {
        this._recipients = new Map();
        this._subscriptions = new Map();
    }

    send(recipient, payload, key = undefined) {
        if (!this._recipients.has(recipient))
            this._recipients.set(recipient, new Recipient(recipient));
        
        const subscriptionsOnRecipient = this._subscriptions.get(recipient);
        if (subscriptionsOnRecipient)
        {
            const subscription = subscriptionsOnRecipient[subscriptionsOnRecipient.length - 1];
            const result = subscription(key, payload);
            if (result !== null)
                return;
        }
        this._recipients.get(recipient).leaveMessage(key, payload);
        return;
        
        

        if (this._subscriptions.get(recipient)) {
            const subscriptionsOnRecipient = this._subscriptions.get(recipient);

            const subscription = subscriptionsOnRecipient[subscriptionsOnRecipient.length - 1]

            subscription(key, payload);

            // for (let i = 0; i < subscriptionsOnRecipient.length; i++) {
            //     const result = subscriptionsOnRecipient[i](key, payload)
                
            //     if (result === null)
            //     {
            //         /**
            //          * If a subscription function returns null we read this as if the
            //          * subscription instance has perished, and should therefore be removed.
            //          */
            //         subscriptionsOnRecipient.splice(i, 1);
            //         this._subscriptions.set(recipient, subscriptionsOnRecipient);
            //     }
            // }
            // this._subscriptions.get(recipient).forEach((subscriptionFunction) => { 
            //     const result = subscriptionFunction(key, payload);
            //     if (result === null)
            //         this._subscriptions.get(recipient)
            // });
        }
    }

    addressedTo(recipient) {
        return this._recipients.get(recipient);
    }

    subscribe( recipient, onChange ) {
        if (this._subscriptions.has( recipient ))
            this._subscriptions.get( recipient ).push( onChange );
        else
            this._subscriptions.set( recipient, [ onChange ] );
    }
}