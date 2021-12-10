import React from "react"

import { EventProps } from "../../types/EventProps"
import { PlayerMarker } from "../player-marker"
import { EventLabel } from "./label"

export function ShotEvent({ event, xScale, yScale }: EventProps) {
  const freeze = event.shot.freeze_frame.map((player: any) => <PlayerMarker
    key={player.player.id}
    x={xScale(player.location[0])}
    y={yScale(player.location[1])}
    teammate={player.teammate}
    player={player.player}
    keeper={player.position.id === 1}
  />)

  return (
    <g className="shot" id={event.id}>
      <g className="freeze_frame">
        {freeze}
      </g>

      <line
        x1={xScale(event.location[0])}
        y1={yScale(event.location[1])}
        x2={xScale(event.shot.end_location[0])}
        y2={yScale(event.shot.end_location[1])}
        stroke="black"
        strokeWidth={2}
        strokeDasharray={3}
      // marker-end="url(#arrowhead)"
      />
      <PlayerMarker
        x={xScale(event.location[0])}
        y={yScale(event.location[1])}
        actor={true}
        teammate={true}
      />

      <circle
        cx={xScale(event.shot.end_location[0])}
        cy={yScale(event.shot.end_location[1])}
        r={6}
        fill="white"
      />

      <EventLabel
        xScale={xScale}
        yScale={xScale}
        type={event.type}
        timestamp={event.timestamp}
        location={event.location}
        player={event.player}
        outcome={event.shot.outcome}
      />
    </g>
  )
}