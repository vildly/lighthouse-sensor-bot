import { useState, useEffect, useRef } from "react";
import { useWebSocket } from "../contexts/WebSocketContext";
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/cjs/styles/prism';

export default function QuestionForm() {
  const [question, setQuestion] = useState("");
  const [content, setContent] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [backendStatus, setBackendStatus] = useState("offline");
  const [sourceFile, setSourceFile] = useState("ferry_trips_data.csv"); // Default to CSV file
  const [modelCategory, setModelCategory] = useState("open-source"); // Default to open-source
  const [selectedModel, setSelectedModel] = useState("qwen/qwen-2.5-72b-instruct"); // Default model
  const [modelUsed, setModelUsed] = useState(null);
  
  // Get WebSocket context
  const { sqlQueries, queryStatus, resetQueries } = useWebSocket();
  
  // Reference to the SQL queries container for auto-scrolling
  const queriesContainerRef = useRef(null);
  
  // Auto-scroll when new queries are added
  useEffect(() => {
    if (queriesContainerRef.current) {
      queriesContainerRef.current.scrollTop = queriesContainerRef.current.scrollHeight;
    }
  }, [sqlQueries]);

  useEffect(() => {
    // Check backend status on component mount
    testConnection(false);
  }, []);

  const askQuestion = async () => {
    if (question.trim() === "") {
      setContent("Please enter a question");
      return;
    }
    
    setIsLoading(true);
    setContent(null);
    resetQueries(); // Reset SQL queries for new question
    
    try {
      const response = await fetch("/api/query", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          question,
          source_file: sourceFile,
          llm_model_id: selectedModel // Include the selected model
        }),
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! Status: ${response.status}`);
      }
      
      const data = await response.json();
      setContent(data.content);
      setModelUsed(selectedModel); // Save the model used for this query.
    } catch (error) {
      console.error("Error asking question:", error);
      setContent("Error connecting to the backend: " + error.message);
    } finally {
      setIsLoading(false);
    }
  };

  const testConnection = async (showAlert = true) => {
    try {
      const response = await fetch("/api/test");
      const data = await response.json();
      
      if (data.status === "online" || data.content === "OK" || 
          data.content === "Backend connection test successful") {
        setBackendStatus("online");
        if (showAlert) {
          alert(`Backend connection test: Success`);
        }
      } else {
        setBackendStatus("offline");
        if (showAlert) {
          alert(`Backend connection test: Failed - ${data.content || "Unknown error"}`);
        }
      }
    } catch (error) {
      setBackendStatus("offline");
      if (showAlert) {
        alert(`Backend connection test failed: ${error.message}`);
      }
    }
  };

  const loadPrompt = async () => {
    try {
      const response = await fetch("/api/load-prompt");
      const data = await response.json();
      
      if (data.content) {
        setQuestion(data.content);
      } else {
        alert("Failed to load prompt: No content received");
      }
    } catch (error) {
      alert(`Failed to load prompt: ${error.message}`);
    }
  };

  const handleCategoryChange = (category) => {
    setModelCategory(category);
    // Set a default model for the selected category
    if (category === "proprietary") {
      setSelectedModel("openai/gpt-4o-2024-11-20");
    } else {
      setSelectedModel("qwen/qwen-2.5-72b-instruct");
    }
  };

  // Update the backend status indicator with breathing effect
  const statusIndicator = (
    <div className="flex items-center">
      <span 
        className={`backend-status-indicator ${backendStatus === "online" ? "online" : "offline"}`}
      ></span>
      <span className="ml-2 text-sm text-white text-opacity-80">
        {backendStatus === "online" ? "Backend connected" : "Backend disconnected"}
      </span>
    </div>
  );

  // Add a section to display SQL queries with syntax highlighting
  const renderSqlQueries = () => {
    if (sqlQueries.length === 0) return null;
    
    return (
      <div className="mt-4 bg-white bg-opacity-10 rounded-xl p-4">
        <h3 className="text-white text-sm font-medium mb-2">SQL Queries</h3>
        <div 
          ref={queriesContainerRef}
          className="space-y-2 max-h-60 overflow-y-auto"
        >
          {sqlQueries.map((query, index) => (
            <div key={index} className="rounded">
              <SyntaxHighlighter 
                language="sql" 
                style={vscDarkPlus}
                customStyle={{ 
                  margin: 0, 
                  borderRadius: '0.25rem',
                  fontSize: '0.875rem',
                  padding: '0.5rem'
                }}
              >
                {query}
              </SyntaxHighlighter>
            </div>
          ))}
        </div>
      </div>
    );
  };

  return (
    <div className="bg-ferry-image min-h-screen">
      <header className="pt-4">
        <div className="arc-navbar">
          <div className="container mx-auto px-6 py-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-3">
               
                <svg className="w-8 h-8 text-white" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M3 18H21L19 22H5L3 18Z" fill="currentColor" />
                  <path d="M19 18L21 8H3L5 18" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                  <path d="M15 18V8" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                  <path d="M9 18V8" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                  <path d="M12 8V4" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                  <path d="M8 4H16" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                </svg>
         

                <h1 className="text-xl font-bold text-white">Ferry Analytics</h1>
              </div>
              
              <div className="flex items-center">
                {statusIndicator}
              </div>
            </div>
          </div>
        </div>
      </header>

      <main className="container mx-auto py-6">
        <div className="flex flex-col lg:flex-row gap-8">
          <div className="lg:w-1/3">
            <div className="transparent-card rounded-xl p-5 shadow-xl border border-gray-600 border-opacity-30">
              <h2 className="text-lg font-semibold text-white mb-4 text-enhanced">Query Settings</h2>
              
              <div className="mb-4">
                <label className="text-sm font-medium text-white mb-2 block text-enhanced">Model Type</label>
                <div className="model-type-toggle flex rounded-lg w-full">
                  <button
                    className={`model-type-option flex-1 ${modelCategory === "proprietary" ? "active" : ""}`}
                    onClick={() => handleCategoryChange("proprietary")}
                  >
                    Proprietary
                  </button>
                  <button
                    className={`model-type-option flex-1 ${modelCategory === "open-source" ? "active" : ""}`}
                    onClick={() => handleCategoryChange("open-source")}
                  >
                    Open Source
                  </button>
                </div>
              </div>
              
              <div className="mb-4">
                <label className="text-sm font-medium text-white mb-2 block text-enhanced">Model</label>
                <div className="relative">
                  {modelCategory === "proprietary" ? (
                    <select
                      className="w-full px-3 py-2 dropdown-field text-white"
                      value={selectedModel}
                      onChange={(e) => setSelectedModel(e.target.value)}
                    >
                      <option value="openai/gpt-4o-2024-11-20">OpenAI GPT-4o</option>
                      <option value="anthropic/claude-3.7-sonnet">Claude 3.7 Sonnet</option>
                      <option value="google/gemini-2.0-flash-001">Gemini 2.0 Flash</option>
                      <option value="amazon/nova-pro-v1">Amazon Nova Pro</option>
                    </select>
                  ) : (
                    <select
                      className="w-full px-3 py-2 dropdown-field text-white"
                      value={selectedModel}
                      onChange={(e) => setSelectedModel(e.target.value)}
                    >
                      <option value="qwen/qwen-2.5-72b-instruct">Qwen 2.5 72B</option>
                      <option value="meta-llama/llama-3.3-70b-instruct">Llama 3.3 70B</option>
                      <option value="meta-llama/llama-3.1-8b-instruct">Llama 3.1 8B</option>
                      <option value="mistralai/ministral-8b">Mistral 8B</option>
                    </select>
                  )}
                  <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-2 text-white">
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7"></path>
                    </svg>
                  </div>
                </div>
              </div>
              
              <div className="mb-4">
                <label className="text-sm font-medium text-white mb-2 block text-enhanced">Data Source</label>
                <div className="relative">
                  <select
                    className="w-full px-3 py-2 dropdown-field text-white"
                    value={sourceFile}
                    onChange={(e) => setSourceFile(e.target.value)}
                  >
                    <option value="ferry_trips_data.csv">Ferry Trips Data (CSV)</option>
                    <option value="ferries.json">Ferries Info (JSON)</option>
                  </select>
                  <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-2 text-white">
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7"></path>
                    </svg>
                  </div>
                </div>
              </div>
              
              <div className="mb-4">
                <label className="text-sm font-medium text-white mb-2 block text-enhanced">Your Question</label>
                <textarea
                  className="w-full px-4 py-3 rounded-lg input-emphasized"
                  rows="4"
                  placeholder="Enter your question about ferry data..."
                  value={question}
                  onChange={(e) => setQuestion(e.target.value)}
                ></textarea>
              </div>
              
              <div className="flex justify-between items-center">
                <div className="space-x-2">
                  <button
                    onClick={loadPrompt}
                    className="button-secondary load-example text-white text-sm py-2 px-4 rounded-lg"
                  >
                    Load Example
                  </button>
                  <button
                    onClick={() => setQuestion("")}
                    className="button-secondary text-white text-sm py-2 px-4 rounded-lg"
                  >
                    Clear
                  </button>
                </div>
                <button 
                  onClick={askQuestion}
                  disabled={isLoading || !question.trim()}
                  className="button-primary text-sm py-2 px-4 rounded-lg"
                >
                  {isLoading ? (
                    <div className="flex items-center">
                      <div className="animate-spin text-white h-4 w-4 border-b-2 border-current mr-2"></div>
                      Processing...
                    </div>
                  ) : 'Send'}
                </button>
              </div>
              
              <div className="mt-6">
                <h3 className="text-sm font-medium text-gray-700 mb-2">Active Context</h3>
                <div className="flex flex-wrap gap-2">
                  <div className="context-label">
                    <span className="context-label-title">Model:</span>
                    <span className="context-label-value">{selectedModel.split('/')[1]}</span>
                  </div>
                  <div className="context-label">
                    <span className="context-label-title">Data:</span>
                    <span className="context-label-value">{sourceFile}</span>
                  </div>
                </div>
              </div>
              
              <div className="mt-6">
                <h3 className="text-sm font-medium text-white mb-2">Response Preview</h3>
                <div className="response-container rounded-lg p-3 max-h-48 overflow-y-auto">
                  {isLoading ? (
                    <div className="flex justify-center items-center py-4">
                      <div className="animate-spin rounded-full h-6 w-6 border-t-2 border-b-2 border-black"></div>
                    </div>
                  ) : content ? (
                    <div className="prose prose-sm max-w-none text-gray-800">
                      <div dangerouslySetInnerHTML={{ __html: content }}></div>
                    </div>
                  ) : (
                    <div className="text-gray-500 text-sm text-center py-4">
                      Response will appear here
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
          
          <div className="lg:w-2/3">
            <div className="transparent-card rounded-xl p-5 shadow-xl border border-gray-600 border-opacity-30 h-full">
              <h2 className="text-lg font-semibold text-white mb-4">Data Visualization</h2>
              
              <div className="mb-4 border-b border-white border-opacity-20">
                <div className="flex space-x-2 border-b border-white border-opacity-20">
                  <button className="tab-button active px-4 py-2">Overview</button>
                  <button className="tab-button px-4 py-2">Speed Analysis</button>
                  <button className="tab-button px-4 py-2">Fuel Consumption</button>
                  <button className="tab-button px-4 py-2">Routes</button>
                </div>
              </div>
              
              <div className="bg-white bg-opacity-20 rounded-xl p-6 visualization-container visualization-expanded">
                {isLoading ? (
                  <div className="flex justify-center items-center h-full">
                    <div className="flex flex-col items-center">
                      <div className="animate-spin rounded-full h-16 w-16 border-4 border-white border-opacity-20 border-t-white"></div>
                      <p className="mt-4 text-white text-opacity-80">Generating visualization...</p>
                      
                      {/* Show SQL queries while loading */}
                      {renderSqlQueries()}
                    </div>
                  </div>
                ) : content ? (
                  <div className="grid grid-cols-2 gap-6 h-full">
                    <div className="col-span-2 bg-white bg-opacity-20 rounded-xl p-4 h-[60%] visualization-container">
                      <h3 className="text-white text-sm font-medium mb-2">Ferry Speed Comparison</h3>
                      <div className="h-[calc(100%-30px)] w-full flex items-center justify-center">
                        <div className="relative w-full h-full">
                          <div className="absolute inset-0 flex items-center justify-center">
                            <svg className="w-16 h-16 text-white text-opacity-40" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M8 13v-1m4 1v-3m4 3V8M8 21l4-4 4 4M3 4h18M4 4h16v12a1 1 0 01-1 1H5a1 1 0 01-1-1V4z"></path>
                            </svg>
                          </div>
                        </div>
                      </div>
                    </div>
                    
                    <div className="bg-white bg-opacity-20 rounded-xl p-4 h-[40%] visualization-container">
                      <h3 className="text-white text-sm font-medium mb-2">Trip Frequency</h3>
                      <div className="h-[calc(100%-30px)] w-full"></div>
                    </div>
                    
                    <div className="bg-white bg-opacity-20 rounded-xl p-4 h-[40%] visualization-container">
                      <h3 className="text-white text-sm font-medium mb-2">Fuel Efficiency</h3>
                      <div className="h-[calc(100%-30px)] w-full"></div>
                    </div>
                    
                    {/* Add SQL queries section */}
                    <div className="col-span-2">
                      {renderSqlQueries()}
                    </div>
                  </div>
                ) : (
                  <div className="flex flex-col justify-center items-center h-full">
                    <svg className="w-24 h-24 text-white text-opacity-20" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M8 13v-1m4 1v-3m4 3V8M8 21l4-4 4 4M3 4h18M4 4h16v12a1 1 0 01-1 1H5a1 1 0 01-1-1V4z"></path>
                    </svg>
                    <h3 className="mt-4 text-white text-opacity-80 text-lg font-medium">Ask a question to generate visualizations</h3>
                    <p className="mt-2 text-white text-opacity-60 text-center max-w-md">
                      Your data will be analyzed and displayed here once you submit a query
                    </p>
                  </div>
                )}
              </div>
              
              <div className="mt-4">
                {/* The Key Insights section has been completely removed */}
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}