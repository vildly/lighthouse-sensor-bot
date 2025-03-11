import { useState, useEffect } from "react";

export default function QuestionForm() {
  const [question, setQuestion] = useState("");
  const [content, setContent] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [backendStatus, setBackendStatus] = useState("offline");
  const [sourceFile, setSourceFile] = useState("ferries.json"); // Default source file.

  const askQuestion = async () => {
    if (!question.trim()) return;
    
    setIsLoading(true);
    setContent(null);
    
    try {
      const response = await fetch("/api/query", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ 
          question,
          source_file: sourceFile // Include the selected source file.
        }),
      });
      
      if (!response.ok) {
        throw new Error(`Failed to get response: ${response.status} ${response.statusText}`);
      }
  
      const data = await response.json();
      
      if (data.content) {
        setContent(data.content);
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

  const testConnection = async () => {
    try {
      const response = await fetch("/api/test");
      const data = await response.json();
      alert(`Backend connection test: ${data.content || "Failed"}`);
    } catch (error) {
      alert(`Backend connection test failed: ${error.message}`);
    }
  };
  
  const loadPrompt = async () => {
    try {
      const response = await fetch("/api/load-prompt");
      const data = await response.json();
      if (data.content) {
        setQuestion(data.content);
      } else {
        alert("Failed to load prompt");
      }
    } catch (error) {
      alert(`Failed to load prompt: ${error.message}`);
    }
  };

  const checkBackendStatus = async () => {
    try {
      const response = await fetch("/api/test");
      const data = await response.json();
      if (data.content && data.content.includes("successful")) {
        setBackendStatus("online");
      } else {
        setBackendStatus("offline");
      }
    } catch (error) {
      setBackendStatus("offline");
    }
  };

  useEffect(() => {
    checkBackendStatus();
    const interval = setInterval(checkBackendStatus, 30000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="min-h-screen bg-[#1c1c1e] text-gray-200">
      <div className="container mx-auto px-4 py-8 max-w-4xl">
        <header className="mb-8 flex justify-between items-center">
          <h1 className="text-xl font-medium text-gray-100">Maritime AI Analysis</h1>
          <div className="flex items-center">
            <div className={`px-3 py-1 rounded-full text-xs font-medium ${
              backendStatus === "online" ? "bg-green-900 text-green-300" : 
              "bg-red-900 text-red-300"
            }`}>
              Backend: {backendStatus}
            </div>
          </div>
        </header>
        
        <div className="bg-[#262626] rounded-md shadow-lg overflow-hidden border border-gray-700">
          {/* Query Section */}
          <div className="p-5 border-b border-gray-700">
            <h3 className="text-sm font-medium text-gray-300 mb-3">Maritime Query</h3>
            
            <div className="mb-4">
              <textarea
                rows="3"
                className="w-full p-3 bg-[#333333] border border-gray-600 rounded-md text-sm focus:ring-1 focus:ring-blue-500 focus:border-blue-500 text-gray-200"
                placeholder="Examples: Which ferry is the most powerful ?"
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
              ></textarea>
            </div>
            
            {/* Source File Selection */}
            <div className="mb-4">
              <div className="flex justify-between items-center">
                <h4 className="text-sm font-medium text-gray-300">Select Data Source:</h4>
                <button
                  onClick={loadPrompt}
                  className="px-3 py-1 rounded-md text-xs font-medium bg-purple-600 hover:bg-purple-700 text-white"
                >
                  Test case 1
                </button>
              </div>
              <div className="flex space-x-2 mt-2">
                <button
                  onClick={() => setSourceFile("ferries.json")}
                  className={`px-3 py-1 rounded-md text-xs font-medium ${
                    sourceFile === "ferries.json" 
                      ? "bg-blue-600 text-white" 
                      : "bg-[#333333] text-gray-300 hover:bg-[#3a3a3a]"
                  }`}
                >
                  ferries.json
                </button>
                <button
                  onClick={() => setSourceFile("ferry_trips_data.csv")}
                  className={`px-3 py-1 rounded-md text-xs font-medium ${
                    sourceFile === "ferry_trips_data.csv" 
                      ? "bg-blue-600 text-white" 
                      : "bg-[#333333] text-gray-300 hover:bg-[#3a3a3a]"
                  }`}
                >
                  ferry_trips_data.csv
                </button>
              </div>
            </div>
            
            <div className="flex justify-between items-center">
              <button 
                onClick={askQuestion}
                disabled={isLoading || !question.trim()}
                className={`px-4 py-2 rounded-md text-sm font-medium text-white ${
                  isLoading || !question.trim() ? 'bg-green-700 opacity-50' : 'bg-green-600 hover:bg-green-700'
                }`}
              >
                {isLoading ? 'Processing...' : 'Send'}
              </button>
              <button 
                onClick={testConnection}
                className="px-4 py-2 bg-[#333333] hover:bg-[#3a3a3a] rounded-md text-sm font-medium text-gray-300"
              >
                Test Connection
              </button>
            </div>
          </div>
          
          {/* Response Section */}
          <div className="p-5">
            <div className="flex justify-between items-center mb-3">
              <h3 className="text-sm font-medium text-gray-300">Response</h3>
              <div className="text-xs text-gray-400">Source: {sourceFile}</div>
            </div>
            <div className="bg-[#333333] rounded-md p-4 min-h-[200px] border border-gray-600">
              {isLoading ? (
                <div className="flex justify-center items-center h-full">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
                </div>
              ) : content ? (
                <div className="prose prose-sm max-w-none text-gray-300">
                  {content}
                </div>
              ) : (
                <div className="text-gray-500 text-sm flex justify-center items-center h-full">
                  Enter your question and click Send to get a response
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}