import React from "react"

import { FreezeFrame } from "../types/FreezeFrame";

interface PlayerMarkerProps extends FreezeFrame {
  x: number;
  y: number;
}

export function PlayerMarker({ x, y, teammate, actor, keeper, location, player }: PlayerMarkerProps) {
  const fill = keeper ? 'lime' : teammate ? 'red' : 'blue'
  const opacity = actor ? 1 : .5;

  return <circle cx={x} cy={y} r={5} strokeWidth={2} stroke="white" opacity={opacity} fill={fill} id={player?.id.toString() || Math.random().toString()}></circle>
}