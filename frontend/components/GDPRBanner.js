import { useState, useEffect } from 'react';

export default function GDPRBanner() {
  const [isVisible, setIsVisible] = useState(false);
  const [showPrivacyModal, setShowPrivacyModal] = useState(false);

  useEffect(() => {
    // Check if user has already accepted GDPR
    const gdprAccepted = localStorage.getItem('gdpr-accepted');
    if (!gdprAccepted) {
      setIsVisible(true);
    }
  }, []);

  // Prevent body scroll when modal is open
  useEffect(() => {
    if (showPrivacyModal) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = 'unset';
    }
    
    // Cleanup on unmount
    return () => {
      document.body.style.overflow = 'unset';
    };
  }, [showPrivacyModal]);

  const acceptGDPR = () => {
    localStorage.setItem('gdpr-accepted', 'true');
    setIsVisible(false);
  };

  const rejectAndClose = () => {
    setIsVisible(false);
    // Don't save acceptance, banner will show again on next visit
  };

  if (!isVisible) return null;

  return (
    <>
      {/* GDPR Banner */}
      <div className="fixed bottom-0 left-0 right-0 bg-gradient-to-r from-indigo-900 via-blue-900 to-purple-900 text-white p-4 shadow-2xl z-[9998] border-t-4 border-gradient-to-r from-cyan-400 to-blue-500">
        <div className="max-w-7xl mx-auto">
          <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
            <div className="flex-1">
              <div className="flex items-center mb-2">
                <div className="w-8 h-8 bg-gradient-to-br from-cyan-400 to-blue-500 rounded-full flex items-center justify-center mr-3 shadow-lg">
                  <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                  </svg>
                </div>
                <h3 className="font-bold text-base text-cyan-100">Privacy & Data Usage Notice</h3>
              </div>
              <p className="text-blue-100 text-sm leading-relaxed pl-11">
                This app processes data locally in your browser. We collect minimal data:
                <span className="inline ml-1 text-cyan-200 font-medium">
                  API Key (session-only), Query History (local device), No Server Storage
                </span>
              </p>
            </div>
            
            <div className="flex flex-row gap-3 lg:ml-6">
              <button
                onClick={() => setShowPrivacyModal(true)}
                className="px-4 py-2 bg-white bg-opacity-10 border border-white border-opacity-30 text-blue-100 rounded-lg hover:bg-opacity-20 hover:text-white transition-all duration-200 text-sm font-medium backdrop-blur-sm"
              >
                Privacy Policy
              </button>
              <button
                onClick={rejectAndClose}
                className="px-4 py-2 bg-white bg-opacity-10 border border-white border-opacity-30 text-blue-100 rounded-lg hover:bg-opacity-20 hover:text-white transition-all duration-200 text-sm font-medium backdrop-blur-sm"
              >
                Close
              </button>
              <button
                onClick={acceptGDPR}
                className="px-6 py-2 bg-gradient-to-r from-cyan-500 to-blue-500 text-white rounded-lg hover:from-cyan-600 hover:to-blue-600 transition-all duration-200 text-sm font-bold shadow-lg transform hover:scale-105"
              >
                I Understand
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Privacy Policy Modal */}
      {showPrivacyModal && (
        <div 
          className="fixed inset-0 bg-black bg-opacity-60 flex items-center justify-center p-4 z-[9999] backdrop-blur-sm"
          onClick={(e) => e.target === e.currentTarget && setShowPrivacyModal(false)}
        >
          <div 
            className="bg-white rounded-xl max-w-4xl w-full max-h-[90vh] overflow-hidden shadow-2xl relative z-[10000] flex flex-col"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="p-6 border-b border-gray-200 flex-shrink-0">
              <div className="flex items-center justify-between">
                <h2 className="text-2xl font-bold text-gray-800">Privacy Policy & GDPR Compliance</h2>
                <button
                  onClick={() => setShowPrivacyModal(false)}
                  className="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
                >
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
            </div>
            
            <div className="p-6 overflow-y-auto flex-1 space-y-6" style={{ maxHeight: 'calc(90vh - 180px)' }}>
              <section>
                <h3 className="text-lg font-semibold text-gray-800 mb-3">Data Collection & Processing</h3>
                <div className="bg-green-50 border border-green-200 rounded-lg p-4 mb-4">
                  <p className="text-green-800 font-medium">✓ Privacy-First Design</p>
                  <p className="text-green-700 text-sm mt-1">All your data stays on your device. We don't collect or store personal information on our servers.</p>
                </div>
                
                <div className="space-y-3 text-gray-700">
                  <p><strong>OpenRouter API Key:</strong></p>
                  <ul className="list-disc pl-6 space-y-1 text-sm">
                    <li>Stored only in your browser's session storage</li>
                    <li>Automatically deleted when you close the application</li>
                    <li>Never transmitted to or stored on our servers</li>
                    <li>Used only to communicate with OpenRouter's API directly from your browser</li>
                  </ul>
                  
                  <p><strong>Query History:</strong></p>
                  <ul className="list-disc pl-6 space-y-1 text-sm">
                    <li>Stored locally in your browser's local storage</li>
                    <li>Remains on your device only</li>
                    <li>You can delete it anytime via the Query History page</li>
                    <li>Not synchronized or backed up to any servers</li>
                  </ul>
                </div>
              </section>

              <section>
                <h3 className="text-lg font-semibold text-gray-800 mb-3">Your Rights Under GDPR</h3>
                <div className="space-y-3 text-gray-700">
                  <div className="flex items-start space-x-3">
                    <span className="text-blue-600">📋</span>
                    <div>
                      <p className="font-medium">Right to Access</p>
                      <p className="text-sm">All your data is stored locally on your device and accessible through the application interface.</p>
                    </div>
                  </div>
                  
                  <div className="flex items-start space-x-3">
                    <span className="text-red-600">🗑️</span>
                    <div>
                      <p className="font-medium">Right to Deletion</p>
                      <p className="text-sm">Delete your query history anytime via the Query History page, or clear browser data to remove all stored information.</p>
                    </div>
                  </div>
                  
                  <div className="flex items-start space-x-3">
                    <span className="text-green-600">📁</span>
                    <div>
                      <p className="font-medium">Data Portability</p>
                      <p className="text-sm">Your data is stored in standard formats on your device and can be exported through browser developer tools if needed.</p>
                    </div>
                  </div>
                </div>
              </section>

              <section>
                <h3 className="text-lg font-semibold text-gray-800 mb-3">Third-Party Services</h3>
                <div className="space-y-3 text-gray-700">
                  <p><strong>OpenRouter API:</strong> When you provide your API key, your queries are sent directly to OpenRouter's servers from your browser. Please review <a href="https://openrouter.ai/privacy" target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline">OpenRouter's Privacy Policy</a>.</p>
                  
                  <p><strong>No Analytics:</strong> We don't use Google Analytics, tracking pixels, or similar technologies.</p>
                </div>
              </section>

              <section>
                <h3 className="text-lg font-semibold text-gray-800 mb-3">Data Security</h3>
                <div className="space-y-2 text-gray-700">
                  <p>• All communication uses HTTPS encryption</p>
                  <p>• API keys are stored in secure browser storage</p>
                  <p>• No data transmission to our servers</p>
                  <p>• Open-source code available for security review</p>
                </div>
              </section>

              <section>
                <h3 className="text-lg font-semibold text-gray-800 mb-3">Contact Information</h3>
                <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
                  <p className="text-gray-700">
                    If you have questions about this privacy policy or your data rights, please contact us through our GitHub repository or create an issue.
                  </p>
                  <p className="text-sm text-gray-600 mt-2">
                    Last updated: {new Date().toLocaleDateString()}
                  </p>
                </div>
              </section>
            </div>
            
            <div className="p-6 border-t border-gray-200 bg-gray-50 flex-shrink-0">
              <div className="flex justify-end space-x-3">
                <button
                  onClick={() => setShowPrivacyModal(false)}
                  className="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors"
                >
                  Close
                </button>
                <button
                  onClick={() => {
                    setShowPrivacyModal(false);
                    acceptGDPR();
                  }}
                  className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium"
                >
                  Accept & Continue
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  );
} 