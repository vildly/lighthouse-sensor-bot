import Link from 'next/link';
import { useWebSocket } from '../contexts/WebSocketContext';
import Image from 'next/image';
import { useState, useEffect } from 'react';

export default function Navigation() {
  const { connected } = useWebSocket();
  const [backendStatus, setBackendStatus] = useState("offline");
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  // Check backend status on component mount
  useEffect(() => {
    testConnection(false);
  }, []);

  const closeMobileMenu = () => {
    setIsMobileMenuOpen(false);
  };

  // Prevent body scroll when mobile menu is open
  useEffect(() => {
    if (isMobileMenuOpen) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = 'unset';
    }
    
    // Cleanup on unmount
    return () => {
      document.body.style.overflow = 'unset';
    };
  }, [isMobileMenuOpen]);

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
    <>
      <nav className="rounded-full mx-2 md:mx-16 mt-4 mb-4 shadow-lg" style={{
        background: 'linear-gradient(135deg, #4A5DCF 0%, #6366F1 50%, #7C3AED 100%)',
        boxShadow: '0 4px 20px rgba(79, 70, 229, 0.3)'
      }}>
        <div className="container mx-auto px-3 md:px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <Link href="/">
                <a className="flex items-center space-x-3" onClick={closeMobileMenu}>
                  <Image
                    src="/logo.png"
                    alt="Lighthouse Bot Logo"
                    width={32}
                    height={32}
                    className="w-8 h-8"
                  />
                  <h1 className="text-lg md:text-xl font-bold text-white">Lighthouse Bot</h1>
                </a>
              </Link>
            </div>

            {/* Desktop Navigation */}
            <div className="hidden lg:flex items-center space-x-6">
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
              <div className="flex items-center">
                <span className={`backend-status-indicator ${backendStatus === "online" ? 'online' : 'offline'}`}></span>
                <span className="ml-3 text-white font-medium">
                  Backend {backendStatus === "online" ? 'connected' : 'disconnected'}
                </span>
              </div>
            </div>

            {/* Mobile Navigation - Hamburger Button and Status */}
            <div className="lg:hidden flex items-center space-x-3">
              {/* Backend Status Indicator for Mobile */}
              <div className="flex items-center">
                <span className={`backend-status-indicator ${backendStatus === "online" ? 'online' : 'offline'}`}></span>
              </div>
              
              {/* Hamburger Button */}
              <button
                onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
                className="text-white hover:text-gray-300 focus:outline-none focus:text-gray-300 transition-colors"
                aria-label="Toggle mobile menu"
              >
                <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  {isMobileMenuOpen ? (
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  ) : (
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
                  )}
                </svg>
              </button>
            </div>
          </div>
        </div>
      </nav>

      {/* Full-Screen Mobile Menu Overlay */}
      {isMobileMenuOpen && (
        <div 
          className="lg:hidden fixed inset-0 z-50" 
          style={{
            background: 'linear-gradient(135deg, #4A5DCF 0%, #6366F1 50%, #7C3AED 100%)',
            backdropFilter: 'blur(5px)'
          }}
        >
          <div className="flex flex-col h-full">
            {/* Header with Close Button */}
            <div className="flex justify-between items-center p-6 border-b border-white border-opacity-20">
              <Link href="/">
                <a className="flex items-center space-x-3" onClick={closeMobileMenu}>
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
              <button
                onClick={closeMobileMenu}
                className="text-white hover:text-gray-200 focus:outline-none transition-colors"
                aria-label="Close mobile menu"
              >
                <svg className="h-8 w-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            {/* Navigation Items - Left-aligned and Middle-Upper Position */}
            <div className="flex-1 flex flex-col justify-start items-start space-y-8 px-6 pt-24">
              <Link href="/">
                <a 
                  className="text-white hover:text-gray-200 transition-colors font-semibold text-2xl flex items-center space-x-4"
                  onClick={closeMobileMenu}
                >
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-8 w-8" viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-8-3a1 1 0 00-.867.5 1 1 0 11-1.731-1A3 3 0 0113 8a3.001 3.001 0 01-2 2.83V11a1 1 0 11-2 0v-1a1 1 0 011-1 1 1 0 100-2zm0 8a1 1 0 100-2 1 1 0 000 2z" clipRule="evenodd" />
                  </svg>
                  <span>New Query</span>
                </a>
              </Link>
              
              <Link href="/query-history">
                <a 
                  className="text-white hover:text-gray-200 transition-colors font-semibold text-2xl flex items-center space-x-4"
                  onClick={closeMobileMenu}
                >
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-8 w-8" viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-12a1 1 0 10-2 0v4a1 1 0 00.293.707l2.828 2.829a1 1 0 101.415-1.415L11 9.586V6z" clipRule="evenodd" />
                  </svg>
                  <span>Query History</span>
                </a>
              </Link>

              <Link href="/about">
                <a 
                  className="text-white hover:text-gray-200 transition-colors font-semibold text-2xl flex items-center space-x-4"
                  onClick={closeMobileMenu}
                >
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-8 w-8" viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-8-3a1 1 0 00-.867.5 1 1 0 11-1.731-1A3 3 0 0113 8a3.001 3.001 0 01-2 2.83V11a1 1 0 11-2 0v-1a1 1 0 011-1 1 1 0 100-2zm0 8a1 1 0 100-2 1 1 0 000 2z" clipRule="evenodd" />
                  </svg>
                  <span>About</span>
                </a>
              </Link>
            </div>

            {/* Footer with Backend Status */}
            <div className="p-6 border-t border-white border-opacity-20">
              <div className="flex items-center justify-center space-x-3">
                <span className={`backend-status-indicator ${backendStatus === "online" ? 'online' : 'offline'}`}></span>
                <span className="ml-3 text-white font-medium">
                  Backend {backendStatus === "online" ? 'connected' : 'disconnected'}
                </span>
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
