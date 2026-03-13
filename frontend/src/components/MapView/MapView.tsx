import React, { useEffect, useState } from 'react';
import { MapContainer, TileLayer, CircleMarker, Popup, useMap } from 'react-leaflet';
import { getPotholes, getHeatmapData } from '../../services/api';
import { Pothole, HeatmapPoint } from '../../types';
import 'leaflet/dist/leaflet.css';
import './MapView.css';

const SEVERITY_COLOR: Record<string, string> = {
  minor: '#34a853',
  moderate: '#fbbc04',
  severe: '#ea4335',
};

interface MapViewProps {
  selectedPothole?: Pothole | null;
}

const MapView: React.FC<MapViewProps> = ({ selectedPothole }) => {
  const [potholes, setPotholes] = useState<Pothole[]>([]);
  const [heatmapPoints, setHeatmapPoints] = useState<HeatmapPoint[]>([]);
  const [showHeatmap, setShowHeatmap] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const load = async () => {
      try {
        const [p, h] = await Promise.all([
          getPotholes({ limit: 500 }),
          getHeatmapData(),
        ]);
        setPotholes(p.potholes);
        setHeatmapPoints(h.points);
      } catch {
        // Backend may not be running during development
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  const center: [number, number] = selectedPothole
    ? [selectedPothole.latitude, selectedPothole.longitude]
    : [20.5937, 78.9629]; // India center

  return (
    <div className="map-view">
      <div className="map-controls">
        <button
          className={`toggle-btn ${showHeatmap ? 'active' : ''}`}
          onClick={() => setShowHeatmap((v) => !v)}
        >
          {showHeatmap ? '🗺️ Show Markers' : '🔥 Show Heat Map'}
        </button>
        <span className="map-count">{potholes.length} pothole(s) on map</span>
      </div>

      {loading && <div className="map-loading">Loading map data...</div>}

      <MapContainer center={center} zoom={5} className="leaflet-map" scrollWheelZoom>
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />

        {!showHeatmap &&
          potholes.map((p) => (
            <CircleMarker
              key={p.id}
              center={[p.latitude, p.longitude]}
              radius={8}
              fillColor={SEVERITY_COLOR[p.severity] || '#1a73e8'}
              color="#fff"
              weight={1.5}
              fillOpacity={0.85}
            >
              <Popup>
                <div className="popup-content">
                  <strong>Pothole #{p.id}</strong>
                  <div>Severity: <span style={{ color: SEVERITY_COLOR[p.severity] }}>{p.severity.toUpperCase()}</span></div>
                  <div>Status: {p.status.replace('_', ' ')}</div>
                  {p.road_name && <div>Road: {p.road_name}</div>}
                  {p.depth_cm && <div>Depth: {p.depth_cm.toFixed(1)} cm</div>}
                  {p.risk_score && <div>Risk Score: {p.risk_score.toFixed(1)}</div>}
                  <div className="popup-date">
                    Detected: {new Date(p.detected_at).toLocaleDateString()}
                  </div>
                </div>
              </Popup>
            </CircleMarker>
          ))}

        {showHeatmap &&
          heatmapPoints.map((pt, i) => (
            <CircleMarker
              key={i}
              center={[pt.lat, pt.lon]}
              radius={12}
              fillColor={SEVERITY_COLOR[pt.severity]}
              color="none"
              fillOpacity={pt.intensity * 0.7 + 0.2}
            >
              <Popup>
                <div>Pothole #{pt.pothole_id}</div>
                <div>Risk: {(pt.intensity * 100).toFixed(0)}</div>
              </Popup>
            </CircleMarker>
          ))}
      </MapContainer>

      {/* Legend */}
      <div className="map-legend">
        <span className="legend-item">
          <span className="dot" style={{ background: '#34a853' }} /> Minor
        </span>
        <span className="legend-item">
          <span className="dot" style={{ background: '#fbbc04' }} /> Moderate
        </span>
        <span className="legend-item">
          <span className="dot" style={{ background: '#ea4335' }} /> Severe
        </span>
      </div>
    </div>
  );
};

export default MapView;
