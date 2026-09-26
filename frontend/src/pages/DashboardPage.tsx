import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { PieChart, Pie, Cell, Tooltip, BarChart, Bar, XAxis, YAxis, ResponsiveContainer } from 'recharts';
import KpiCard from '@/components/KpiCard';
import Badge from '@/components/Badge';
import { getStats, getRecent } from '@/api/dashboard';
import { DashboardStats, ScanRecord } from '@/types';

export default function DashboardPage() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [recent, setRecent] = useState<ScanRecord[]>([]);

  useEffect(() => {
    getStats().then(setStats).catch(() => {});
    getRecent().then(setRecent).catch(() => {});
  }, []);

  if (!stats) return <div className="p-8">Loading...</div>;

  const pieData = [
    { name: 'Critical', value: stats.criticalCount, color: '#ef4444' },
    { name: 'Patched', value: stats.patchedCount, color: '#10b981' },
    { name: 'Abstained', value: stats.abstentionCount, color: '#8b5cf6' },
  ];

  return (
    <div className="p-8 space-y-8">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold">Dashboard</h1>
        <Link to="/scans/new" className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-md text-sm font-medium">
          New Scan
        </Link>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <KpiCard title="Total Scans" value={stats.totalScans} borderColor="blue" />
        <KpiCard title="Total Findings" value={stats.totalFindings} borderColor="red" />
        <KpiCard title="Auto-Patchable" value={stats.patchedCount} borderColor="green" />
        <KpiCard title="Manual Review" value={stats.abstentionCount} borderColor="purple" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-gray-900 border border-gray-800 rounded-lg p-6">
          <h2 className="text-lg font-medium mb-4">Findings Distribution</h2>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie data={pieData} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={80}>
                  {pieData.map((entry, i) => <Cell key={i} fill={entry.color} />)}
                </Pie>
                <Tooltip contentStyle={{ backgroundColor: '#1f2937', border: 'none' }} />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>
        <div className="bg-gray-900 border border-gray-800 rounded-lg p-6">
          <h2 className="text-lg font-medium mb-4">Top Vulnerable Primitives</h2>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={stats.topVulnerablePrimitives} layout="vertical" margin={{ left: 20 }}>
                <XAxis type="number" hide />
                <YAxis dataKey="name" type="category" stroke="#9ca3af" width={80} />
                <Tooltip contentStyle={{ backgroundColor: '#1f2937', border: 'none' }} />
                <Bar dataKey="count" fill="#3b82f6" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      <div className="bg-gray-900 border border-gray-800 rounded-lg">
        <div className="p-6 border-b border-gray-800">
          <h2 className="text-lg font-medium">Recent Scans</h2>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="bg-gray-800/50 text-gray-400">
              <tr>
                <th className="px-6 py-3 font-medium">Project</th>
                <th className="px-6 py-3 font-medium">GitHub URL</th>
                <th className="px-6 py-3 font-medium">Status</th>
                <th className="px-6 py-3 font-medium">Findings</th>
                <th className="px-6 py-3 font-medium">Date</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-800">
              {recent.map((scan: any) => (
                <tr key={scan.id} className="hover:bg-gray-800/50 transition-colors">
                  <td className="px-6 py-4 font-medium text-blue-400">
                    <Link to={`/scans/${scan.id}`}>{scan.projectName}</Link>
                  </td>
                  <td className="px-6 py-4 text-gray-400">{scan.githubUrl}</td>
                  <td className="px-6 py-4">
                    <Badge variant={
                      scan.status === 'COMPLETE' ? 'safe' :
                      scan.status === 'FAILED' ? 'critical' : 'pending'
                    }>{scan.status}</Badge>
                  </td>
                  <td className="px-6 py-4">{scan.totalFindings}</td>
                  <td className="px-6 py-4 text-gray-400">{new Date(scan.createdAt).toLocaleDateString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
