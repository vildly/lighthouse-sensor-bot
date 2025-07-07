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

          {/* Database Information Section */}
          <div className="bg-white bg-opacity-95 rounded-xl p-6 shadow-lg border border-gray-100 mb-6">
            <h2 className="text-xl font-semibold text-gray-800 mb-4">📊 Ferry Database Overview</h2>
            
            <div className="mb-6">
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-4">
                <div className="flex items-center justify-between mb-2">
                  <h3 className="text-lg font-medium text-blue-800">🚢 Ferry Fleet Data</h3>
                  <a 
                    href="https://github.com/RISE-Maritime/hack-a-fleet" 
                    target="_blank" 
                    rel="noopener noreferrer"
                    className="text-blue-600 hover:text-blue-800 underline text-sm"
                  >
                    🔗 View Source Data
                  </a>
                </div>
                <p className="text-blue-700 text-sm">
                  Our database contains real-world operational data from Färjerederiet's ferry fleet, 
                  covering the period from <strong>March 2023 to February 2024</strong>.
                </p>
              </div>

              <div className="grid md:grid-cols-2 gap-6">
                {/* Ferry Fleet */}
                <div>
                  <h4 className="font-semibold text-gray-800 mb-3">🚢 Available Ferries (5 Vessels)</h4>
                  <div className="space-y-2">
                    <div className="flex items-center bg-gray-50 p-2 rounded">
                      <span className="font-mono text-sm bg-blue-100 text-blue-800 px-2 py-1 rounded mr-2">Fragancia</span>
                      <span className="text-gray-600 text-sm">Ferry operations & routes</span>
                    </div>
                    <div className="flex items-center bg-gray-50 p-2 rounded">
                      <span className="font-mono text-sm bg-green-100 text-green-800 px-2 py-1 rounded mr-2">Jupiter</span>
                      <span className="text-gray-600 text-sm">Ferry operations & routes</span>
                    </div>
                    <div className="flex items-center bg-gray-50 p-2 rounded">
                      <span className="font-mono text-sm bg-purple-100 text-purple-800 px-2 py-1 rounded mr-2">Merkurius</span>
                      <span className="text-gray-600 text-sm">Ferry operations & routes</span>
                    </div>
                    <div className="flex items-center bg-gray-50 p-2 rounded">
                      <span className="font-mono text-sm bg-orange-100 text-orange-800 px-2 py-1 rounded mr-2">Nina</span>
                      <span className="text-gray-600 text-sm">Ferry operations & routes</span>
                    </div>
                    <div className="flex items-center bg-gray-50 p-2 rounded">
                      <span className="font-mono text-sm bg-red-100 text-red-800 px-2 py-1 rounded mr-2">Yxlan</span>
                      <span className="text-gray-600 text-sm">Ferry operations & routes</span>
                    </div>
                  </div>
                </div>

                {/* Data Categories */}
                <div>
                  <h4 className="font-semibold text-gray-800 mb-3">📈 Available Data Categories</h4>
                  <div className="space-y-2 text-sm">
                    <div className="flex items-start">
                      <span className="text-blue-600 mr-2">🛳️</span>
                      <div>
                        <strong>Trip Operations:</strong> Departure/arrival times, routes, trip types (ordinary, extra, doubling)
                      </div>
                    </div>
                    <div className="flex items-start">
                      <span className="text-green-600 mr-2">⛽</span>
                      <div>
                        <strong>Performance Metrics:</strong> Fuel consumption, distances, speed, efficiency
                      </div>
                    </div>
                    <div className="flex items-start">
                      <span className="text-purple-600 mr-2">🚗</span>
                      <div>
                        <strong>Cargo & Passengers:</strong> Vehicle counts, passenger car equivalents, load statistics
                      </div>
                    </div>
                    <div className="flex items-start">
                      <span className="text-orange-600 mr-2">📍</span>
                      <div>
                        <strong>Route Information:</strong> Terminal locations, route descriptions, schedules
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Sample Questions */}
            <div className="bg-green-50 border border-green-200 rounded-lg p-4">
              <h4 className="font-semibold text-green-800 mb-3">💡 Example Questions You Can Ask</h4>
              <div className="grid md:grid-cols-2 gap-4 text-sm">
                <div>
                  <h5 className="font-medium text-green-700 mb-2">Performance Analysis:</h5>
                  <ul className="space-y-1 text-green-700">
                    <li>• "What is the average fuel consumption of ferry Jupiter?"</li>
                    <li>• "Which ferry has the best fuel efficiency?"</li>
                    <li>• "Compare the average speed of all ferries"</li>
                    <li>• "Show me the longest trips by distance"</li>
                  </ul>
                </div>
                <div>
                  <h5 className="font-medium text-green-700 mb-2">Operations & Traffic:</h5>
                  <ul className="space-y-1 text-green-700">
                    <li>• "What are the busiest routes by passenger volume?"</li>
                    <li>• "How many extra trips were made in 2023?"</li>
                    <li>• "Which ferry carries the most vehicles on average?"</li>
                    <li>• "Show passenger patterns by month"</li>
                  </ul>
                </div>
              </div>
            </div>

            {/* Database Fields */}
            <div className="mt-6">
              <h4 className="font-semibold text-gray-800 mb-3">🗃️ Key Database Fields</h4>
              <div className="bg-gray-50 rounded-lg p-4 text-xs">
                <div className="grid md:grid-cols-3 gap-4">
                  <div>
                    <h5 className="font-medium text-gray-700 mb-2">Trip Information:</h5>
                    <code className="block text-gray-600">
                      time_departure<br/>
                      trip_type<br/>
                      tailored_trip<br/>
                      start_time_outbound<br/>
                      end_time_outbound
                    </code>
                  </div>
                  <div>
                    <h5 className="font-medium text-gray-700 mb-2">Performance Data:</h5>
                    <code className="block text-gray-600">
                      distance_outbound_nm<br/>
                      fuelcons_outbound_l<br/>
                      distance_inbound_nm<br/>
                      fuelcons_inbound_l
                    </code>
                  </div>
                  <div>
                    <h5 className="font-medium text-gray-700 mb-2">Load & Capacity:</h5>
                    <code className="block text-gray-600">
                      passenger_car_equivalent_outbound<br/>
                      passenger_car_equivalent_inbound<br/>
                      vehicles_left_at_terminal_outbound<br/>
                      vehicles_left_at_terminal_inbound
                    </code>
                  </div>
                </div>
              </div>
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

              <div className="border-l-4 border-amber-500 pl-4">
                <h3 className="font-medium text-gray-800 mb-1">🗃️ Raw Ferry Data Source</h3>
                <p className="text-gray-700 text-sm mb-2">
                  The ferry operational data used in this platform is part of the Hack-A-Fleet v2.0 dataset from RISE Maritime:
                </p>
                <a 
                  href="https://github.com/RISE-Maritime/hack-a-fleet" 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="text-amber-600 hover:text-amber-800 underline text-sm"
                >
                  🔗 RISE Maritime - Hack-A-Fleet Dataset (ferry_trips_data.csv)
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