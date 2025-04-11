import Link from 'next/link';
import { useWebSocket } from '../contexts/WebSocketContext';
import Image from 'next/image';

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
