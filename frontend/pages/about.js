import { useState } from 'react';

export default function About() {
  return (
    <div className="bg-ferry-image min-h-screen">
      <main className="container mx-auto py-6 px-4">
        <div className="max-w-6xl mx-auto">
          {/* Page Header */}
          <div className="bg-white bg-opacity-95 rounded-xl p-6 shadow-lg border border-gray-100 mb-6">
            <div className="text-center mb-6">
              <h1 className="text-3xl font-bold text-gray-800 mb-2">About Lighthouse Sensor Bot</h1>
              <p className="text-gray-600">AI-Powered Maritime Data Analysis Platform</p>
            </div>
          </div>

          {/* Introduction Section */}
          <div className="bg-white bg-opacity-95 rounded-xl p-6 shadow-lg border border-gray-100 mb-6">
            <h2 className="text-xl font-semibold text-gray-800 mb-4">What is Lighthouse Sensor Bot?</h2>
            <p className="text-gray-700 leading-relaxed mb-4">
              Lighthouse Sensor Bot is a data analysis application that uses natural language queries to analyze 
              maritime ferry data using agentic Retrieval-Augmented Generation (RAG). The platform allows users 
              to ask questions about ferry operations, routes, passenger traffic, and performance metrics in plain English, 
              and receive detailed analytical responses backed by real data.
            </p>
            <p className="text-gray-700 leading-relaxed">
              This innovative platform bridges the gap between complex maritime data and accessible insights, 
              making data analysis available to both technical and non-technical users in the maritime industry.
            </p>
          </div>

          {/* How to Use Section */}
          <div className="bg-white bg-opacity-95 rounded-xl p-6 shadow-lg border border-gray-100 mb-6">
            <h2 className="text-xl font-semibold text-gray-800 mb-4">How to Use This Platform</h2>
            
            <div className="mb-4">
              <h3 className="text-lg font-medium text-gray-800 mb-2">🔑 API Key Requirement</h3>
              <p className="text-gray-700 leading-relaxed mb-3">
                To use this application, you need an <strong>OpenRouter API key</strong>. This key enables access 
                to various Large Language Models (LLMs) for processing your queries.
              </p>
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
                <p className="text-blue-800 text-sm">
                  <strong>Note:</strong> The platform is designed for querying and analysis only. 
                  Advanced features like model evaluation are available through the source code.
                </p>
              </div>
            </div>

            <div className="mb-4">
              <h3 className="text-lg font-medium text-gray-800 mb-2">📊 Getting Started</h3>
              <ol className="list-decimal list-inside text-gray-700 space-y-2">
                <li>Select a language model from the dropdown menu</li>
                <li>Enter your question about ferry data (e.g., "What is the average speed of ferry Jupiter?")</li>
                <li>View comprehensive responses including SQL queries and analysis</li>
                <li>Access your query history to track previous analyses</li>
              </ol>
            </div>
          </div>

          {/* More Information Section */}
          <div className="bg-white bg-opacity-95 rounded-xl p-6 shadow-lg border border-gray-100 mb-6">
            <h2 className="text-xl font-semibold text-gray-800 mb-4">Learn More</h2>
            
            <div className="space-y-4">
              <div className="border-l-4 border-blue-500 pl-4">
                <h3 className="font-medium text-gray-800 mb-1">📚 Full Documentation & Source Code</h3>
                <p className="text-gray-700 text-sm mb-2">
                  For detailed setup instructions, evaluation features, and technical documentation:
                </p>
                <a 
                  href="https://github.com/vildly/lighthouse-sensor-bot" 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="text-blue-600 hover:text-blue-800 underline text-sm"
                >
                  🔗 GitHub Repository - vildly/lighthouse-sensor-bot
                </a>
              </div>

              <div className="border-l-4 border-green-500 pl-4">
                <h3 className="font-medium text-gray-800 mb-1">🎓 Academic Research</h3>
                <p className="text-gray-700 text-sm mb-2">
                  This platform was developed as part of a bachelor's degree thesis evaluating LLMs for maritime data analysis:
                </p>
                <a 
                  href="https://www.diva-portal.org/smash/get/diva2:1969025/FULLTEXT02.pdf" 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="text-green-600 hover:text-green-800 underline text-sm"
                >
                  📄 "Lighthouse Bot: A Platform For Evaluating LLMs For Agentic Maritime Data Analysis"
                </a>
              </div>
            </div>
          </div>

          {/* Contributors Section */}
          <div className="bg-white bg-opacity-95 rounded-xl p-6 shadow-lg border border-gray-100 mb-6">
            <h2 className="text-xl font-semibold text-gray-800 mb-4">Contributors</h2>
            
            <div className="grid md:grid-cols-3 gap-6">
              <div className="text-center">
                <div className="w-16 h-16 bg-green-600 rounded-full flex items-center justify-center text-white text-xl font-bold mx-auto mb-3">
                  OS
                </div>
                <h3 className="font-medium text-gray-800">Oxana Sachenkova</h3>
                <p className="text-gray-600 text-sm">Supervisor & Contributor</p>
              </div>

              <div className="text-center">
                <div className="w-16 h-16 bg-blue-600 rounded-full flex items-center justify-center text-white text-xl font-bold mx-auto mb-3">
                  DT
                </div>
                <h3 className="font-medium text-gray-800">Dongzhu Tan</h3>
                <p className="text-gray-600 text-sm">Co-Developer & Researcher</p>
              </div>
              
              <div className="text-center">
                <div className="w-16 h-16 bg-purple-600 rounded-full flex items-center justify-center text-white text-xl font-bold mx-auto mb-3">
                  MA
                </div>
                <h3 className="font-medium text-gray-800">Melker Andreasson</h3>
                <p className="text-gray-600 text-sm">Co-Developer & Researcher</p>
              </div>
            </div>
            
            <div className="mt-6 text-center">
              <p className="text-gray-700 text-sm">
                This project was developed as part of a Computer Science bachelor's degree program, 
                focusing on evaluating Large Language Models for maritime data analysis applications. 
                Oxana Sachenkova served as the academic supervisor, guiding the research 
                and contributing to the application development.
              </p>
            </div>
          </div>

          {/* Technical Details Section */}
          <div className="bg-white bg-opacity-95 rounded-xl p-6 shadow-lg border border-gray-100">
            <h2 className="text-xl font-semibold text-gray-800 mb-4">Technical Overview</h2>
            
            <div className="grid md:grid-cols-3 gap-4">
              <div className="text-center p-4 bg-gray-50 rounded-lg">
                <div className="text-2xl mb-2">🖥️</div>
                <h3 className="font-medium text-gray-800 mb-1">Frontend</h3>
                <p className="text-gray-600 text-sm">Next.js interface for submitting queries and viewing results</p>
              </div>
              
              <div className="text-center p-4 bg-gray-50 rounded-lg">
                <div className="text-2xl mb-2">⚙️</div>
                <h3 className="font-medium text-gray-800 mb-1">Backend</h3>
                <p className="text-gray-600 text-sm">Flask server processing queries with LLM agents</p>
              </div>
              
              <div className="text-center p-4 bg-gray-50 rounded-lg">
                <div className="text-2xl mb-2">🗄️</div>
                <h3 className="font-medium text-gray-800 mb-1">Database</h3>
                <p className="text-gray-600 text-sm">PostgreSQL storing query results and evaluations</p>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
} 