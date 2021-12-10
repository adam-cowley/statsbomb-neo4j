import React from 'react'

import { EventProps } from "../../types/EventProps";
import { Arrow } from "../arrow";
import { PlayerMarker } from "../player-marker";
import { EventLabel } from './label';

export function CarryEvent({ xScale, yScale, event }: EventProps) {
    return (
      <g className="carry" id={event.id}>
        <PlayerMarker
          x={xScale(event.location[0])}
          y={yScale(event.location[1])}
          teammate={true}
        />
        <Arrow
          start={event.location}
          end={event.carry.end_location}
          xScale={xScale}
          yScale={yScale}
          strokeDasharray={3}
        />
        <EventLabel
          xScale={xScale}
          yScale={xScale}
          type={event.type}
          timestamp={event.timestamp}
          location={event.location}
          player={event.player}
          outcome={event.carry.outcome}
        />
      </g>
    )
  }