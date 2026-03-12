import axios from 'axios';
import {
  Analytics,
  Complaint,
  HeatmapPoint,
  KPI,
  PaginatedComplaints,
  PaginatedPotholes,
  Pothole,
  Resolution,
} from '../types';

const BASE_URL = process.env.REACT_APP_API_URL || '';

const api = axios.create({
  baseURL: BASE_URL,
  headers: { 'Content-Type': 'application/json' },
});

// Detection
export async function detectPotholes(
  file: File,
  latitude?: number,
  longitude?: number,
  sourceType: string = 'dashcam'
): Promise<{ detected: boolean; count: number; potholes: Pothole[] }> {
  const form = new FormData();
  form.append('file', file);
  if (latitude !== undefined) form.append('latitude', String(latitude));
  if (longitude !== undefined) form.append('longitude', String(longitude));
  form.append('source_type', sourceType);
  const resp = await api.post('/api/detect/', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return resp.data;
}

// Potholes
export async function getPotholes(params?: {
  severity?: string;
  status?: string;
  state?: string;
  skip?: number;
  limit?: number;
}): Promise<PaginatedPotholes> {
  const resp = await api.get('/api/potholes/', { params });
  return resp.data;
}

export async function getPothole(id: number): Promise<Pothole> {
  const resp = await api.get(`/api/potholes/${id}`);
  return resp.data;
}

export async function getHeatmapData(): Promise<{ points: HeatmapPoint[]; total: number }> {
  const resp = await api.get('/api/potholes/heatmap/data');
  return resp.data;
}

export async function getPriorityQueue(): Promise<{ total: number; queue: Pothole[] }> {
  const resp = await api.get('/api/potholes/priority/queue');
  return resp.data;
}

// Complaints
export async function fileComplaint(potholeId: number, notes?: string): Promise<Complaint> {
  const resp = await api.post('/api/complaints/', { pothole_id: potholeId, notes });
  return resp.data;
}

export async function getComplaints(params?: {
  status?: string;
  pothole_id?: number;
  skip?: number;
  limit?: number;
}): Promise<PaginatedComplaints> {
  const resp = await api.get('/api/complaints/', { params });
  return resp.data;
}

export async function getComplaint(id: number): Promise<Complaint> {
  const resp = await api.get(`/api/complaints/${id}`);
  return resp.data;
}

export async function verifyResolution(
  complaintId: number,
  verificationImageUrl?: string
): Promise<Resolution> {
  const resp = await api.post(`/api/complaints/${complaintId}/verify`, null, {
    params: { verification_image_url: verificationImageUrl },
  });
  return resp.data;
}

export async function runEscalationCheck(): Promise<{ message: string; summary: Record<string, number> }> {
  const resp = await api.post('/api/complaints/escalate-all');
  return resp.data;
}

// Analytics
export async function getAnalytics(): Promise<Analytics> {
  const resp = await api.get('/api/analytics/');
  return resp.data;
}

export async function getKPIs(): Promise<{ kpis: KPI[] }> {
  const resp = await api.get('/api/analytics/kpis');
  return resp.data;
}
