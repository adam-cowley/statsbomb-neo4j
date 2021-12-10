import { Player } from "../../types/Player";
import { Outcome } from "../../types/Outcome";
import { StatsbombEventType } from "../../types/StatsbombEvent";
import { EventScale } from "../../utils"

interface EventLabelProps {
  xScale: EventScale;
  yScale: EventScale;
  location: number[];
  timestamp: string;
  type: StatsbombEventType;
  player: Player;
  outcome?: Outcome;
}

export function EventLabel({ location, timestamp, type, player, outcome, xScale, yScale }: EventLabelProps) {
  return (
    <text
      className="event-label"
      textAnchor="end"
      x={xScale(location[0] - 3)}
      y={yScale(location[1] + 3)}
      fill="black"
      stroke="white"
      strokeWidth="6"
      paintOrder="stroke"
    >
      {/* {timestamp}: */}
      {type.name} by {player.name}
      {outcome && `(${outcome.name})`}
    </text>
  )
}