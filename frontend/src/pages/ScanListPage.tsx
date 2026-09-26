import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Trash2 } from 'lucide-react';
import Badge from '@/components/Badge';
import { getScans, deleteScan } from '@/api/scans';
import { ScanRecord } from '@/types';

export default function ScanListPage() {
  const [scans, setScans] = useState<ScanRecord[]>([]);

  const loadScans = async () => {
    try {
      const data = await getScans();
      setScans(data);
    } catch (err) {}
  };

  useEffect(() => {
    loadScans();
  }, []);

  const handleDelete = async (id: number) => {
    if (confirm('Are you sure you want to delete this scan?')) {
      await deleteScan(id);
      loadScans();
    }
  };

  return (
    <div className="p-8 space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold">All Scans</h1>
        <Link to="/scans/new" className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-md text-sm font-medium">
          New Scan
        </Link>
      </div>

      <div className="bg-gray-900 border border-gray-800 rounded-lg overflow-hidden">
        <table className="w-full text-left text-sm">
          <thead className="bg-gray-800/50 text-gray-400">
            <tr>
              <th className="px-6 py-3 font-medium">Project</th>
              <th className="px-6 py-3 font-medium">Status</th>
              <th className="px-6 py-3 font-medium">Files Scanned</th>
              <th className="px-6 py-3 font-medium">Findings</th>
              <th className="px-6 py-3 font-medium">Date</th>
              <th className="px-6 py-3 font-medium text-right">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-800">
            {scans.map((scan: any) => (
              <tr key={scan.id} className="hover:bg-gray-800/50 transition-colors">
                <td className="px-6 py-4 font-medium text-blue-400">
                  <Link to={`/scans/${scan.id}`}>{scan.projectName}</Link>
                </td>
                <td className="px-6 py-4">
                  <Badge variant={
                    scan.status === 'COMPLETE' ? 'safe' :
                    scan.status === 'FAILED' ? 'critical' : 'pending'
                  }>{scan.status}</Badge>
                </td>
                <td className="px-6 py-4">{scan.filesScanned}</td>
                <td className="px-6 py-4">{scan.totalFindings}</td>
                <td className="px-6 py-4 text-gray-400">{new Date(scan.createdAt).toLocaleDateString()}</td>
                <td className="px-6 py-4 text-right">
                  <button 
                    onClick={() => handleDelete(scan.id)}
                    className="text-red-400 hover:text-red-300 transition-colors"
                  >
                    <Trash2 className="w-4 h-4 inline" />
                  </button>
                </td>
              </tr>
            ))}
            {scans.length === 0 && (
              <tr>
                <td colSpan={6} className="px-6 py-8 text-center text-gray-500">
                  No scans found. Create a new one!
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
