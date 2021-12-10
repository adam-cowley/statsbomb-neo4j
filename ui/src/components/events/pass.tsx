import React from "react"

import { EventProps } from "../../types/EventProps";
import { PlayerMarker } from "../player-marker";
import { EventLabel } from "./label";

export function PassEvent({ event, xScale, yScale }: EventProps) {
    return (
        <g className="pass" id={event.id}>
            <PlayerMarker
                x={xScale(event.location[0])}
                y={yScale(event.location[1])}
                actor={true}
                teammate={true}
            />


            <PlayerMarker
                x={xScale(event.pass.end_location[0])}
                y={yScale(event.pass.end_location[1])}
                actor={false}
                teammate={true}
            />

            <line
                x1={xScale(event.location[0])}
                y1={yScale(event.location[1])}
                x2={xScale(event.pass.end_location[0])}
                y2={yScale(event.pass.end_location[1])}
                stroke="blue"
                strokeWidth={2}
                // strokeDasharray={5}
                markerEnd="url(#arrowhead)"
            />
            <EventLabel
                xScale={xScale}
                yScale={xScale}
                type={event.type}
                timestamp={event.timestamp}
                location={event.location}
                player={event.player}
                outcome={event.pass.outcome}
            />
        </g>
    )
}