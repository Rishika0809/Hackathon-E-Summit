import React, { useEffect, useState } from 'react';
import { getPotholes, fileComplaint } from '../../services/api';
import { Pothole } from '../../types';
import './PotholeList.css';

const SEVERITY_BADGE: Record<string, string> = {
  minor: 'badge-minor',
  moderate: 'badge-moderate',
  severe: 'badge-severe',
};

interface PotholeListProps {
  onSelect?: (p: Pothole) => void;
}

const PotholeList: React.FC<PotholeListProps> = ({ onSelect }) => {
  const [potholes, setPotholes] = useState<Pothole[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState({ severity: '', status: '' });
  const [page, setPage] = useState(0);
  const [filing, setFiling] = useState<number | null>(null);
  const LIMIT = 20;

  const load = async () => {
    setLoading(true);
    try {
      const resp = await getPotholes({
        severity: filter.severity || undefined,
        status: filter.status || undefined,
        skip: page * LIMIT,
        limit: LIMIT,
      });
      setPotholes(resp.potholes);
      setTotal(resp.total);
    } catch {
      // handle error
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filter, page]);

  const handleFileComplaint = async (p: Pothole) => {
    setFiling(p.id);
    try {
      await fileComplaint(p.id);
      await load();
      alert(`Complaint filed for Pothole #${p.id}`);
    } catch {
      alert('Failed to file complaint.');
    } finally {
      setFiling(null);
    }
  };

  return (
    <div className="pothole-list">
      <div className="list-header">
        <h2>🕳️ Detected Potholes ({total})</h2>
        <div className="filters">
          <select value={filter.severity} onChange={(e) => setFilter((f) => ({ ...f, severity: e.target.value }))}>
            <option value="">All Severities</option>
            <option value="minor">Minor</option>
            <option value="moderate">Moderate</option>
            <option value="severe">Severe</option>
          </select>
          <select value={filter.status} onChange={(e) => setFilter((f) => ({ ...f, status: e.target.value }))}>
            <option value="">All Statuses</option>
            <option value="detected">Detected</option>
            <option value="classified">Classified</option>
            <option value="complaint_filed">Complaint Filed</option>
            <option value="in_progress">In Progress</option>
            <option value="resolved">Resolved</option>
          </select>
        </div>
      </div>

      {loading ? (
        <div className="loading">Loading...</div>
      ) : potholes.length === 0 ? (
        <div className="empty">No potholes found. Upload an image to start detection.</div>
      ) : (
        <div className="pothole-table-wrapper">
          <table className="pothole-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Severity</th>
                <th>Status</th>
                <th>Location</th>
                <th>Depth</th>
                <th>Risk</th>
                <th>Detected</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {potholes.map((p) => (
                <tr
                  key={p.id}
                  className="pothole-row"
                  onClick={() => onSelect && onSelect(p)}
                >
                  <td>#{p.id}</td>
                  <td>
                    <span className={`badge ${SEVERITY_BADGE[p.severity]}`}>
                      {p.severity}
                    </span>
                  </td>
                  <td>
                    <span className="status-tag">{p.status.replace(/_/g, ' ')}</span>
                  </td>
                  <td className="location-cell">
                    <div>{p.highway_name || p.road_name || '–'}</div>
                    <div className="coords">
                      {p.latitude.toFixed(4)}, {p.longitude.toFixed(4)}
                    </div>
                  </td>
                  <td>{p.depth_cm ? `${p.depth_cm.toFixed(1)} cm` : '–'}</td>
                  <td>
                    <span className={`risk-badge ${getRiskClass(p.risk_score)}`}>
                      {p.risk_score ? p.risk_score.toFixed(0) : '–'}
                    </span>
                  </td>
                  <td>{new Date(p.detected_at).toLocaleDateString()}</td>
                  <td onClick={(e) => e.stopPropagation()}>
                    {p.status === 'detected' || p.status === 'classified' ? (
                      <button
                        className="btn-file"
                        disabled={filing === p.id}
                        onClick={() => handleFileComplaint(p)}
                      >
                        {filing === p.id ? '...' : 'File Complaint'}
                      </button>
                    ) : (
                      <span className="filed-tag">Filed</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Pagination */}
      <div className="pagination">
        <button disabled={page === 0} onClick={() => setPage((p) => p - 1)}>
          ← Prev
        </button>
        <span>
          Page {page + 1} / {Math.max(1, Math.ceil(total / LIMIT))}
        </span>
        <button
          disabled={(page + 1) * LIMIT >= total}
          onClick={() => setPage((p) => p + 1)}
        >
          Next →
        </button>
      </div>
    </div>
  );
};

function getRiskClass(score: number | null): string {
  if (!score) return '';
  if (score >= 75) return 'risk-critical';
  if (score >= 50) return 'risk-high';
  if (score >= 30) return 'risk-medium';
  return 'risk-low';
}

export default PotholeList;
