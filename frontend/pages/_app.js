import '../styles/globals.css'
import { WebSocketProvider } from '../contexts/WebSocketContext';
import Navigation from '../components/navigation';

function MyApp({ Component, pageProps }) {
  return (
    <WebSocketProvider>
      <Navigation />
      <Component {...pageProps} />
    </WebSocketProvider>
  );
}

export default MyApp 