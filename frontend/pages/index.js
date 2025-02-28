import { useState, useEffect } from "react";

// This is a simple form that allows the user to ask a question and receive a response.
export default function QuestionForm() {
  const [question, setQuestion] = useState("");
  const [content, setContent] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [selectedFile, setSelectedFile] = useState(null);
  const [backendStatus, setBackendStatus] = useState("unknown"); // "unknown", "online", "offline"

  const askQuestion = async () => {
    if (!question.trim()) return;
    
    setIsLoading(true);
    setContent(null); // Clear previous content
    
    try {
      console.log("Sending question to API:", question);
      const response = await fetch("/api/query", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ question }),
      });
  
      console.log("API response status:", response.status);
      
      if (!response.ok) {
        console.error("API response not OK:", response.status, response.statusText);
        throw new Error(`Failed to get response: ${response.status} ${response.statusText}`);
      }
  
      const data = await response.json();
      console.log("Received data from API:", data);
      
      if (data.content) {
        console.log("Setting content to:", data.content);
        setContent(data.content);
      } else {
        console.log("No content found in response data:", data);
        setContent("No content available. Response format may be incorrect.");
      }
    } catch (error) {
      console.error("Error fetching response:", error);
      setContent(`Failed to fetch response: ${error.message}`);
      setBackendStatus("offline"); // Update backend status on error
    } finally {
      setIsLoading(false);
    }
  };

  const analyzeFile = async (filename) => {
    setIsLoading(true);
    try {
      const response = await fetch("/api/query", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ 
          prompt_file: filename 
        }),
      });

      if (!response.ok) throw new Error("Failed to get response");

      const data = await response.json();
      setContent(data.content || "No content available.");
    } catch (error) {
      console.error("Error fetching response:", error);
      setContent("Failed to fetch response.");
    } finally {
      setIsLoading(false);
    }
  };

  const testConnection = async () => {
    try {
      const response = await fetch("/api/test");
      const data = await response.json();
      console.log("Test connection result:", data);
      alert(`Backend connection test: ${data.content || "Failed"}`);
    } catch (error) {
      console.error("Test connection failed:", error);
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
      console.error("Backend status check failed:", error);
      setBackendStatus("offline");
    }
  };

  useEffect(() => {
    checkBackendStatus();
    // Check status every 30 seconds
    const interval = setInterval(checkBackendStatus, 30000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      <div className="container mx-auto px-4 py-8">
        <h1 className="text-3xl font-bold text-center mb-8">Maritime AI Analysis</h1>
        
        <div className="max-w-3xl mx-auto bg-gray-800 rounded-lg p-6 shadow-lg">
          <div className="mb-6">
            <label className="block text-lg mb-2">Select AI Model:</label>
            <select 
              className="w-full p-3 bg-gray-700 border border-gray-600 rounded-lg text-white"
              defaultValue="default-model"
            >
              <option value="default-model">🇺🇸 GPT-3.5 Turbo (Technical & Maritime Analysis)</option>
            </select>
          </div>
          
          <div className="mb-6">
            <label className="block text-lg mb-2">Your Maritime Question:</label>
            <textarea
              rows="4"
              className="w-full p-3 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-400"
              placeholder="Examples: • Analyze vessel stability • Calculate fuel consumption • Optimize route between ports"
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
            ></textarea>
          </div>
          
          <div className="mb-6">
            <label className="block text-lg mb-2">Analysis Files:</label>
            <div className="grid grid-cols-2 gap-3">
              <button 
                onClick={() => analyzeFile("ferry_analysis.txt")}
                className="p-3 bg-gray-700 hover:bg-gray-600 rounded-lg text-center"
              >
                Ferry Analysis
              </button>
              <button 
                onClick={() => analyzeFile("my_analysis.txt")}
                className="p-3 bg-gray-700 hover:bg-gray-600 rounded-lg text-center"
              >
                Trip Data Analysis
              </button>
            </div>
          </div>
          
          <button
            onClick={askQuestion}
            disabled={isLoading}
            className="w-full py-3 bg-blue-600 hover:bg-blue-700 rounded-lg font-medium transition-colors"
          >
            {isLoading ? "Analyzing..." : "Analyze"}
          </button>
          
          {content && (
            <div className="mt-8 bg-gray-700 p-5 rounded-lg">
              <h2 className="font-semibold text-xl mb-3">Analysis Results:</h2>
              <div className="prose prose-invert max-w-none">
                <pre className="whitespace-pre-wrap text-sm">{content}</pre>
              </div>
            </div>
          )}
          
          <button 
            onClick={testConnection}
            className="text-xs text-gray-400 hover:text-white mt-2"
          >
            Test Connection
          </button>
          
          <div className="text-xs mt-2 flex items-center">
            <span className="mr-2">Backend:</span>
            <span className={`inline-block w-2 h-2 rounded-full mr-1 ${
              backendStatus === "online" ? "bg-green-500" : 
              backendStatus === "offline" ? "bg-red-500" : "bg-yellow-500"
            }`}></span>
            <span className={
              backendStatus === "online" ? "text-green-500" : 
              backendStatus === "offline" ? "text-red-500" : "text-yellow-500"
            }>
              {backendStatus === "online" ? "Online" : 
               backendStatus === "offline" ? "Offline" : "Checking..."}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
