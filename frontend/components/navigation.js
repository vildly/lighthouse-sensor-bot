import Link from 'next/link';
import { useWebSocket } from '../contexts/WebSocketContext';

export default function Navigation() {
  const { connected } = useWebSocket();
  
  return (
    <header className="pt-4">
      <div className="arc-navbar">
        <div className="container mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <Link href="/">
                <a className="flex items-center space-x-3">
                  <svg className="w-8 h-8 text-white" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M3 18H21L19 22H5L3 18Z" fill="currentColor" />
                    <path d="M19 18L21 8H3L5 18" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                    <path d="M15 18V8" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                    <path d="M9 18V8" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                    <path d="M12 8V4" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                    <path d="M8 4H16" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                  </svg>
                  <h1 className="text-xl font-bold text-white">Lighthouse</h1>
                </a>
              </Link>
            </div>

            <div className="flex items-center space-x-6">
              <Link href="/">
                <a className="text-white hover:text-gray-300 transition-colors font-medium">
                  Query
                </a>
              </Link>
              <Link href="/model-performance">
                <a className="text-white hover:text-gray-300 transition-colors font-medium flex items-center">
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-1" viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" d="M3 3a1 1 0 011-1h12a1 1 0 011 1v12a1 1 0 01-1 1H4a1 1 0 01-1-1V3zm1 0v12h12V3H4z" clipRule="evenodd" />
                    <path d="M7 6a1 1 0 011-1h4a1 1 0 110 2H8a1 1 0 01-1-1z" />
                    <path d="M5 9a1 1 0 011-1h8a1 1 0 110 2H6a1 1 0 01-1-1z" />
                    <path d="M6 12a1 1 0 011-1h2a1 1 0 110 2H7a1 1 0 01-1-1z" />
                  </svg>
                  Evaluation
                </a>
              </Link>
              <div className="flex items-center">
                <span className={`backend-status-indicator ${connected ? 'online' : 'offline'}`}></span>
                <span className="ml-2 text-sm text-white text-opacity-80">
                  Backend {connected ? 'connected' : 'disconnected'}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </header>
  );
}
