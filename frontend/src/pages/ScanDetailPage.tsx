import { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { Download, RefreshCw, Undo } from 'lucide-react';
import Badge from '@/components/Badge';
import { getScan } from '@/api/scans';
import { applyPatch, rollbackPatch } from '@/api/patch';
import { ScanRecord, Finding } from '@/types';

export default function ScanDetailPage() {
  const { id } = useParams();
  const [data, setData] = useState<{ scan: ScanRecord; findings: Finding[] } | null>(null);
  const [loadingAction, setLoadingAction] = useState(false);

  const loadData = async () => {
    if (id) {
      try {
        const res = await getScan(id);
        setData(res);
      } catch (e) {}
    }
  };

  useEffect(() => {
    loadData();
  }, [id]);

  if (!data) return <div className="p-8">Loading...</div>;

  const { scan, findings } = data;

  const handleAction = async (action: 'patch' | 'rollback') => {
    if (!id) return;
    setLoadingAction(true);
    try {
      if (action === 'patch') await applyPatch(id);
      else await rollbackPatch(id);
      await loadData();
    } catch (e) {
      alert('Action failed');
    } finally {
      setLoadingAction(false);
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'AUTO-PATCH': return <Badge variant="safe">AUTO-PATCH</Badge>;
      case 'ABSTAINED': return <Badge variant="abstain">ABSTAINED</Badge>;
      case 'MANUAL': return <Badge variant="high">MANUAL</Badge>;
      default: return <Badge variant="pending">{status}</Badge>;
    }
  };

  return (
    <div className="p-8 space-y-6">
      <div className="flex justify-between items-start">
        <div>
          <div className="flex items-center space-x-3 mb-2">
            <h1 className="text-2xl font-bold">{scan.projectName}</h1>
            <Badge variant={scan.status === 'COMPLETE' ? 'safe' : 'pending'}>{scan.status}</Badge>
          </div>
          <p className="text-gray-400">{scan.githubUrl}</p>
          <div className="mt-2 text-sm text-gray-500">
            Files Scanned: {scan.filesScanned} | Total Findings: {scan.totalFindings}
          </div>
        </div>
        <div className="flex space-x-3">
          <button 
            onClick={() => handleAction('patch')}
            disabled={loadingAction || scan.status !== 'COMPLETE'}
            className="flex items-center px-4 py-2 bg-green-600 hover:bg-green-700 disabled:opacity-50 text-white rounded-md text-sm font-medium transition-colors"
          >
            <RefreshCw className="w-4 h-4 mr-2" /> Apply Auto-Patch
          </button>
          <button 
            onClick={() => handleAction('rollback')}
            disabled={loadingAction || scan.status !== 'COMPLETE'}
            className="flex items-center px-4 py-2 bg-red-600 hover:bg-red-700 disabled:opacity-50 text-white rounded-md text-sm font-medium transition-colors"
          >
            <Undo className="w-4 h-4 mr-2" /> Rollback
          </button>
          <button 
            className="flex items-center px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded-md text-sm font-medium transition-colors"
            onClick={() => alert('Download JSON unimplemented')}
          >
            <Download className="w-4 h-4 mr-2" /> Export JSON
          </button>
        </div>
      </div>

      <div className="bg-gray-900 border border-gray-800 rounded-lg overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="bg-gray-800/50 text-gray-400">
              <tr>
                <th className="px-6 py-3 font-medium">File</th>
                <th className="px-6 py-3 font-medium">Primitive</th>
                <th className="px-6 py-3 font-medium">Role</th>
                <th className="px-6 py-3 font-medium">Operation</th>
                <th className="px-6 py-3 font-medium">Target</th>
                <th className="px-6 py-3 font-medium">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-800">
              {findings.map((f: any) => (
                <tr key={f.id} className="hover:bg-gray-800/50 transition-colors">
                  <td className="px-6 py-4 font-mono text-xs text-gray-300">
                    {f.filePath.split('/').pop()}:{f.lineNumber}
                  </td>
                  <td className="px-6 py-4 font-medium text-red-400">{f.primitiveName}</td>
                  <td className="px-6 py-4">{f.role}</td>
                  <td className="px-6 py-4">{f.operation}</td>
                  <td className="px-6 py-4 font-medium text-green-400">{f.targetAlgorithm || '-'}</td>
                  <td className="px-6 py-4">{getStatusBadge(f.status)}</td>
                </tr>
              ))}
              {findings.length === 0 && (
                <tr>
                  <td colSpan={6} className="px-6 py-8 text-center text-gray-500">
                    No findings detected.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
