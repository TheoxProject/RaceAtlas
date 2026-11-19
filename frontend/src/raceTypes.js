import { SPORTS, TYPES } from './catalog.js';

const colors = {
  neutral: '#475569',
  road_race: '#9a3412',
  time_trial: '#1d4ed8',
  hill_climb: '#6d28d9',
  track: '#9d174d',
  cyclocross: '#b91c1c',
  gravel: '#a16207',
  mtb: '#166534',
  xco: '#3f6212',
  enduro: '#0f766e',
  downhill: '#155e75',
};

export const raceStyles = Object.entries(colors).map(([key, color], id) => {
  const [discipline, type] = TYPES[key] || [];
  return {
    id,
    color,
    label: key === 'neutral' ? 'Type non précisé ou types variés' : type || SPORTS[key],
    discipline: discipline || key,
  };
});

const stylesByKey = new Map(Object.keys(colors).map((key, index) => [key, raceStyles[index]]));
export const neutralStyle = raceStyles[0];

export function raceStyle(race) {
  const types = [...new Set(race.types)];
  if (types.length > 1) return neutralStyle;
  const style = stylesByKey.get(types[0]);
  if (style?.discipline === race.discipline) return style;
  return stylesByKey.get(race.discipline) || neutralStyle;
}

export function raceStyleLabel(race, style) {
  const discipline = SPORTS[race.discipline];
  if (style === neutralStyle) {
    const type = new Set(race.types).size > 1 ? 'Types variés' : 'Type non précisé';
    return discipline ? `${discipline} · ${type}` : type;
  }
  return discipline === style.label ? style.label : `${discipline} · ${style.label}`;
}
