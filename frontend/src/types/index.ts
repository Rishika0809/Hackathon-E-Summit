// Core types for the Pothole Intelligence System

export type Severity = 'minor' | 'moderate' | 'severe';

export type PotholeStatus =
  | 'detected'
  | 'classified'
  | 'complaint_filed'
  | 'in_progress'
  | 'resolved'
  | 'verified'
  | 'escalated';

export type ComplaintStatus =
  | 'pending'
  | 'filed'
  | 'acknowledged'
  | 'in_progress'
  | 'resolved'
  | 'closed'
  | 'escalated_l1'
  | 'escalated_l2'
  | 'publicly_flagged'
  | 'failed';

export interface Pothole {
  id: number;
  latitude: number;
  longitude: number;
  severity: Severity;
  status: PotholeStatus;
  length_cm: number | null;
  width_cm: number | null;
  depth_cm: number | null;
  area_sqm: number | null;
  road_name: string | null;
  highway_name: string | null;
  km_marker: string | null;
  address: string | null;
  state: string | null;
  district: string | null;
  image_url: string | null;
  thumbnail_url: string | null;
  source_type: string | null;
  confidence_score: number | null;
  risk_score: number | null;
  priority_rank: number | null;
  detected_at: string;
  updated_at: string;
  complaints?: Complaint[];
}

export interface Complaint {
  id: number;
  pothole_id: number;
  portal: string;
  complaint_id: string | null;
  status: ComplaintStatus;
  form_data: Record<string, unknown> | null;
  portal_response: Record<string, unknown> | null;
  filed_at: string | null;
  last_checked: string | null;
  resolved_at: string | null;
  escalation_level: number;
  escalated_at: string | null;
  notes: string | null;
  created_at: string;
  updated_at: string;
}

export interface Resolution {
  id: number;
  complaint_id: number;
  resolved_at: string | null;
  verified_at: string | null;
  verification_image_url: string | null;
  before_image_url: string | null;
  after_image_url: string | null;
  similarity_score: number | null;
  repair_quality: string | null;
  is_verified: boolean;
  verification_notes: string | null;
  pothole_still_present: boolean | null;
}

export interface AnalyticsSummary {
  total_potholes: number;
  total_complaints: number;
  total_resolved: number;
  resolution_rate: number;
  avg_risk_score: number;
}

export interface ChartDataPoint {
  name: string;
  value: number;
}

export interface Analytics {
  summary: AnalyticsSummary;
  severity_breakdown: ChartDataPoint[];
  status_breakdown: ChartDataPoint[];
  complaint_breakdown: ChartDataPoint[];
}

export interface KPI {
  label: string;
  value: number;
  unit: string;
  description?: string;
}

export interface HeatmapPoint {
  lat: number;
  lon: number;
  intensity: number;
  severity: Severity;
  pothole_id: number;
}

export interface PaginatedPotholes {
  total: number;
  skip: number;
  limit: number;
  potholes: Pothole[];
}

export interface PaginatedComplaints {
  total: number;
  skip: number;
  limit: number;
  complaints: Complaint[];
}
