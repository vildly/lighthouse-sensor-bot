import Link from 'next/link';
import { useWebSocket } from '../contexts/WebSocketContext';
import Image from 'next/image';
import { useState, useEffect } from 'react';

export default function Navigation() {
  const { connected } = useWebSocket();
  const [backendStatus, setBackendStatus] = useState("offline");

  // Check backend status on component mount
  useEffect(() => {
    testConnection(false);
  }, []);

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

  return (
    <nav className="rounded-full mx-16 mt-4 mb-4 shadow-lg" style={{
      background: 'linear-gradient(135deg, #4A5DCF 0%, #6366F1 50%, #7C3AED 100%)',
      boxShadow: '0 4px 20px rgba(79, 70, 229, 0.3)'
    }}>
      <div className="container mx-auto px-6 py-4">
        <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <Link href="/">
                <a className="flex items-center space-x-3">
                  <Image
                    src="/logo.png"
                    alt="Lighthouse Bot Logo"
                    width={32}
                    height={32}
                    className="w-8 h-8"
                  />
                  <h1 className="text-xl font-bold text-white">Lighthouse Bot</h1>
                </a>
              </Link>
            </div>

            <div className="flex items-center space-x-6">
              <Link href="/">
                <a className="text-white hover:text-gray-300 transition-colors font-medium flex items-center">
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-1" viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-8-3a1 1 0 00-.867.5 1 1 0 11-1.731-1A3 3 0 0113 8a3.001 3.001 0 01-2 2.83V11a1 1 0 11-2 0v-1a1 1 0 011-1 1 1 0 100-2zm0 8a1 1 0 100-2 1 1 0 000 2z" clipRule="evenodd" />
                  </svg>
                  New Query
                </a>
              </Link>
              <Link href="/query-history">
                <a className="text-white hover:text-gray-300 transition-colors font-medium flex items-center">
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-1" viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-12a1 1 0 10-2 0v4a1 1 0 00.293.707l2.828 2.829a1 1 0 101.415-1.415L11 9.586V6z" clipRule="evenodd" />
                  </svg>
                  Query History
                </a>
              </Link>
              <Link href="/about">
                <a className="text-white hover:text-gray-300 transition-colors font-medium flex items-center">
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-1" viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-8-3a1 1 0 00-.867.5 1 1 0 11-1.731-1A3 3 0 0113 8a3.001 3.001 0 01-2 2.83V11a1 1 0 11-2 0v-1a1 1 0 011-1 1 1 0 100-2zm0 8a1 1 0 100-2 1 1 0 000 2z" clipRule="evenodd" />
                  </svg>
                  About
                </a>
              </Link>
              {/* COMMENTED OUT - Evaluation Mode functionality */}
              {/* <Link href="/model-performance">
                <a className="text-white hover:text-gray-300 transition-colors font-medium flex items-center">
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-1" viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" d="M3 3a1 1 0 011-1h12a1 1 0 011 1v12a1 1 0 01-1 1H4a1 1 0 01-1-1V3zm1 0v12h12V3H4z" clipRule="evenodd" />
                    <path d="M7 6a1 1 0 011-1h4a1 1 0 110 2H8a1 1 0 01-1-1z" />
                    <path d="M5 9a1 1 0 011-1h8a1 1 0 110 2H6a1 1 0 01-1-1z" />
                    <path d="M6 12a1 1 0 011-1h2a1 1 0 110 2H7a1 1 0 01-1-1z" />
                  </svg>
                  Analytics
                </a>
              </Link> */}
              {/* COMMENTED OUT - Evaluation Mode functionality */}
              {/* <Link href="/history">
                <a className="text-white hover:text-gray-300 transition-colors font-medium flex items-center">
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-1" viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-12a1 1 0 10-2 0v4a1 1 0 00.293.707l2.828 2.829a1 1 0 101.415-1.415L11 9.586V6z" clipRule="evenodd" />
                  </svg>
                  History
                </a>
              </Link> */}
              <div className="flex items-center">
                <span className={`backend-status-indicator ${backendStatus === "online" ? 'online' : 'offline'}`}></span>
                <span className="ml-2 text-sm text-white text-opacity-80">
                  Backend {backendStatus === "online" ? 'connected' : 'disconnected'}
                </span>
              </div>
            </div>
          </div>
        </div>
    </nav>
  );
}
