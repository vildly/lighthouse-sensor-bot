import { useState, useEffect } from 'react';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/cjs/styles/prism';
import ReactMarkdown from 'react-markdown';

export default function HistoryPage() {
  const [queryHistory, setQueryHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [sortField, setSortField] = useState('query_timestamp');
  const [sortDirection, setSortDirection] = useState('asc');
  const [selectedQuery, setSelectedQuery] = useState(null);

  useEffect(() => {
    async function fetchQueryHistory() {
      try {
        setLoading(true);
        const response = await fetch('/api/full-query-data');

        if (!response.ok) {
          throw new Error(`Error fetching query history: ${response.statusText}`);
        }

        const data = await response.json();

        const formattedData = data.data.map(item => {
          if (item.query_timestamp) {
            // Check if timestamp is in epoch format or already formatted
            const timestamp = new Date(item.query_timestamp);
            if (!isNaN(timestamp)) {
              item.formatted_timestamp = timestamp.toLocaleString();
            } else {
              item.formatted_timestamp = item.query_timestamp;
            }
          } else {
            item.formatted_timestamp = 'N/A';
          }
          return item;
        });

        setQueryHistory(formattedData);
        setError(null);
      } catch (err) {
        console.error('Error fetching query history:', err);
        setError('Failed to load query history data');
      } finally {
        setLoading(false);
      }
    }

    fetchQueryHistory();
  }, []);

  const handleSort = (field) => {
    if (sortField === field) {
      // Toggle direction if clicking the same field
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      // Default to descending for new sort field
      setSortField(field);
      setSortDirection('desc');
    }
  };

  const sortedHistory = [...queryHistory].sort((a, b) => {
    let valueA = a[sortField];
    let valueB = b[sortField];

    // Handle numeric values
    if (!isNaN(parseFloat(valueA)) && !isNaN(parseFloat(valueB))) {
      valueA = parseFloat(valueA);
      valueB = parseFloat(valueB);
    }

    // Handle null/undefined values
    if (valueA === null || valueA === undefined) return sortDirection === 'asc' ? -1 : 1;
    if (valueB === null || valueB === undefined) return sortDirection === 'asc' ? 1 : -1;

    // Sort strings
    if (typeof valueA === 'string' && typeof valueB === 'string') {
      return sortDirection === 'asc'
        ? valueA.localeCompare(valueB)
        : valueB.localeCompare(valueA);
    }

    // Sort numbers
    return sortDirection === 'asc' ? valueA - valueB : valueB - valueA;
  });

  const viewQueryDetails = (query) => {
    setSelectedQuery(query);
  };

  const closeQueryDetails = () => {
    setSelectedQuery(null);
  };

  // Parse SQL queries from JSON string - improved error handling
  const parseSqlQueries = (sqlQueriesString) => {
    try {
      if (!sqlQueriesString) return [];

      // Handle string format with curly braces
      if (typeof sqlQueriesString === 'string' && sqlQueriesString.startsWith('{')) {
        // Remove curly braces and split by commas
        const queriesString = sqlQueriesString.replace(/^{|}$/g, '');
        // Split by commas that are followed by a quote
        const queries = queriesString.split(/",/).map(q => {
          // Clean up each query
          return q.trim().replace(/^"|"$/g, '');
        });
        return queries;
      }
      // Handle regular JSON array
      else if (typeof sqlQueriesString === 'string') {
        try {
          const parsed = JSON.parse(sqlQueriesString);
          if (Array.isArray(parsed)) {
            return parsed;
          }
          return [sqlQueriesString]; // Return as single item if parsing fails
        } catch (e) {
          // If JSON parsing fails, treat as a single query
          return [sqlQueriesString];
        }
      }

      // If it's already an array
      if (Array.isArray(sqlQueriesString)) {
        return sqlQueriesString;
      }

      return [String(sqlQueriesString)]; // Convert to string as fallback
    } catch (error) {
      console.error('Error parsing SQL queries:', error);
      return [String(sqlQueriesString)]; // Return as single item on error
    }
  };

  // Format metric name for display
  const formatMetricName = (key) => {
    return key
      .split('_')
      .map(word => word.charAt(0).toUpperCase() + word.slice(1))
      .join(' ');
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 to-gray-800">
      <main className="container mx-auto px-4 py-8">
        <h1 className="text-3xl font-bold text-white mb-8">Query History</h1>

        {loading ? (
          <div className="flex justify-center items-center h-64">
            <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-600"></div>
          </div>
        ) : error ? (
          <div className="bg-red-100 border-l-4 border-red-500 text-red-700 p-4 rounded">
            <p>{error}</p>
          </div>
        ) : (
          <div className="bg-white bg-opacity-95 rounded-xl shadow-lg overflow-hidden">
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th
                      scope="col"
                      className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                      onClick={() => handleSort('query')}
                    >
                      Query
                      {sortField === 'query' && (
                        <span className="ml-1">{sortDirection === 'asc' ? '↑' : '↓'}</span>
                      )}
                    </th>
                    <th
                      scope="col"
                      className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                      onClick={() => handleSort('model_name')}
                    >
                      Model
                      {sortField === 'model_name' && (
                        <span className="ml-1">{sortDirection === 'asc' ? '↑' : '↓'}</span>
                      )}
                    </th>
                    <th
                      scope="col"
                      className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                      onClick={() => handleSort('query_timestamp')}
                    >
                      Timestamp
                      {sortField === 'query_timestamp' && (
                        <span className="ml-1">{sortDirection === 'asc' ? '↑' : '↓'}</span>
                      )}
                    </th>
                    <th
                      scope="col"
                      className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                      onClick={() => handleSort('factual_correctness')}
                    >
                      Factual Correctness
                      {sortField === 'factual_correctness' && (
                        <span className="ml-1">{sortDirection === 'asc' ? '↑' : '↓'}</span>
                      )}
                    </th>
                    <th
                      scope="col"
                      className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                      onClick={() => handleSort('semantic_similarity')}
                    >
                      Semantic Similarity
                      {sortField === 'semantic_similarity' && (
                        <span className="ml-1">{sortDirection === 'asc' ? '↑' : '↓'}</span>
                      )}
                    </th>
                    <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {sortedHistory.length > 0 ? (
                    sortedHistory.map((item, index) => (
                      <tr key={index} className="hover:bg-gray-50">
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                          {item.query ? item.query.substring(0, 50) + (item.query.length > 50 ? '...' : '') : 'N/A'}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {item.model_name ? item.model_name.split('/')[1] : 'N/A'}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {item.formatted_timestamp}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {item.factual_correctness !== null ? parseFloat(item.factual_correctness).toFixed(2) : 'N/A'}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {item.semantic_similarity ? parseFloat(item.semantic_similarity).toFixed(2) : 'N/A'}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                          <button
                            onClick={() => viewQueryDetails(item)}
                            className="text-blue-600 hover:text-blue-900"
                          >
                            View Details
                          </button>
                        </td>
                      </tr>
                    ))
                  ) : (
                    <tr>
                      <td colSpan="6" className="px-6 py-4 text-center text-sm text-gray-500">
                        No query history available
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Query Details Modal */}
        {selectedQuery && (
          <div 
            className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50"
            onClick={(e) => {
              // Close modal when clicking outside it
              if (e.target === e.currentTarget) {
                closeQueryDetails();
              }
            }}
          >
            <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-y-auto">
              <div className="p-6">
                <div className="flex justify-between items-center mb-4">
                  <h2 className="text-xl font-bold text-gray-900">Query Details</h2>
                  <button
                    onClick={closeQueryDetails}
                    className="text-gray-500 hover:text-gray-700"
                  >
                    <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12"></path>
                    </svg>
                  </button>
                </div>

                <div className="space-y-4">

                <div>
                    <h3 className="text-lg font-medium text-gray-900">Model</h3>
                    <p className="mt-1 text-sm text-gray-600">{selectedQuery.model_name || 'N/A'}</p>
                  </div>

                  
                  <div>
                    <h3 className="text-lg font-medium text-gray-900">Timestamp</h3>
                    <p className="mt-1 text-sm text-gray-600">{selectedQuery.formatted_timestamp}</p>
                  </div>


                  <div>
                    <h3 className="text-lg font-medium text-gray-900">Query</h3>
                    <p className="mt-1 text-sm text-gray-600">{selectedQuery.query || 'N/A'}</p>
                  </div>

                  <div>
                    <h3 className="text-lg font-medium text-gray-900">Direct Response</h3>
                    <p className="mt-1 text-sm text-gray-600">{selectedQuery.direct_response || 'N/A'}</p>
                  </div>

                

                  <div>
                    <h3 className="text-lg font-medium text-gray-900">Metrics</h3>
                    <div className="mt-2 grid grid-cols-1 md:grid-cols-2 gap-4">
                      {Object.entries(selectedQuery)
                        .filter(([key, value]) => 
                          !['query', 'model_name', 'query_timestamp', 'formatted_timestamp', 'full_response', 'sql_queries', 'query_result_id', 'evaluation_metric_id', 'direct_response'].includes(key) && 
                          value !== null
                        )
                        .map(([key, value]) => (
                          <div key={key} className="bg-gray-50 p-3 rounded">
                            <span className="text-sm font-medium text-gray-700">{formatMetricName(key)}</span>
                            <p className="text-sm text-gray-900">{typeof value === 'number' ? value.toFixed(3) : value}</p>
                          </div>
                        ))
                      }
                    </div>
                  </div>

                  <div>
                    <h3 className="text-lg font-medium text-gray-900">Full Response</h3>
                    <div className="mt-2 bg-gray-50 p-4 rounded max-h-96 overflow-y-auto">
                      <div className="prose prose-sm max-w-none">
                        <ReactMarkdown
                          components={{
                            code: ({ node, inline, className, children, ...props }) => {
                              const match = /language-(\w+)/.exec(className || '')
                              return !inline ? (
                                <SyntaxHighlighter
                                  language={match ? match[1] : 'text'}
                                  style={vscDarkPlus}
                                  customStyle={{
                                    margin: 0,
                                    borderRadius: '0.25rem',
                                    fontSize: '0.875rem',
                                    padding: '0.5rem',
                                    color: '#f8f8f8'
                                  }}
                                  {...props}
                                >
                                  {String(children).replace(/\n$/, '')}
                                </SyntaxHighlighter>
                              ) : (
                                <code className="bg-gray-200 px-1 py-0.5 rounded text-gray-800" {...props}>
                                  {children}
                                </code>
                              )
                            }
                          }}
                        >
                          {selectedQuery.full_response || 'No response available'}
                        </ReactMarkdown>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
} 