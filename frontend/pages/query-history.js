import { useState, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/cjs/styles/prism';

export default function QueryHistory() {
  const [queryHistory, setQueryHistory] = useState([]);
  const [selectedQueries, setSelectedQueries] = useState(new Set());
  const [selectAll, setSelectAll] = useState(false);
  const [expandedQuery, setExpandedQuery] = useState(null);

  // Load query history from localStorage on component mount
  useEffect(() => {
    const savedHistory = localStorage.getItem('queryHistory');
    if (savedHistory) {
      try {
        setQueryHistory(JSON.parse(savedHistory));
      } catch (error) {
        console.error('Error loading query history:', error);
        setQueryHistory([]);
      }
    }
  }, []);

  // Save query history to localStorage whenever it changes
  useEffect(() => {
    localStorage.setItem('queryHistory', JSON.stringify(queryHistory));
  }, [queryHistory]);

  const handleSelectQuery = (queryId) => {
    const newSelected = new Set(selectedQueries);
    if (newSelected.has(queryId)) {
      newSelected.delete(queryId);
    } else {
      newSelected.add(queryId);
    }
    setSelectedQueries(newSelected);
    setSelectAll(newSelected.size === queryHistory.length && queryHistory.length > 0);
  };

  const handleSelectAll = () => {
    if (selectAll) {
      setSelectedQueries(new Set());
      setSelectAll(false);
    } else {
      setSelectedQueries(new Set(queryHistory.map(q => q.id)));
      setSelectAll(true);
    }
  };

  const handleDeleteSelected = () => {
    if (selectedQueries.size === 0) return;
    
    const confirmDelete = window.confirm(
      `Are you sure you want to delete ${selectedQueries.size} selected quer${selectedQueries.size === 1 ? 'y' : 'ies'}?`
    );
    
    if (confirmDelete) {
      setQueryHistory(prev => prev.filter(query => !selectedQueries.has(query.id)));
      setSelectedQueries(new Set());
      setSelectAll(false);
    }
  };

  const handleDeleteSingle = (queryId) => {
    const confirmDelete = window.confirm('Are you sure you want to delete this query?');
    if (confirmDelete) {
      setQueryHistory(prev => prev.filter(query => query.id !== queryId));
      setSelectedQueries(prev => {
        const newSelected = new Set(prev);
        newSelected.delete(queryId);
        return newSelected;
      });
    }
  };

  const handleClearAll = () => {
    if (queryHistory.length === 0) return;
    
    const confirmClear = window.confirm('Are you sure you want to clear all query history? This action cannot be undone.');
    if (confirmClear) {
      setQueryHistory([]);
      setSelectedQueries(new Set());
      setSelectAll(false);
      setExpandedQuery(null);
    }
  };

  const toggleExpanded = (queryId) => {
    setExpandedQuery(expandedQuery === queryId ? null : queryId);
  };

  const formatTimestamp = (timestamp) => {
    return new Date(timestamp).toLocaleString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const truncateText = (text, maxLength = 150) => {
    if (text.length <= maxLength) return text;
    return text.substring(0, maxLength) + '...';
  };

  return (
    <div className="bg-ferry-image min-h-screen">
      <main className="container mx-auto py-4 sm:py-6 px-2 sm:px-4">
        <div className="max-w-6xl mx-auto">
          {/* Page Header */}
          <div className="bg-white bg-opacity-95 rounded-xl p-4 sm:p-6 shadow-lg border border-gray-100 mb-4 sm:mb-6">
            <div className="flex flex-col space-y-4 lg:flex-row lg:items-center lg:justify-between lg:space-y-0">
              <div className="flex items-center">
                <div className="p-2 bg-purple-600 rounded text-white mr-3 flex-shrink-0">
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 sm:h-6 sm:w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
                <div className="min-w-0">
                  <h1 className="text-xl sm:text-2xl font-bold text-gray-800">Query History</h1>
                  <p className="text-gray-600 text-xs sm:text-sm">
                    {queryHistory.length} quer{queryHistory.length === 1 ? 'y' : 'ies'} stored in browser memory
                  </p>
                </div>
              </div>
              
              {queryHistory.length > 0 && (
                <div className="flex flex-wrap items-center gap-2 sm:gap-3">
                  <button
                    onClick={handleSelectAll}
                    className="px-3 py-1.5 sm:px-4 sm:py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-xs sm:text-sm flex-shrink-0"
                  >
                    {selectAll ? 'Deselect' : 'Select'} All
                  </button>
                  
                  {selectedQueries.size > 0 && (
                    <button
                      onClick={handleDeleteSelected}
                      className="px-3 py-1.5 sm:px-4 sm:py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors text-xs sm:text-sm flex-shrink-0"
                    >
                      Delete ({selectedQueries.size})
                    </button>
                  )}
                  
                  <button
                    onClick={handleClearAll}
                    className="px-3 py-1.5 sm:px-4 sm:py-2 bg-orange-600 text-white rounded-lg hover:bg-orange-700 transition-colors text-xs sm:text-sm flex-shrink-0"
                  >
                    Clear All
                  </button>
                </div>
              )}
            </div>
            
            {/* Privacy & Local Storage Notice */}
            <div className="mt-3 sm:mt-4 space-y-2 sm:space-y-3">
              <div className="p-2 sm:p-3 bg-green-50 border border-green-200 rounded-lg">
                <div className="flex items-start">
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 sm:h-5 sm:w-5 text-green-600 mr-2 mt-0.5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.8-3.6a9 9 0 11-4.95 15.95A8.97 8.97 0 013 12a9 9 0 019-9z" />
                  </svg>
                  <div className="flex-1 min-w-0">
                    <p className="text-green-800 text-xs sm:text-sm font-medium">🔒 GDPR Compliant - Your Data Stays Private</p>
                    <p className="text-green-700 text-xs mt-1">
                      All query history is stored locally on your device only. We don't collect, transmit, or store your data on our servers.
                    </p>
                  </div>
                </div>
              </div>
              
              <div className="p-2 sm:p-3 bg-blue-50 border border-blue-200 rounded-lg">
                <div className="flex items-start">
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 sm:h-5 sm:w-5 text-blue-600 mr-2 mt-0.5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <div className="flex-1 min-w-0">
                    <p className="text-blue-800 text-xs sm:text-sm font-medium">Local Storage Information</p>
                    <ul className="text-blue-700 text-xs mt-1 space-y-0.5">
                      <li>• Data is stored in your browser's local storage</li>
                      <li>• Available only on this device and browser</li>
                      <li>• Automatically deleted if you clear browser data</li>
                      <li>• You can delete all history using the "Clear All" button</li>
                      <li>• Maximum 100 queries stored (oldest automatically removed)</li>
                    </ul>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Query History List */}
          <div className="space-y-3 sm:space-y-4">
            {queryHistory.length === 0 ? (
              <div className="bg-white bg-opacity-95 rounded-xl p-8 sm:p-12 shadow-lg border border-gray-100 text-center">
                <svg className="w-16 h-16 sm:w-24 sm:h-24 text-gray-300 mx-auto mb-3 sm:mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <h3 className="text-lg sm:text-xl font-medium text-gray-500 mb-2">No Query History</h3>
                <p className="text-gray-400 text-sm sm:text-base px-4">Your query history will appear here after you run some analyses.</p>
                <a 
                  href="/"
                  className="inline-block mt-4 px-4 py-2 sm:px-6 sm:py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm sm:text-base"
                >
                  Start Querying
                </a>
              </div>
            ) : (
              queryHistory.map((query) => (
                <div key={query.id} className="bg-white bg-opacity-95 rounded-xl shadow-lg border border-gray-100 overflow-hidden">
                  <div className="p-3 sm:p-6">
                    <div className="flex items-start space-x-3 sm:space-x-4">
                      {/* Checkbox */}
                      <div className="mt-1 flex-shrink-0">
                        <input
                          type="checkbox"
                          checked={selectedQueries.has(query.id)}
                          onChange={() => handleSelectQuery(query.id)}
                          className="w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500"
                        />
                      </div>
                      
                      {/* Query Content */}
                      <div className="flex-1 min-w-0">
                        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-2 gap-2">
                          <div className="flex flex-col sm:flex-row sm:items-center gap-2 sm:gap-3">
                            <span className="px-2 py-1 bg-blue-100 text-blue-800 text-xs font-medium rounded-full self-start">
                              {query.model}
                            </span>
                            <span className="text-gray-500 text-xs sm:text-sm">
                              {formatTimestamp(query.timestamp)}
                            </span>
                          </div>
                          
                          <button
                            onClick={() => handleDeleteSingle(query.id)}
                            className="p-1.5 sm:p-1 text-red-600 hover:bg-red-50 rounded transition-colors self-start"
                            title="Delete this query"
                          >
                            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                            </svg>
                          </button>
                        </div>
                        
                        {/* Query Question */}
                        <div className="mb-3">
                          <h3 className="font-medium text-gray-800 mb-1">Question:</h3>
                          <p className="text-gray-700 bg-gray-50 p-2 sm:p-3 rounded-lg break-words text-sm">
                            {query.question}
                          </p>
                        </div>
                        
                        {/* Response Preview/Full */}
                        <div>
                          <h3 className="font-medium text-gray-800 mb-1">Response:</h3>
                          <div className="relative">
                            {expandedQuery === query.id ? (
                              <div className="border rounded-lg">
                                {/* Close button when expanded */}
                                <div className="flex justify-end p-2 bg-gray-100 border-b border-gray-200">
                                  <button
                                    onClick={() => toggleExpanded(query.id)}
                                    className="text-gray-500 hover:text-gray-700 transition-colors"
                                    title="Close expanded view"
                                  >
                                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                                    </svg>
                                  </button>
                                </div>
                                <div className="max-h-80 sm:max-h-96 overflow-auto">
                                  <div className="p-3 sm:p-4">
                                    <ReactMarkdown
                                      className="prose prose-sm max-w-none text-gray-700 break-words"
                                      components={{
                                        code({ node, inline, className, children, ...props }) {
                                          const match = /language-(\w+)/.exec(className || '')
                                          const language = match ? match[1] : 'text'
                                          return !inline && (language === 'sql' || language === 'mysql') ? (
                                            <div className="w-full overflow-x-auto bg-gray-900 rounded my-2">
                                              <SyntaxHighlighter
                                                language="sql"
                                                style={vscDarkPlus}
                                                customStyle={{
                                                  margin: 0,
                                                  borderRadius: '0.25rem',
                                                  fontSize: '0.75rem',
                                                  padding: '0.75rem',
                                                  width: '100%',
                                                  maxWidth: '100%',
                                                  overflowX: 'auto'
                                                }}
                                                wrapLines={true}
                                                wrapLongLines={true}
                                                {...props}
                                              >
                                                {String(children).replace(/\n$/, '')}
                                              </SyntaxHighlighter>
                                            </div>
                                          ) : (
                                            <code className="bg-gray-200 px-1 py-0.5 rounded text-gray-800" {...props}>
                                              {children}
                                            </code>
                                          )
                                        }
                                      }}
                                    >
                                      {query.response}
                                    </ReactMarkdown>
                                  </div>
                                </div>
                              </div>
                            ) : (
                              <div 
                                className="border rounded-lg cursor-pointer hover:bg-gray-50 transition-colors border-2 border-transparent hover:border-blue-200"
                                onClick={() => toggleExpanded(query.id)}
                                title="Click to expand full response"
                              >
                                <p className="text-gray-700 p-3 sm:p-4 break-words text-sm">
                                  {truncateText(query.response.replace(/[#*`_~]/g, ''))}
                                </p>
                                {/* Visual indicator that it's clickable */}
                                <div className="text-right p-2 text-xs text-gray-500">
                                  Click to expand full response
                                </div>
                              </div>
                            )}
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </main>
    </div>
  );
} 