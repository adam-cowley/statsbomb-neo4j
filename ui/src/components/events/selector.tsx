import React from "react";

import { StatsbombEvent } from "../../types/StatsbombEvent";

export function EventSelector({events, handleSelectChange}: any) {
    return (
    <select onChange={handleSelectChange} style={{margin: '12px', padding: '12px', width: '320px'}}>
        {events?.filter((event: StatsbombEvent) => [16].includes(event.type.id))
          .map((item: StatsbombEvent) => <option key={item.id} value={item.id}>
          {item.minute}:{('00'+item.second).substr(-2)}: {item.type?.name} {item.player && `by ${item.player?.name}` }
        </option>)}
      </select>
    )
}