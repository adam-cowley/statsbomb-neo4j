import d3 from 'd3'
import { StatsbombEvent } from './StatsbombEvent';

interface EventProps {
  event: StatsbombEvent;
  xScale: d3.ScaleLinear<number, number, never>;
  yScale: d3.ScaleLinear<number, number, never>;
}