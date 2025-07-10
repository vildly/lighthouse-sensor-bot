import React, { createContext, useContext, useEffect, useState } from 'react';
import { io } from 'socket.io-client';

const WebSocketContext = createContext(null);

export const WebSocketProvider = ({ children }) => {
  const [socket, setSocket] = useState(null);
  const [sqlQueries, setSqlQueries] = useState([]);
  const [queryStatus, setQueryStatus] = useState('idle');
  const [connected, setConnected] = useState(false);
  const [evaluationProgress, setEvaluationProgress] = useState(null);

  useEffect(() => {
    let SERVER_URL;
    if (process.env.DEV_MODE) {
      SERVER_URL = process.env.SERVER_URL;
    } else {
      SERVER_URL = process.env.NEXT_PUBLIC_SERVER_URL || 'http://localhost:5001';
    }
    
    // For WebSocket connection, remove /api suffix if present
    const WEBSOCKET_URL = SERVER_URL.replace(/\/api$/, '');
    
    // Detect mobile device
    const isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
    
    console.log('WebSocket Setup:', {
      isMobile,
      WEBSOCKET_URL,
      userAgent: navigator.userAgent.substring(0, 50) + '...'
    });
    
    // Initialize socket connection
    const socketInstance = io(`${WEBSOCKET_URL}/query`, {
      transports: ['websocket'],
      autoConnect: true,
      reconnection: true,
      reconnectionAttempts: 5,
      reconnectionDelay: 1000,
      timeout: 10000, // 10 second timeout for mobile
      forceNew: true  // Force new connection on mobile
    });

    // Set up event listeners
    socketInstance.on('connect', () => {
      console.log('WebSocket connected');
      setConnected(true);
    });

    socketInstance.on('connect_error', (error) => {
      console.error('WebSocket connection error:', error);
      setConnected(false);
    });

    socketInstance.on('log_message', (data) => {
      console.log('WebSocket log_message received:', data);
      if (data.type === 'sql_query') {
        console.log('Adding SQL query to state:', data.content);
        setSqlQueries(prev => [...prev, data.content]);
      }
    });

    socketInstance.on('query_status', (data) => {
      setQueryStatus(data.status);
    });
    
    // Add listener for evaluation progress
    socketInstance.on('evaluation_progress', (data) => {

      setEvaluationProgress(data);
    });

    socketInstance.on('disconnect', () => {
      console.log('WebSocket disconnected');
      setConnected(false);
    });

    // Save socket instance
    setSocket(socketInstance);

    // Clean up on unmount
    return () => {
      socketInstance.disconnect();
    };
  }, []);

  // Reset queries when starting a new query
  const resetQueries = () => {
    setSqlQueries([]);
    setQueryStatus('idle');
    setEvaluationProgress(null);
  };

  return (
    <WebSocketContext.Provider value={{ 
      socket, 
      sqlQueries, 
      queryStatus, 
      resetQueries,
      connected,
      evaluationProgress
    }}>
      {children}
    </WebSocketContext.Provider>
  );
};

export const useWebSocket = () => useContext(WebSocketContext); 