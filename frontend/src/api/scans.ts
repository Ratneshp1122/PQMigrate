import client from './client';
import { ScanRecord, Finding } from '@/types';

export const getScans = async () => {
  const { data } = await client.get<ScanRecord[]>('/scans');
  return data;
};

export const getScan = async (id: string | number) => {
  const { data } = await client.get<{ scan: ScanRecord; findings: Finding[] }>(`/scans/${id}`);
  return data;
};

export const createScan = async (githubUrl: string) => {
  const { data } = await client.post<ScanRecord>('/scans', { githubUrl });
  return data;
};

export const deleteScan = async (id: string | number) => {
  await client.delete(`/scans/${id}`);
};
