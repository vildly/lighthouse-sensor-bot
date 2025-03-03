// pages/index.js
import { useState, useEffect } from "react";

export default function QuestionForm() {
  const [question, setQuestion] = useState("");
  const [content, setContent] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [backendStatus, setBackendStatus] = useState("offline");

  // Keep all existing functions
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
        body: JSON.stringify({ question }),
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
                placeholder="Examples: Which ferry is the most powerful? Based on ferries-info!"
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
              ></textarea>
            </div>
            
            <div className="flex space-x-2">
              <button 
                onClick={askQuestion}
                disabled={isLoading || !question.trim()}
                className={`px-4 py-2 rounded-md text-sm font-medium text-white ${
                  isLoading || !question.trim() ? 'bg-blue-700 opacity-50' : 'bg-blue-600 hover:bg-blue-700'
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