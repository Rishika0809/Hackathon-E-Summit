import React, { useEffect, useState } from 'react';
import { getAnalytics, getKPIs } from '../../services/api';
import { Analytics, KPI } from '../../types';
import {
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import './Dashboard.css';

const SEVERITY_COLORS: Record<string, string> = {
  Minor: '#34a853',
  Moderate: '#fbbc04',
  Severe: '#ea4335',
};

const STATUS_COLORS = ['#1a73e8', '#fbbc04', '#ea4335', '#34a853', '#8ab4f8', '#ff6d00', '#46bdc6'];

const Dashboard: React.FC = () => {
  const [analytics, setAnalytics] = useState<Analytics | null>(null);
  const [kpis, setKpis] = useState<KPI[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const load = async () => {
      try {
        const [a, k] = await Promise.all([getAnalytics(), getKPIs()]);
        setAnalytics(a);
        setKpis(k.kpis);
      } catch (err) {
        setError('Failed to load analytics. Is the backend running?');
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  if (loading) return <div className="loading">Loading dashboard...</div>;
  if (error) return <div className="error">{error}</div>;
  if (!analytics) return null;

  return (
    <div className="dashboard">
      <h2 className="section-title">📊 Dashboard Overview</h2>

      {/* KPI Cards */}
      <div className="kpi-grid">
        {kpis.map((kpi) => (
          <div key={kpi.label} className="kpi-card">
            <div className="kpi-value">
              {kpi.value}
              {kpi.unit}
            </div>
            <div className="kpi-label">{kpi.label}</div>
            {kpi.description && <div className="kpi-desc">{kpi.description}</div>}
          </div>
        ))}
      </div>

      {/* Summary Stats */}
      <div className="stats-grid">
        <div className="stat-card">
          <span className="stat-number">{analytics.summary.total_potholes}</span>
          <span className="stat-label">Total Potholes</span>
        </div>
        <div className="stat-card">
          <span className="stat-number">{analytics.summary.total_complaints}</span>
          <span className="stat-label">Complaints Filed</span>
        </div>
        <div className="stat-card">
          <span className="stat-number">{analytics.summary.total_resolved}</span>
          <span className="stat-label">Resolved</span>
        </div>
        <div className="stat-card">
          <span className="stat-number">{analytics.summary.resolution_rate}%</span>
          <span className="stat-label">Resolution Rate</span>
        </div>
        <div className="stat-card">
          <span className="stat-number">{analytics.summary.avg_risk_score}</span>
          <span className="stat-label">Avg Risk Score</span>
        </div>
      </div>

      {/* Charts Row */}
      <div className="charts-row">
        {/* Severity Pie Chart */}
        <div className="chart-card">
          <h3>Severity Distribution</h3>
          <ResponsiveContainer width="100%" height={250}>
            <PieChart>
              <Pie
                data={analytics.severity_breakdown}
                cx="50%"
                cy="50%"
                outerRadius={80}
                dataKey="value"
                label={({ name, value }) => `${name}: ${value}`}
              >
                {analytics.severity_breakdown.map((entry, index) => (
                  <Cell
                    key={`cell-${index}`}
                    fill={SEVERITY_COLORS[entry.name] || '#8884d8'}
                  />
                ))}
              </Pie>
              <Tooltip />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        </div>

        {/* Status Bar Chart */}
        <div className="chart-card">
          <h3>Status Breakdown</h3>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={analytics.status_breakdown}>
              <XAxis dataKey="name" tick={{ fontSize: 10 }} angle={-30} textAnchor="end" height={50} />
              <YAxis allowDecimals={false} />
              <Tooltip />
              <Bar dataKey="value" name="Count">
                {analytics.status_breakdown.map((_, index) => (
                  <Cell key={index} fill={STATUS_COLORS[index % STATUS_COLORS.length]} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Complaint Status Chart */}
        <div className="chart-card">
          <h3>Complaint Status</h3>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={analytics.complaint_breakdown}>
              <XAxis dataKey="name" tick={{ fontSize: 10 }} angle={-30} textAnchor="end" height={60} />
              <YAxis allowDecimals={false} />
              <Tooltip />
              <Bar dataKey="value" fill="#1a73e8" name="Complaints" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
