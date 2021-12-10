import React from "react";
import { ScaleLinear } from "d3-scale";

interface ArrowProps {
  start: number[];
  end: number[];
  xScale: ScaleLinear<number, number, never>;
  yScale: ScaleLinear<number, number, never>;
  [style: string]: any;
}

export function Arrow({ xScale, yScale, start, end, ...props }: ArrowProps) {
  return (
    <line
      x1={xScale(start[0])}
      y1={yScale(start[1])}
      x2={xScale(end[0])}
      y2={yScale(end[1])}
      stroke="black"
      strokeWidth={2}
      markerEnd="url(#arrowhead)"
      {...props}
    />
  )
}