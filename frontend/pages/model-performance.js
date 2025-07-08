import { useState } from 'react';
import ModelPerformanceChart from '../components/ModelPerformanceChart';
import React from 'react';
import GDPRBanner from '../components/GDPRBanner';

export default function ModelPerformancePage() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  
  const chartRef = React.useRef();
  
  const refreshData = async () => {
    try {
      setLoading(true);
      if (chartRef.current) {
        await chartRef.current.refreshData();
      }
    } catch (err) {
      console.error('Error refreshing data:', err);
      setError('Failed to refresh data');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 to-gray-800">
      <GDPRBanner />
      <main className="container mx-auto px-4 py-8">
        <div className="flex justify-between items-center mb-4">
          <h1 className="text-3xl font-bold text-white">LLM Model Performance Dashboard</h1>
          <button 
            onClick={refreshData}
            className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-md"
            disabled={loading}
          >
            {loading ? 'Refreshing...' : 'Refresh Data'}
          </button>
        </div>
        
        <div className="mb-8">
          <ModelPerformanceChart ref={chartRef} setPageLoading={setLoading} />
        </div>
      </main>
    </div>
  );
} 