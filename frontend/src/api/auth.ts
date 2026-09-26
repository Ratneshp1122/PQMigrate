import client from './client';
import { User } from '@/types';

export const login = async (email: string, password: string) => {
  const { data } = await client.post('/auth/login', { email, password });
  return data;
};

export const register = async (email: string, password: string) => {
  const { data } = await client.post('/auth/register', { email, password });
  return data;
};

export const getMe = async () => {
  const { data } = await client.get<User>('/auth/me');
  return data;
};
