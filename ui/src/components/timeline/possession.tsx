import { Dispatch, SetStateAction } from "react"
import { Possession } from "../../types/Possession"
import { StatsbombEvent, Team } from "../../types/StatsbombEvent"
import { EventScale, toMilliseconds } from "../../utils"

interface TimelinePossessionProps {
    possession: Possession;
    current: Possession | undefined;
    setPossession: Dispatch<SetStateAction<Possession | undefined>>;
    xScale: EventScale;
    yScale: EventScale;
    isHomeTeam: (team: Team) => number;
  }

export function TimelinePossession({ possession, current, xScale, yScale, isHomeTeam, setPossession }: TimelinePossessionProps) {
    const start = toMilliseconds(possession.startTimestamp)
    const end = toMilliseconds(possession.endTimestamp)

    const yCoordinate = yScale(isHomeTeam(possession.team) ? 0 : 1)
    const fill = isHomeTeam(possession.team) ? 'red' : 'green'
    const stroke = isHomeTeam(possession.team) ? 'red' : 'green'

    const endRadius = possession.events.some((p: StatsbombEvent) => p.type.id === 16) ? 10 : 2
    const endStrokeWidth = possession.events.some((p: StatsbombEvent) => p.type.id === 16 && p.shot.outcome.id === 97) ? 5 : 0
    const opacity = current?.id === possession.id ? 1 : 0.4

    return (
      <g id={possession.id.toString()} onMouseEnter={() => setPossession(possession)} opacity={opacity}>
        <line x1={xScale(start)} y1={yCoordinate} x2={xScale(start)} y2="50" stroke={stroke} strokeOpacity="0.6" />
        <line x1={xScale(end)} y1={yCoordinate} x2={xScale(end)} y2="50" stroke="white" strokeWidth="1" strokeOpacity="0.8" strokeDasharray="2" />
        <circle className="start" cx={xScale(start)} cy={yCoordinate} r="2" fill={fill} />
        <circle className="end" cx={xScale(end)} cy={yCoordinate} r={endRadius} fill={fill} stroke="white" strokeWidth={endStrokeWidth} />
      </g>
    )
  }