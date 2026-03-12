import React, { useEffect, useState } from 'react';
import { getComplaints, verifyResolution, runEscalationCheck } from '../../services/api';
import { Complaint } from '../../types';
import './ComplaintTracker.css';

const STATUS_COLOR: Record<string, string> = {
  pending: '#9e9e9e',
  filed: '#1a73e8',
  acknowledged: '#0d47a1',
  in_progress: '#fbbc04',
  resolved: '#34a853',
  closed: '#4caf50',
  escalated_l1: '#ff6d00',
  escalated_l2: '#e53935',
  publicly_flagged: '#7b1fa2',
  failed: '#b71c1c',
};

const ComplaintTracker: React.FC = () => {
  const [complaints, setComplaints] = useState<Complaint[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('');
  const [page, setPage] = useState(0);
  const [running, setRunning] = useState(false);
  const [escalationMsg, setEscalationMsg] = useState('');
  const LIMIT = 20;

  const load = async () => {
    setLoading(true);
    try {
      const resp = await getComplaints({
        status: filter || undefined,
        skip: page * LIMIT,
        limit: LIMIT,
      });
      setComplaints(resp.complaints);
      setTotal(resp.total);
    } catch {
      // handle
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, [filter, page]); // eslint-disable-line

  const handleVerify = async (c: Complaint) => {
    try {
      await verifyResolution(c.id);
      await load();
      alert(`Resolution verified for Complaint #${c.id}`);
    } catch {
      alert('Verification failed.');
    }
  };

  const handleEscalateAll = async () => {
    setRunning(true);
    try {
      const result = await runEscalationCheck();
      setEscalationMsg(
        `Checked: ${result.summary.checked}, L1: ${result.summary.escalated_l1}, L2: ${result.summary.escalated_l2}, Flagged: ${result.summary.flagged}`
      );
      await load();
    } catch {
      setEscalationMsg('Escalation check failed.');
    } finally {
      setRunning(false);
    }
  };

  return (
    <div className="complaint-tracker">
      <div className="tracker-header">
        <h2>📋 Complaint Tracker ({total})</h2>
        <div className="tracker-actions">
          <select value={filter} onChange={(e) => { setFilter(e.target.value); setPage(0); }}>
            <option value="">All Statuses</option>
            <option value="filed">Filed</option>
            <option value="acknowledged">Acknowledged</option>
            <option value="in_progress">In Progress</option>
            <option value="resolved">Resolved</option>
            <option value="escalated_l1">Escalated L1</option>
            <option value="escalated_l2">Escalated L2</option>
            <option value="publicly_flagged">Publicly Flagged</option>
          </select>
          <button className="btn-escalate" onClick={handleEscalateAll} disabled={running}>
            {running ? 'Checking...' : '⚡ Run Escalation Check'}
          </button>
        </div>
      </div>

      {escalationMsg && (
        <div className="escalation-result">✅ {escalationMsg}</div>
      )}

      {loading ? (
        <div className="loading">Loading complaints...</div>
      ) : complaints.length === 0 ? (
        <div className="empty">No complaints found. File a complaint from the Potholes tab.</div>
      ) : (
        <div className="table-wrapper">
          <table className="complaint-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Pothole</th>
                <th>Tracking ID</th>
                <th>Portal</th>
                <th>Status</th>
                <th>Escalation</th>
                <th>Filed</th>
                <th>Last Checked</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {complaints.map((c) => (
                <tr key={c.id}>
                  <td>#{c.id}</td>
                  <td>#{c.pothole_id}</td>
                  <td className="tracking-id">{c.complaint_id || '–'}</td>
                  <td>{c.portal?.replace('_', ' ').toUpperCase()}</td>
                  <td>
                    <span
                      className="status-dot"
                      style={{ background: STATUS_COLOR[c.status] || '#9e9e9e' }}
                    />
                    <span className="status-text">{c.status.replace(/_/g, ' ')}</span>
                  </td>
                  <td>
                    {c.escalation_level > 0 ? (
                      <span className="escalation-badge">L{c.escalation_level}</span>
                    ) : '–'}
                  </td>
                  <td>{c.filed_at ? new Date(c.filed_at).toLocaleDateString() : '–'}</td>
                  <td>{c.last_checked ? new Date(c.last_checked).toLocaleDateString() : '–'}</td>
                  <td>
                    {(c.status === 'in_progress' || c.status === 'acknowledged') && (
                      <button className="btn-verify" onClick={() => handleVerify(c)}>
                        Verify
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <div className="pagination">
        <button disabled={page === 0} onClick={() => setPage((p) => p - 1)}>← Prev</button>
        <span>Page {page + 1} / {Math.max(1, Math.ceil(total / LIMIT))}</span>
        <button disabled={(page + 1) * LIMIT >= total} onClick={() => setPage((p) => p + 1)}>Next →</button>
      </div>
    </div>
  );
};

export default ComplaintTracker;
