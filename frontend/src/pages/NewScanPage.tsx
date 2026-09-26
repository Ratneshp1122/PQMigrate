import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Loader2 } from 'lucide-react';
import { createScan } from '@/api/scans';

export default function NewScanPage() {
  const [url, setUrl] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    try {
      const scan = await createScan(url);
      navigate(`/scans/${scan.id}`);
    } catch (err: any) {
      setError(err.response?.data?.message || 'Failed to start scan');
      setLoading(false);
    }
  };

  return (
    <div className="p-8 max-w-2xl mx-auto mt-12">
      <div className="bg-gray-900 border border-gray-800 rounded-lg p-6">
        <h1 className="text-2xl font-bold mb-2">New Repository Scan</h1>
        <p className="text-gray-400 mb-6">Enter a GitHub repository URL or format like `owner/repo` to begin scanning for cryptographic primitives.</p>

        {error && <div className="mb-4 p-3 bg-red-900/50 border border-red-500 text-red-200 rounded">{error}</div>}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1">GitHub URL or Repository</label>
            <input 
              type="text" 
              required
              placeholder="e.g. paramiko/paramiko or https://github.com/..."
              className="w-full px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg focus:ring-2 focus:ring-blue-500 text-gray-100"
              value={url}
              onChange={e => setUrl(e.target.value)}
              disabled={loading}
            />
          </div>
          <button 
            type="submit"
            disabled={loading}
            className="flex items-center justify-center w-full py-2 px-4 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white font-medium rounded-lg transition-colors"
          >
            {loading ? <><Loader2 className="w-5 h-5 mr-2 animate-spin" /> Scanning...</> : 'Start Scan'}
          </button>
        </form>
      </div>
    </div>
  );
}
