import client from './client';

export const applyPatch = async (scanId: string | number) => {
  const { data } = await client.post(`/patch/${scanId}`);
  return data;
};

export const rollbackPatch = async (scanId: string | number) => {
  const { data } = await client.post(`/patch/${scanId}/rollback`);
  return data;
};
