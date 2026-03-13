import React, { useEffect, useState } from 'react';
import { getAnalytics } from '../../services/api';
import { Analytics } from '../../types';
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
} from 'recharts';
import './Analytics.css';

const COLORS = ['#1a73e8', '#fbbc04', '#ea4335', '#34a853', '#8ab4f8', '#ff6d00'];

// Mock trend data (in production, fetch from /api/analytics/trends)
const TREND_DATA = [
  { month: 'Jan', detected: 12, filed: 10, resolved: 5 },
  { month: 'Feb', detected: 18, filed: 15, resolved: 9 },
  { month: 'Mar', detected: 24, filed: 22, resolved: 14 },
  { month: 'Apr', detected: 30, filed: 27, resolved: 19 },
  { month: 'May', detected: 28, filed: 26, resolved: 22 },
  { month: 'Jun', detected: 35, filed: 32, resolved: 25 },
];

const Analytics: React.FC = () => {
  const [analytics, setAnalytics] = useState<Analytics | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getAnalytics()
      .then(setAnalytics)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="loading">Loading analytics...</div>;

  return (
    <div className="analytics">
      <h2 className="section-title">📈 Analytics & Performance</h2>

      {/* Trend Chart */}
      <div className="analytics-card wide">
        <h3>Detection → Filing → Resolution Trend</h3>
        <ResponsiveContainer width="100%" height={280}>
          <AreaChart data={TREND_DATA}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="month" />
            <YAxis />
            <Tooltip />
            <Legend />
            <Area type="monotone" dataKey="detected" stackId="1" stroke="#1a73e8" fill="#8ab4f8" name="Detected" />
            <Area type="monotone" dataKey="filed" stackId="2" stroke="#fbbc04" fill="#fff176" name="Filed" />
            <Area type="monotone" dataKey="resolved" stackId="3" stroke="#34a853" fill="#a5d6a7" name="Resolved" />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      {/* Resolution Rate */}
      {analytics && (
        <div className="analytics-row">
          <div className="analytics-card">
            <h3>Severity Distribution</h3>
            <ResponsiveContainer width="100%" height={220}>
              <PieChart>
                <Pie
                  data={analytics.severity_breakdown}
                  cx="50%"
                  cy="50%"
                  innerRadius={50}
                  outerRadius={85}
                  dataKey="value"
                  label={({ name, percent }) =>
                    percent > 0 ? `${name} ${(percent * 100).toFixed(0)}%` : ''
                  }
                >
                  {analytics.severity_breakdown.map((_, i) => (
                    <Cell key={i} fill={COLORS[i % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </div>

          <div className="analytics-card">
            <h3>Complaint Status Overview</h3>
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={analytics.complaint_breakdown} layout="vertical">
                <XAxis type="number" />
                <YAxis type="category" dataKey="name" width={100} tick={{ fontSize: 11 }} />
                <Tooltip />
                <Bar dataKey="value" fill="#1a73e8" name="Count" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>

          <div className="analytics-card">
            <h3>Response Time (Mock)</h3>
            <ResponsiveContainer width="100%" height={220}>
              <LineChart data={TREND_DATA}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="month" />
                <YAxis unit=" days" />
                <Tooltip />
                <Legend />
                <Line
                  type="monotone"
                  dataKey="resolved"
                  stroke="#34a853"
                  name="Avg Days to Resolve"
                  dot={{ r: 4 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {/* KPI Table */}
      {analytics && (
        <div className="analytics-card wide">
          <h3>Key Performance Metrics</h3>
          <table className="kpi-table">
            <thead>
              <tr>
                <th>Metric</th>
                <th>Value</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td>Total Potholes Detected</td>
                <td>{analytics.summary.total_potholes}</td>
              </tr>
              <tr>
                <td>Total Complaints Filed</td>
                <td>{analytics.summary.total_complaints}</td>
              </tr>
              <tr>
                <td>Total Resolved &amp; Verified</td>
                <td>{analytics.summary.total_resolved}</td>
              </tr>
              <tr>
                <td>Resolution Rate</td>
                <td>{analytics.summary.resolution_rate}%</td>
              </tr>
              <tr>
                <td>Average Risk Score</td>
                <td>{analytics.summary.avg_risk_score}</td>
              </tr>
              <tr>
                <td>Automation Rate</td>
                <td>100%</td>
              </tr>
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};

export default Analytics;
