import { useState, useEffect } from 'react';

export default function ApiKeyManager({ onApiKeyChange }) {
  const [apiKey, setApiKey] = useState('');
  const [showApiKey, setShowApiKey] = useState(false);
  const [isConfigured, setIsConfigured] = useState(false);

  useEffect(() => {
    // Check if API key exists in session storage (not localStorage for GDPR compliance)
    const savedApiKey = sessionStorage.getItem('openrouter-api-key');
    if (savedApiKey) {
      setApiKey(savedApiKey);
      setIsConfigured(true);
      if (onApiKeyChange) {
        onApiKeyChange(savedApiKey);
      }
    }
  }, [onApiKeyChange]);

  const handleApiKeyChange = (e) => {
    const newApiKey = e.target.value;
    setApiKey(newApiKey);
    
    if (newApiKey.trim()) {
      // Store in session storage only (automatically deleted when browser closes)
      sessionStorage.setItem('openrouter-api-key', newApiKey);
      setIsConfigured(true);
    } else {
      // Remove from session storage if empty
      sessionStorage.removeItem('openrouter-api-key');
      setIsConfigured(false);
    }
    
    if (onApiKeyChange) {
      onApiKeyChange(newApiKey);
    }
  };

  const clearApiKey = () => {
    setApiKey('');
    setIsConfigured(false);
    sessionStorage.removeItem('openrouter-api-key');
    if (onApiKeyChange) {
      onApiKeyChange('');
    }
  };

  return (
    <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 mb-4">
      <div className="flex items-start space-x-2">
        <div className="flex-shrink-0">
          <svg className="w-4 h-4 text-blue-600 mt-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 7a2 2 0 012 2m4 0a6 6 0 01-7.029 5.912c-.563-.097-1.159-.026-1.669.189L10.5 16.5l-1.414-1.414L12 12.5V9a3 3 0 116 0z" />
          </svg>
        </div>
        
        <div className="flex-1 min-w-0">
          <h3 className="text-blue-800 font-medium mb-2 text-sm">OpenRouter API Key Required</h3>
          
          <div className="space-y-2">
            <div className="flex flex-col gap-2">
              <div className="relative">
                <input
                  type={showApiKey ? "text" : "password"}
                  value={apiKey}
                  onChange={handleApiKeyChange}
                  placeholder="Enter OpenRouter API key..."
                  className="w-full px-2 py-1.5 border border-blue-300 rounded text-xs focus:ring-1 focus:ring-blue-500 focus:border-transparent"
                />
                <button
                  type="button"
                  onClick={() => setShowApiKey(!showApiKey)}
                  className="absolute right-1.5 top-1/2 transform -translate-y-1/2 text-gray-500 hover:text-gray-700"
                >
                  {showApiKey ? (
                    <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.878 9.878L3 3m6.878 6.878L21 21" />
                    </svg>
                  ) : (
                    <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                    </svg>
                  )}
                </button>
              </div>
              
              {isConfigured && (
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-1 text-green-700 text-xs">
                    <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    <span>Configured</span>
                  </div>
                  <button
                    onClick={clearApiKey}
                    className="px-2 py-1 bg-red-600 text-white rounded text-xs hover:bg-red-700 transition-colors"
                  >
                    Clear
                  </button>
                </div>
              )}
            </div>
            
            <div className="bg-white border border-blue-200 rounded p-2">
              <p className="text-xs text-blue-800 font-medium mb-1">🔒 Session-only storage</p>
              <p className="text-xs text-blue-600">
                Need a key? <a href="https://openrouter.ai/keys" target="_blank" rel="noopener noreferrer" className="underline hover:no-underline">Get from OpenRouter</a>
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
} 