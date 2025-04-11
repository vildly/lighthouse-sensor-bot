import { useState } from 'react';
import ModelPerformanceChart from '../components/ModelPerformanceChart';

export default function ModelPerformancePage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 to-gray-800">
      <main className="container mx-auto px-4 py-8">
        <h1 className="text-3xl font-bold text-white mb-8">LLM Model Performance Dashboard</h1>
        
        <div className="mb-8">
          <ModelPerformanceChart />
        </div>
      </main>
    </div>
  );
} 