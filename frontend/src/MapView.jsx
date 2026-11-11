import { useEffect, useRef, useState } from 'react';
import maplibregl from 'maplibre-gl';
import 'maplibre-gl/dist/maplibre-gl.css';
import { groupCommunes } from './catalog.js';

const STYLE = 'https://tiles.openfreemap.org/styles/liberty';
const DEM = 'https://tiles.mapterhorn.com/tilejson.json';
const empty = { type: 'FeatureCollection', features: [] };

export function MapView({ features, races, mode, setMode, onReliefError, onSelect, chooseCenter, onCenter }) {
  const container = useRef(null), mapRef = useRef(null), current = useRef({});
  const [message, setMessage] = useState(''), [ready, setReady] = useState(false);
  useEffect(() => { current.current = { onSelect, chooseCenter, onCenter, races }; });
  useEffect(() => {
    let map, markers = [], resize, active = true, markerSignature = '';
    const failTerrain = () => {
      if (!map?.getSource('elevation')) return;
      map.setTerrain(null);
      if (map.getLayer('relief')) map.setLayoutProperty('relief', 'visibility', 'none');
      setMode('altitude');
      onReliefError(true);
      setMessage('Le relief est indisponible. La carte et les courses restent accessibles.');
    };
    try {
      map = new maplibregl.Map({ container: container.current, style: STYLE, center: [4.9, 45.35], zoom: 6.5, pitch: 35, bearing: -12, attributionControl: false, canvasContextAttributes: { antialias: true } });
      mapRef.current = map;
      const recordCamera = () => { container.current.dataset.camera = JSON.stringify({ center: map.getCenter().toArray(), zoom: map.getZoom(), bearing: map.getBearing(), pitch: map.getPitch() }); };
      recordCamera(); map.on('moveend', recordCamera);
      map.addControl(new maplibregl.NavigationControl({ visualizePitch: true }), 'bottom-right');
      map.getCanvas().setAttribute('aria-label', 'Carte des courses en Auvergne-Rhône-Alpes');
      map.on('error', event => {
        if (['elevation', 'terrain-elevation'].includes(event.sourceId) || event.error?.message?.includes('mapterhorn')) failTerrain();
        else setMessage('Le fond de carte est partiellement indisponible. Les courses restent consultables.');
      });
      map.on('webglcontextlost', () => setMessage('L’affichage de la carte est interrompu. Retrouvez les courses avec Explorer les communes.'));
      map.on('load', () => {
        map.addSource('elevation', { type: 'raster-dem', url: DEM, tileSize: 512, encoding: 'terrarium', attribution: '© Mapterhorn' });
        map.addLayer({ id: 'relief', type: 'hillshade', source: 'elevation', paint: { 'hillshade-exaggeration': 0.35, 'hillshade-shadow-color': '#4d5e57', 'hillshade-highlight-color': '#fff8e8' } });
        map.addSource('communes', { type: 'geojson', data: empty, cluster: true, clusterRadius: 52, clusterMaxZoom: 11, clusterProperties: { race_count: ['+', ['get', 'race_count']] } });
        map.addLayer({ id: 'race-points', type: 'circle', source: 'communes', paint: { 'circle-radius': 12, 'circle-color': '#F97316', 'circle-stroke-width': 3, 'circle-stroke-color': '#ffffff' } });
        setReady(true);
        container.current.dataset.ready = 'true';
      });
      const renderMarkers = () => {
        if (map.getTerrain()) {
          const elevation = map.queryTerrainElevation(map.getCenter());
          if (elevation != null) container.current.dataset.elevation = String(elevation);
        }
        if (!map.getLayer('race-points')) return;
        const seen = new Set(), visible = [];
        for (const feature of map.queryRenderedFeatures({ layers: ['race-points'] })) {
          const properties = feature.properties;
          const key = properties.cluster ? `cluster-${properties.cluster_id}` : properties.commune_id;
          if (seen.has(key)) continue;
          seen.add(key);
          const ids = properties.cluster ? [] : JSON.parse(properties.race_ids);
          const commune = current.current.races.find(item => ids.includes(item.race.id))?.race.location?.commune_name;
          visible.push({ feature, properties, key, ids, commune });
        }
        const signature = JSON.stringify(visible.map(({ key, properties, commune, feature }) => [key, properties.race_count, properties.race_ids, commune, feature.geometry.coordinates]).sort());
        if (signature === markerSignature) return;
        markerSignature = signature;
        markers.forEach(marker => marker.remove()); markers = [];
        for (const { feature, properties, ids, commune } of visible) {
          const button = document.createElement('button');
          button.className = properties.cluster ? 'race-marker cluster-marker' : 'race-marker';
          button.textContent = properties.race_count;
          button.setAttribute('aria-label', properties.cluster ? `${properties.race_count} courses regroupées, agrandir` : `${properties.race_count} course${properties.race_count > 1 ? 's' : ''} à ${commune || 'cette commune'}`);
          button.addEventListener('click', async event => {
            event.stopPropagation();
            if (properties.cluster) {
              try {
                const zoom = await map.getSource('communes').getClusterExpansionZoom(properties.cluster_id);
                map.easeTo({ center: feature.geometry.coordinates, zoom, duration: 400 });
              } catch { /* A newer source may have replaced this cluster. */ }
            } else current.current.onSelect(ids);
          });
          markers.push(new maplibregl.Marker({ element: button }).setLngLat(feature.geometry.coordinates).addTo(map));
        }
      };
      // A failed external source may prevent `idle`; rendering still delivers race points.
      // Preserve unchanged button nodes so keyboard focus survives ordinary map frames.
      map.on('render', renderMarkers);
      map.on('click', event => { if (current.current.chooseCenter) current.current.onCenter([event.lngLat.lng, event.lngLat.lat]); });
      resize = new ResizeObserver(() => map.resize()); resize.observe(container.current);
    } catch {
      queueMicrotask(() => { if (active) setMessage('La carte est indisponible sur cet appareil. Retrouvez les courses avec Explorer les communes.'); });
    }
    return () => { active = false; resize?.disconnect(); markers.forEach(marker => marker.remove()); map?.remove(); mapRef.current = null; };
  }, [setMode, onReliefError]);
  useEffect(() => {
    if (!ready) return;
    mapRef.current.getSource('communes').setData({ type: 'FeatureCollection', features: groupCommunes(features).map(group => ({ type: 'Feature', geometry: { type: 'Point', coordinates: group.coordinates }, properties: { commune_id: group.id, race_count: group.raceIds.length, race_ids: JSON.stringify(group.raceIds) } })) });
  }, [features, ready]);
  useEffect(() => {
    if (!ready) return;
    const map = mapRef.current;
    container.current.dataset.terrain = mode;
    if (mode === 'summit') {
      // Separate DEM source for terrain avoids sharing hillshade's tile render cache.
      if (!map.getSource('terrain-elevation')) map.addSource('terrain-elevation', { type: 'raster-dem', url: DEM, tileSize: 512, encoding: 'terrarium', attribution: '© Mapterhorn' });
      map.setTerrain({ source: 'terrain-elevation', exaggeration: 1.3 }); map.easeTo({ pitch: 60, duration: 500 });
    }
    else { map.setTerrain(null); map.easeTo({ pitch: 35, duration: 500 }); /* Period/filter updates never touch this camera. */ }
  }, [mode, ready]);
  return <>
    <div className={`map-canvas ${chooseCenter ? 'choosing-center' : ''}`} ref={container} />
    {message && <p className="map-warning" role="status">{message}</p>}
    <div className="map-attribution"><a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noreferrer">© OpenStreetMap</a> · <a href="https://openmaptiles.org/" target="_blank" rel="noreferrer">OpenMapTiles</a> · <a href="https://openfreemap.org/" target="_blank" rel="noreferrer">OpenFreeMap</a> · <a href="https://mapterhorn.com/" target="_blank" rel="noreferrer">© Mapterhorn</a></div>
  </>;
}
