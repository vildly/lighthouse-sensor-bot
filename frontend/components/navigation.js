import Link from 'next/link';

export default function Navigation() {
  return (
    <nav className="navigation">
      <Link href="/" className="nav-link">Home</Link>
      
      <Link href="/model-performance" className="nav-link">
        <span className="flex items-center">
          <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2" viewBox="0 0 20 20" fill="currentColor">
            <path fillRule="evenodd" d="M3 3a1 1 0 011-1h12a1 1 0 011 1v12a1 1 0 01-1 1H4a1 1 0 01-1-1V3zm1 0v12h12V3H4z" clipRule="evenodd" />
            <path d="M7 6a1 1 0 011-1h4a1 1 0 110 2H8a1 1 0 01-1-1z" />
            <path d="M5 9a1 1 0 011-1h8a1 1 0 110 2H6a1 1 0 01-1-1z" />
            <path d="M6 12a1 1 0 011-1h2a1 1 0 110 2H7a1 1 0 01-1-1z" />
          </svg>
          Performance Dashboard
        </span>
      </Link>
    
    </nav>
  );
}
