import { ScaleLinear, scaleLinear } from "d3-scale"
import { Possession } from "./types/Possession"
import { StatsbombEvent } from "./types/StatsbombEvent"

export function reduceToPossession(events: StatsbombEvent[]): Possession[] {
  return events.reduce((acc: Possession[], current: StatsbombEvent): Possession[] => {

    // No events, must be the first
    if (acc.length === 0) {
      return [new Possession(current.possession, current.possession_team, [current])]
    }

    // Get the last sequence
    const lastPossession = acc.pop()!

    // Append a new Possession record
    if (lastPossession.id !== current.possession) {
      return acc.concat(lastPossession, new Possession(current.possession, current.possession_team, [current]))
    }

    // Add the current event to the latest possession
    lastPossession.addEvent(current)

    return acc.concat(lastPossession)
  }, [])
}

export function toMilliseconds(timestamp: string): number {
  // TODO: Split timestamp properly or use the match date
  return new Date(`2021-01-01T${timestamp}`).getTime()
}

type NumberTuple = [number, number]
export type EventScale = ScaleLinear<number, number, never>;

export function scale(minAndMaxValues: NumberTuple = [0, 120], rangeInPixels: NumberTuple = [0, 1000]): EventScale {
  return scaleLinear().domain(minAndMaxValues).range(rangeInPixels)
}
