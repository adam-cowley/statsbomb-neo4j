import { EventProps } from "../../types/EventProps"
import { CarryEvent } from "./carry"
import { InterceptionEvent } from "./interception"
import { EventLabel } from "./label"
import { PassEvent } from "./pass"
import { ShotEvent } from "./shot"

export function EventWrapper(props: EventProps) {
  const { event } = props

  switch (event.type.id) {
    case 10: // Interception
      return <InterceptionEvent {...props} />

    case 43: // Carry
      return <CarryEvent {...props} />

    case 30: // Pass
      return <PassEvent {...props} />

    case 16: // Shot
      return <ShotEvent {...props} />
  }


  const { xScale, yScale } = props
  return (
    <g className="unknown" id={event.id}>
      {event.location && (
        <g>
          <circle
            cx={xScale(event.location[0])}
            cy={yScale(event.location[1])}
            r={2}
            fill="black"
          />
          <EventLabel
            xScale={xScale}
            yScale={xScale}
            type={event.type}
            timestamp={event.timestamp}
            location={event.location}
            player={event.player}
            outcome={undefined}
          />
        </g>
      )}


    </g>

  )
}