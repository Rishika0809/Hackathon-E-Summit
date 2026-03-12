import React, { useState } from 'react';
import Dashboard from './components/Dashboard/Dashboard';
import MapView from './components/MapView/MapView';
import PotholeList from './components/PotholeList/PotholeList';
import Analytics from './components/Analytics/Analytics';
import ComplaintTracker from './components/ComplaintTracker/ComplaintTracker';
import { Pothole } from './types';
import { detectPotholes } from './services/api';
import './App.css';

type Tab = 'dashboard' | 'map' | 'potholes' | 'analytics' | 'complaints';

const TABS: { id: Tab; label: string; icon: string }[] = [
  { id: 'dashboard', label: 'Dashboard', icon: '📊' },
  { id: 'map', label: 'Map View', icon: '🗺️' },
  { id: 'potholes', label: 'Potholes', icon: '🕳️' },
  { id: 'complaints', label: 'Complaints', icon: '📋' },
  { id: 'analytics', label: 'Analytics', icon: '📈' },
];

const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<Tab>('dashboard');
  const [selectedPothole, setSelectedPothole] = useState<Pothole | null>(null);
  const [uploading, setUploading] = useState(false);
  const [uploadMsg, setUploadMsg] = useState('');

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploading(true);
    setUploadMsg('');
    try {
      const result = await detectPotholes(file);
      if (result.detected) {
        setUploadMsg(`✅ Detected ${result.count} pothole(s)! Switching to Potholes tab.`);
        setActiveTab('potholes');
      } else {
        setUploadMsg('ℹ️ No potholes detected in this image.');
      }
    } catch {
      setUploadMsg('❌ Upload failed. Is the backend running?');
    } finally {
      setUploading(false);
      e.target.value = '';
    }
  };

  const handlePotholeSelect = (p: Pothole) => {
    setSelectedPothole(p);
    setActiveTab('map');
  };

  return (
    <div className="app">
      {/* Header */}
      <header className="app-header">
        <div className="header-brand">
          <span className="header-icon">🛣️</span>
          <div>
            <h1>Pothole Intelligence System</h1>
            <p>Autonomous Detection · Complaint Filing · Resolution Tracking</p>
          </div>
        </div>
        <div className="header-upload">
          <label className={`upload-btn ${uploading ? 'loading' : ''}`}>
            {uploading ? '⏳ Detecting...' : '📷 Upload Image'}
            <input
              type="file"
              accept="image/*"
              hidden
              onChange={handleFileUpload}
              disabled={uploading}
            />
          </label>
        </div>
      </header>

      {uploadMsg && (
        <div className={`upload-banner ${uploadMsg.startsWith('✅') ? 'success' : uploadMsg.startsWith('❌') ? 'error' : 'info'}`}>
          {uploadMsg}
        </div>
      )}

      {/* Navigation */}
      <nav className="app-nav">
        {TABS.map((tab) => (
          <button
            key={tab.id}
            className={`nav-tab ${activeTab === tab.id ? 'active' : ''}`}
            onClick={() => setActiveTab(tab.id)}
          >
            {tab.icon} {tab.label}
          </button>
        ))}
      </nav>

      {/* Content */}
      <main className="app-content">
        {activeTab === 'dashboard' && <Dashboard />}
        {activeTab === 'map' && <MapView selectedPothole={selectedPothole} />}
        {activeTab === 'potholes' && <PotholeList onSelect={handlePotholeSelect} />}
        {activeTab === 'complaints' && <ComplaintTracker />}
        {activeTab === 'analytics' && <Analytics />}
      </main>

      <footer className="app-footer">
        Autonomous Pothole Intelligence System · E-Summit Hackathon 2024
      </footer>
    </div>
  );
};

export default App;
