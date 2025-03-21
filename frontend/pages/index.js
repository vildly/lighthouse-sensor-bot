import { useState, useEffect } from "react";

export default function QuestionForm() {
  const [question, setQuestion] = useState("");
  const [content, setContent] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [backendStatus, setBackendStatus] = useState("offline");
  const [sourceFile, setSourceFile] = useState("ferry_trips_data.csv"); // Default to CSV file
  const [modelCategory, setModelCategory] = useState("open-source"); // Default to open-source
  const [selectedModel, setSelectedModel] = useState("qwen/qwen-2.5-72b-instruct"); // Default model
  const [modelUsed, setModelUsed] = useState(null);

  useEffect(() => {
    // Check backend status on component mount
    testConnection(false);
  }, []);

  const askQuestion = async () => {
    if (!question.trim()) return;
    
    setIsLoading(true);
    setContent(null);
    setModelUsed(null);
    
    try {
      const response = await fetch("/api/query", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ 
          question,
          source_file: sourceFile,
          model: selectedModel // Include the selected model
        }),
      });
      
      if (!response.ok) {
        throw new Error(`Failed to get response: ${response.status} ${response.statusText}`);
      }
  
      const data = await response.json();
      
      if (data.content) {
        setContent(data.content);
        if (data.model_used) {
          setModelUsed(data.model_used);
        }
      } else {
        setContent("No content available. Response format may be incorrect.");
      }
    } catch (error) {
      setContent(`Failed to fetch response: ${error.message}`);
      setBackendStatus("offline");
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

  return (
    <div className="min-h-screen bg-[#111827] text-gray-200">
      <header className="bg-gray-900 shadow-md">
        <div className="container mx-auto px-4 py-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
             
              <svg className="w-8 h-8 text-blue-500" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M3 18H21L19 22H5L3 18Z" fill="currentColor" />
                <path d="M19 18L21 8H3L5 18" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                <path d="M15 18V8" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                <path d="M9 18V8" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                <path d="M12 8V4" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                <path d="M8 4H16" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
       

              <h1 className="text-lg font-bold text-white">Ferry Analytics</h1>
            </div>
            
            <div className="flex items-center">
              <div className="flex items-center px-3 py-1 bg-gray-800 rounded-full">
                <div className={`w-2 h-2 rounded-full mr-2 ${
                  backendStatus === "online" ? "bg-green-400" : "bg-red-400"
                }`}></div>
                <span className="text-gray-200 text-sm">
                  {backendStatus === "online" ? "Backend Connected" : "Backend Offline"}
                </span>
              </div>
            </div>
          </div>
        </div>
      </header>

      <main className="container mx-auto px-4 py-6 max-w-5xl">
        <div className="max-w-4xl mx-auto px-4 py-6">
          <div className="bg-[#0f172a] rounded-lg shadow-xl mb-6 overflow-hidden">
            <div className="p-4">
              <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 mb-4">
                <h2 className="text-lg font-semibold text-[#FDECB2]">Query Settings</h2>
                
                <div className="flex flex-wrap items-center gap-3">
                  {/* Model Type Selection */}
                  <div className="flex items-center">
                    <span className="text-xs text-gray-400 mr-2 whitespace-nowrap">Model:</span>
                    <div className="flex">
                      <button
                        onClick={() => handleCategoryChange("proprietary")}
                        className={`px-3 py-1 text-xs font-medium rounded-l-md transition-colors ${
                          modelCategory === "proprietary" 
                            ? "bg-[#EFD81D] text-black" 
                            : "bg-[#1B1B1B] text-gray-300 hover:bg-gray-800"
                        }`}
                      >
                        Proprietary
                      </button>
                      <button
                        onClick={() => handleCategoryChange("open-source")}
                        className={`px-3 py-1 text-xs font-medium rounded-r-md transition-colors ${
                          modelCategory === "open-source" 
                            ? "bg-[#EFD81D] text-black" 
                            : "bg-[#1B1B1B] text-gray-300 hover:bg-gray-800"
                        }`}
                      >
                        Open Source
                      </button>
                    </div>
                  </div>
                  
                  {/* Model Selection Dropdown */}
                  <div className="flex items-center">
                    <div className="relative w-48">
                      {modelCategory === "proprietary" ? (
                        <select
                          value={selectedModel}
                          onChange={(e) => setSelectedModel(e.target.value)}
                          className="w-full py-1 px-2 text-xs bg-[#1B1B1B] border border-gray-700 rounded-md text-gray-200 appearance-none focus:outline-none focus:ring-1 focus:ring-[#EFD81D]"
                        >
                          <option value="openai/gpt-4o-2024-11-20">OpenAI GPT-4o</option>
                          <option value="anthropic/claude-3.7-sonnet">Claude 3.7 Sonnet</option>
                          <option value="google/gemini-2.0-flash-001">Gemini 2.0 Flash</option>
                          <option value="amazon/nova-pro-v1">Amazon Nova Pro</option>
                        </select>
                      ) : (
                        <select
                          value={selectedModel}
                          onChange={(e) => setSelectedModel(e.target.value)}
                          className="w-full py-1 px-2 text-xs bg-[#1B1B1B] border border-gray-700 rounded-md text-gray-200 appearance-none focus:outline-none focus:ring-1 focus:ring-[#EFD81D]"
                        >
                          <option value="qwen/qwen-2.5-72b-instruct">Qwen 2.5 72B</option>
                          <option value="meta-llama/llama-3.3-70b-instruct">Llama 3.3 70B</option>
                          <option value="meta-llama/llama-3.1-8b-instruct">Llama 3.1 8B</option>
                          <option value="mistralai/ministral-8b">Mistral 8B</option>
                        </select>
                      )}
                      <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-2 text-gray-400">
                        <svg className="h-3 w-3 fill-current" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20">
                          <path d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" />
                        </svg>
                      </div>
                    </div>
                  </div>
                  
                  {/* Data Source Pill */}
                  <div className="bg-[#1A9964] text-white py-1 px-3 rounded text-xs font-medium inline-flex items-center">
                    <svg className="w-3 h-3 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
                    </svg>
                    ferry_trips_data.csv
                  </div>
                </div>
              </div>
              
              {/* Question input and buttons */}
              <div className="space-y-3">
                <div className="flex justify-between items-center">
                  <label className="text-sm font-medium text-gray-300">Your Question</label>
                </div>
                
                <textarea
                  rows="2"
                  className="w-full p-2 bg-[#1B1B1B] border border-gray-700 rounded-lg text-sm focus:ring-1 focus:ring-[#EFD81D] focus:border-[#EFD81D] text-gray-200 resize-none"
                  placeholder="What is the average speed of ferry Jupiter?"
                  value={question}
                  onChange={(e) => setQuestion(e.target.value)}
                ></textarea>
                
                <div className="flex justify-between items-center">
                  {/* Display full names for model and data source */}
                  <div className="text-xs text-gray-400 flex items-center">
                    <span className="inline-block px-2 py-1 bg-[#1B1B1B] rounded mr-1 text-xs whitespace-nowrap overflow-hidden text-ellipsis max-w-[150px]">
                      {selectedModel.split('/')[1]}
                    </span>
                    <span className="mx-1">+</span>
                    <span className="inline-block px-2 py-1 bg-[#1B1B1B] rounded ml-1 text-xs">
                      {sourceFile}
                    </span>
                  </div>
                  
                  {/* Buttons container - now all three buttons together */}
                  <div className="flex items-center gap-2">
                    <button
                      onClick={loadPrompt}
                      className="px-2 py-1.5 rounded text-xs bg-[#663399] hover:bg-opacity-80 text-white"
                    >
                      Load Example
                    </button>
                    <button
                      onClick={() => setQuestion("")}
                      className="px-2 py-1.5 rounded text-xs bg-gray-700 hover:bg-gray-600 text-white"
                    >
                      Clear
                    </button>
                    <button 
                      onClick={askQuestion}
                      disabled={isLoading || !question.trim()}
                      className={`px-4 py-1.5 rounded-md text-xs font-medium transition-colors ${
                        isLoading || !question.trim() 
                          ? 'bg-gray-600 cursor-not-allowed text-gray-300' 
                          : 'bg-[#EFD81D] hover:bg-opacity-90 text-black'
                      }`}
                    >
                      {isLoading ? (
                        <div className="flex items-center">
                          <div className="animate-spin h-3 w-3 border-b-2 border-current mr-1"></div>
                          Processing...
                        </div>
                      ) : 'Send'}
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
          
          {/* Response section */}
          <div className="bg-[#1e293b] rounded-lg shadow-xl overflow-hidden">
            <div className="bg-[#0f172a] p-4 border-b border-gray-700 flex justify-between items-center">
              <h2 className="text-xl font-semibold text-[#FDECB2]">Response</h2>
              {modelUsed && (
                <div className="text-xs text-gray-400">
                  Generated by: <span className="text-[#1A9964]">{modelUsed.split('/')[1]}</span>
                </div>
              )}
            </div>
            
            <div className="p-5">
              <div className="bg-[#1B1B1B] rounded-lg p-6 min-h-[300px] border border-gray-700 shadow-inner">
                {isLoading ? (
                  <div className="flex justify-center items-center h-full">
                    <div className="flex flex-col items-center">
                      <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-[#EFD81D]"></div>
                      <p className="mt-4 text-gray-400 text-sm">Generating response...</p>
                    </div>
                  </div>
                ) : content ? (
                  <div className="prose prose-invert max-w-none text-gray-200 prose-headings:text-[#FDECB2] prose-a:text-[#663399]">
                    <div dangerouslySetInnerHTML={{ __html: content }}></div>
                  </div>
                ) : (
                  <div className="text-gray-400 text-sm flex flex-col justify-center items-center h-full">
                    <svg className="w-16 h-16 mb-4 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-4l-4 4z"></path>
                    </svg>
                    <p>Ask a question to get started</p>
                    <p className="mt-2 text-xs text-gray-500">Example: "What is the average speed of the ferries?"</p>
                  </div>
                )}
              </div>
              
              {/* Data visualization placeholder - Empty for future implementation */}
              <div className="mt-6 bg-[#1B1B1B] rounded-lg p-5 border border-gray-700">
                <h3 className="text-lg font-semibold text-white mb-4">Data Visualization</h3>
                <div className="h-64 w-full flex items-center justify-center">
                  <div className="text-center text-gray-500">
                    <svg className="w-16 h-16 mx-auto mb-4 text-gray-700 opacity-50" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M8 13v-1m4 1v-3m4 3V8M8 21l4-4 4 4M3 4h18M4 4h16v12a1 1 0 01-1 1H5a1 1 0 01-1-1V4z"></path>
                    </svg>
                    <p className="text-sm">Ready for data visualization</p>
                    <p className="text-xs mt-2">This area will display charts and graphs based on query results</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}