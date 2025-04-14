import React, { useState, useEffect } from 'react';
import { 
  Chart as ChartJS, 
  CategoryScale, 
  LinearScale, 
  BarElement, 
  Title, 
  Tooltip, 
  Legend, 
  RadialLinearScale,
  PointElement,
  LineElement,
  Filler
} from 'chart.js';
import { Bar, Radar } from 'react-chartjs-2';

ChartJS.register(
  CategoryScale, 
  LinearScale, 
  BarElement, 
  RadialLinearScale,
  PointElement,
  LineElement,
  Filler,
  Title, 
  Tooltip, 
  Legend
);

const COLORS = [
  'rgba(31, 119, 180, 0.8)',
  'rgba(255, 127, 14, 0.8)',
  'rgba(44, 160, 44, 0.8)',
  'rgba(214, 39, 40, 0.8)',
  'rgba(148, 103, 189, 0.8)',
  'rgba(140, 86, 75, 0.8)',
  'rgba(227, 119, 194, 0.8)',
  'rgba(127, 127, 127, 0.8)',
  'rgba(188, 189, 34, 0.8)',
  'rgba(23, 190, 207, 0.8)'
];

export default function ModelPerformanceChart() {
  const [performanceData, setPerformanceData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedMetric, setSelectedMetric] = useState('avg_factual_correctness');
  const [chartType, setChartType] = useState('bar');
  const [modelTypeFilter, setModelTypeFilter] = useState(null);
  
  useEffect(() => {
    async function fetchData() {
      try {
        setLoading(true);
        
        const params = new URLSearchParams();
        if (modelTypeFilter) {
          params.append('type', modelTypeFilter);
        }
        
        const response = await fetch(`/api/model-performance?${params.toString()}`);
        
        if (!response.ok) {
          throw new Error(`Error fetching model performance: ${response.statusText}`);
        }
        
        const data = await response.json();
        setPerformanceData(data);
        setError(null);
      } catch (err) {
        console.error('Error fetching model performance:', err);
        setError('Failed to load model performance data');
      } finally {
        setLoading(false);
      }
    }
    
    fetchData();
  }, [modelTypeFilter]);

  const handleMetricChange = (e) => {
    setSelectedMetric(e.target.value);
  };

  const handleChartTypeChange = (e) => {
    setChartType(e.target.value);
  };

  const handleModelTypeChange = (e) => {
    setModelTypeFilter(e.target.value === 'all' ? null : e.target.value);
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-100 border-l-4 border-red-500 text-red-700 p-4 rounded">
        <p>{error}</p>
      </div>
    );
  }

  if (!performanceData || !performanceData.data || performanceData.data.length === 0) {
    return (
      <div className="bg-yellow-100 border-l-4 border-yellow-500 text-yellow-700 p-4 rounded">
        <p>No performance data available.</p>
      </div>
    );
  }

  // Get the corresponding stddev field for a metric
  const getStdDevField = (metricField) => {
    return metricField.replace('avg_', 'stddev_');
  };

  // Prepare bar chart data
  const prepareBarChartData = () => {
    const modelNames = performanceData.data.map(model => model.model_name.split('/')[1]);
    
    return {
      labels: modelNames,
      datasets: [{
        label: performanceData.metrics.find(m => m.id === selectedMetric)?.name || selectedMetric,
        data: performanceData.data.map(model => model[selectedMetric] || 0),
        backgroundColor: modelNames.map((_, i) => COLORS[i % COLORS.length]),
        borderColor: modelNames.map((_, i) => COLORS[i % COLORS.length].replace('0.8', '1')),
        borderWidth: 1
      }]
    };
  };

  // Prepare radar chart data for comparing models
  const prepareRadarChartData = () => {
    const metricIds = performanceData.metrics.map(m => m.id);
    const metricLabels = performanceData.metrics.map(m => m.name);
    
    return {
      labels: metricLabels,
      datasets: performanceData.data.map((model, idx) => ({
        label: model.model_name.split('/')[1],
        data: metricIds.map(metricId => model[metricId] || 0),
        backgroundColor: COLORS[idx % COLORS.length].replace('0.8', '0.2'),
        borderColor: COLORS[idx % COLORS.length].replace('0.8', '1'),
        borderWidth: 2,
        pointBackgroundColor: COLORS[idx % COLORS.length].replace('0.8', '1'),
        pointRadius: 3
      }))
    };
  };

  // Format standard deviation value
  const formatStdDev = (value) => {
    if (value === null || value === undefined) return 'N/A';
    if (typeof value === 'string') {
      return parseFloat(value).toFixed(3);
    }
    return value.toFixed(3);
  };

  return (
    <div className="transparent-card rounded-xl p-5 shadow-xl border border-gray-600 border-opacity-30 w-full">
      <div className="mb-6">
        <h2 className="text-xl font-bold mb-4">Model Performance Metrics</h2>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Chart Type
            </label>
            <select
              value={chartType}
              onChange={handleChartTypeChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="bar">Bar Chart</option>
              <option value="radar">Radar Chart</option>
            </select>
          </div>
          
          {chartType === 'bar' && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Metric
              </label>
              <select
                value={selectedMetric}
                onChange={handleMetricChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
              >
                {performanceData.metrics.map(metric => (
                  <option key={metric.id} value={metric.id}>
                    {metric.name}
                  </option>
                ))}
              </select>
            </div>
          )}
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Model Type
            </label>
            <select
              value={modelTypeFilter || 'all'}
              onChange={handleModelTypeChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="all">All Models</option>
              <option value="proprietary">Proprietary</option>
              <option value="open source">Open Source</option>
            </select>
          </div>
        </div>
      </div>
      
      <div className="h-96">
        {chartType === 'bar' ? (
          <Bar 
            data={prepareBarChartData()} 
            options={{
              responsive: true,
              maintainAspectRatio: false,
              plugins: {
                legend: {
                  position: 'top',
                },
                title: {
                  display: true,
                  text: `Model Performance: ${performanceData.metrics.find(m => m.id === selectedMetric)?.name || selectedMetric}`,
                  font: {
                    size: 16
                  }
                },
                tooltip: {
                  callbacks: {
                    label: function(context) {
                      const model = performanceData.data[context.dataIndex];
                      return `${context.dataset.label}: ${context.parsed.y.toFixed(3)}`;
                    },
                    afterLabel: function(context) {
                      const model = performanceData.data[context.dataIndex];
                      const stdDevField = getStdDevField(selectedMetric);
                      const stdDev = model[stdDevField];
                      return `Standard Deviation: ${formatStdDev(stdDev)}`;
                    }
                  }
                }
              },
              scales: {
                y: {
                  beginAtZero: true,
                  max: 1,
                  title: {
                    display: true,
                    text: 'Score (0-1)'
                  }
                }
              }
            }}
          />
        ) : (
          <Radar
            data={prepareRadarChartData()}
            options={{
              responsive: true,
              maintainAspectRatio: false,
              scales: {
                r: {
                  beginAtZero: true,
                  min: 0,
                  max: 1,
                  ticks: {
                    stepSize: 0.2,
                    showLabelBackdrop: false,
                    font: {
                      size: 10
                    }
                  },
                  pointLabels: {
                    font: {
                      size: 12
                    }
                  }
                }
              },
              plugins: {
                legend: {
                  position: 'top',
                },
                title: {
                  display: true,
                  text: 'Model Performance Comparison (All Metrics)',
                  font: {
                    size: 16
                  }
                },
                tooltip: {
                  callbacks: {
                    label: function(context) {
                      const model = performanceData.data[context.datasetIndex];
                      return `${context.dataset.label}: ${context.raw.toFixed(3)}`;
                    },
                    afterLabel: function(context) {
                      const model = performanceData.data[context.datasetIndex];
                      const metricId = performanceData.metrics[context.dataIndex].id;
                      const stdDevField = getStdDevField(metricId);
                      const stdDev = model[stdDevField];
                      return `Standard Deviation: ${formatStdDev(stdDev)}`;
                    }
                  }
                }
              }
            }}
          />
        )}
      </div>
      
      <div className="mt-6">
        <h3 className="text-lg font-semibold mb-3">Data Table</h3>
        <div className="overflow-x-auto">
          <table className="min-w-full bg-white rounded-lg overflow-hidden">
            <thead className="bg-gray-100">
              <tr>
                <th className="px-4 py-2 text-left text-sm font-semibold text-gray-600">Model</th>
                {performanceData.metrics.map(metric => (
                  <th key={metric.id} className="px-4 py-2 text-left text-sm font-semibold text-gray-600">
                    {metric.name}
                  </th>
                ))}
                <th className="px-4 py-2 text-left text-sm font-semibold text-gray-600">Evaluated Query Count</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {performanceData.data.map((model, idx) => (
                <tr key={model.model_id} className={idx % 2 === 0 ? 'bg-gray-50' : 'bg-white'}>
                  <td className="px-4 py-2 text-sm text-gray-900 font-medium">{model.model_name.split('/')[1]}</td>
                  {performanceData.metrics.map(metric => {
                    const metricValue = model[metric.id];
                    const stdDevField = getStdDevField(metric.id);
                    const stdDev = model[stdDevField];
                    
                    return (
                      <td key={`${model.model_id}-${metric.id}`} className="px-4 py-2 text-sm text-gray-900">
                        {metricValue !== null && metricValue !== undefined ? metricValue.toFixed(3) : 'N/A'}
                        <span className="text-gray-500 ml-1">
                          (σ: {formatStdDev(stdDev)})
                        </span>
                      </td>
                    );
                  })}
                  <td className="px-4 py-2 text-sm text-gray-900">{model.query_evaluation_count}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
} 