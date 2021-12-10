import { StatsbombEvent, Team } from "./StatsbombEvent"

export class Possession {
    constructor(
        public id: number,
        public team: Team,
        public events: StatsbombEvent[]
    ) { }

    addEvent(event: StatsbombEvent) {
        this.events.push(event)
    }

    get last() {
        return this.events[this.events.length - 1]
    }

    get startTimestamp() {
        return this.events[0].timestamp
    }


    get endTimestamp() {
        return this.last.timestamp
    }

}