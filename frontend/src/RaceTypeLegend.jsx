import { raceStyles } from './raceTypes.js';
import './race-types.css';

export function RaceTypeLegend() {
  return <details className="race-legend">
    <summary>Légende des courses</summary>
    <ul>{raceStyles.map(style => <li key={style.id}>
      <span className="race-type-swatch" style={{ '--race-type-color': style.color }} aria-hidden="true" />
      {style.label}
    </li>)}</ul>
  </details>;
}
