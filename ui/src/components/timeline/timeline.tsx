import { Dispatch, SetStateAction } from "react"
import { Possession } from "../../types/Possession"
import { Team } from "../../types/StatsbombEvent"
import { scale, toMilliseconds } from "../../utils"
import { TimelinePossession } from "./possession"

interface TimelineProps {
    possessions: Possession[];
    current: Possession | undefined;
    setPossession: Dispatch<SetStateAction<Possession | undefined>>,
}

export function Timeline({ possessions, current, setPossession }: TimelineProps) {
    const start = toMilliseconds(possessions[0].startTimestamp)
    const end = toMilliseconds(possessions[possessions.length - 1].endTimestamp)

    const width = 950
    const leftPadding = 20

    const xScale = scale([start, end], [leftPadding, leftPadding + width])
    const yScale = scale([0, 1], [25, 75])

    const isHomeTeam = (team: Team) => team.id === possessions[0].team.id ? 0 : 1

    return (
        <div className="timeline">
            <svg width="1000px" height="100px">
                <g>
                    <rect id="placeholder" x={leftPadding} y="0" width={`${width}px`} height="100px" stroke="white" strokeOpacity="0.2" strokeWidth="1" />
                    <line id="start" x1={leftPadding} y1="0" x2={leftPadding} y2="100" stroke="white" strokeWidth="3" />
                    <line id="horizontal_divider" x1="20" y1="50" x2={width + leftPadding} y2="50" stroke="white" strokeOpacity="0.8" strokeWidth="1" strokeDasharray="3" />
                </g>

                <g id="events">
                    {possessions.map((possession: Possession) => <TimelinePossession
                        key={possession.id}
                        possession={possession}
                        current={current}
                        setPossession={setPossession}
                        isHomeTeam={isHomeTeam}
                        xScale={xScale}
                        yScale={yScale}
                    />)}
                </g>
            </svg>
        </div>
    )
}
