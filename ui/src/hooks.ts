import React, { useEffect, useState } from "react"
import { StatsbombEvent } from "./types/StatsbombEvent"
import { getJson } from "./data/json"
import { HOSTNAME, VERSIONS } from "./config";

interface UseEventsOutput {
  loading: boolean;
  events: StatsbombEvent[]
}



export const useEvents = (id: number): UseEventsOutput => {
  const [ loading, setLoading ] = useState<boolean>(true)
  const [ events, setEvents ] = useState<StatsbombEvent[]>([])

  useEffect(() => {
    // getJson(`https://raw.githubusercontent.com/statsbomb/open-data/master/data/events/${id}.json`)
    getJson(`${HOSTNAME}/api/${VERSIONS['events']}/events/${id}`)
      .then((res: StatsbombEvent[]) => {
        setEvents(res)
      })
      .catch((e: Error) => {
        // TODO: Nothing ever goes wrong...
      })
      .finally(() => {
        setLoading(false)
      })
  }, [ id ])

  return {
    loading,
    events
  }
}
