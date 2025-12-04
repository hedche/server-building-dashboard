import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import App from './App.tsx';
import './index.css';

// Development mode logging
const DEV_MODE = import.meta.env.VITE_DEV_MODE === 'true';
const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000';
const APP_NAME = import.meta.env.VITE_APP_NAME || 'SAML Portal';
const LOGIN_LOGO_PATH = import.meta.env.VITE_LOGIN_LOGO_PATH || 'logo.png';

if (DEV_MODE) {
  console.log('%c🚀 Development Mode Active', 'color: #10b981; font-size: 16px; font-weight: bold;');
  console.log('%c━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━', 'color: #6b7280;');
  console.log('%c📋 Environment Configuration:', 'color: #3b82f6; font-weight: bold;');
  console.log('  VITE_DEV_MODE:', DEV_MODE);
  console.log('  VITE_BACKEND_URL:', BACKEND_URL);
  console.log('  VITE_APP_NAME:', APP_NAME);
  console.log('  VITE_LOGIN_LOGO_PATH:', LOGIN_LOGO_PATH);
  console.log('%c━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━', 'color: #6b7280;');
  console.log('%c💡 Dev Mode Features:', 'color: #f59e0b; font-weight: bold;');
  console.log('  ✓ Backend connection attempted first');
  console.log('  ✓ Auto-fallback to mock data if backend unreachable');
  console.log('  ✓ Auto-login as dev@example.com (mock fallback)');
  console.log('  ✓ SAML authentication bypassed in fallback mode');
  console.log('  ✓ 3-second timeout for backend requests');
  console.log('%c━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━', 'color: #6b7280;');
  console.log('%c🔌 Backend Connection:', 'color: #8b5cf6; font-weight: bold;');
  console.log('  Attempting to connect to:', BACKEND_URL);
  console.log('  Watch for connection status messages below...');
  console.log('%c━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━', 'color: #6b7280;');
  console.log('%c🔧 Useful Tips:', 'color: #6366f1; font-weight: bold;');
  console.log('  • Backend URL is set at build/compile time');
  console.log('  • Set VITE_DEV_MODE=false to disable fallback');
  console.log('  • Check .env file to modify configuration');
  console.log('  • Green ✓ = Backend connected | Yellow ⚠ = Using mock data');
  console.log('%c━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━', 'color: #6b7280;');
}

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>
);
