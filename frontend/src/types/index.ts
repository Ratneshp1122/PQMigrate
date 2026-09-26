export interface User {
  id: number;
  email: string;
  role: string;
}

export interface ScanRecord {
  id: number;
  projectName: string;
  githubUrl: string;
  status: 'PENDING' | 'SCANNING' | 'COMPLETE' | 'FAILED';
  filesScanned: number;
  totalFindings: number;
  createdAt: string;
  completedAt: string | null;
}

export interface Finding {
  id: number;
  primitiveName: string;
  filePath: string;
  lineNumber: number;
  role: string;
  operation: string;
  status: string;
  confidence: string;
  detectionType: string;
  targetAlgorithm: string;
  targetStandard: string;
  patchAvailable: boolean;
  requiresManualIntervention: boolean;
  interventionReason: string | null;
}

export interface DashboardStats {
  totalScans: number;
  totalFindings: number;
  criticalCount: number;
  abstentionCount: number;
  patchedCount: number;
  topVulnerablePrimitives: { name: string; count: number }[];
}
