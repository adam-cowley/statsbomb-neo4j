import React from 'react'

import { EventProps } from "../../types/EventProps";
import { PlayerMarker } from "../player-marker";

export function InterceptionEvent({ xScale, yScale, event }: EventProps) {
    return (
      <g className="interception" id={event.id}>
        <PlayerMarker
          x={xScale(event.location[0])}
          y={yScale(event.location[1])}
          teammate={true}
        />
      </g>
    )
  }