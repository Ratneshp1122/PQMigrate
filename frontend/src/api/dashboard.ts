import client from './client';
import { DashboardStats, ScanRecord } from '@/types';

export const getStats = async () => {
  const { data } = await client.get<DashboardStats>('/dashboard/stats');
  return data;
};

export const getRecent = async () => {
  const { data } = await client.get<ScanRecord[]>('/dashboard/recent');
  return data;
};
