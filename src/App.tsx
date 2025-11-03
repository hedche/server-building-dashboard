import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';
import Layout from './components/Layout';
import ProtectedRoute from './components/ProtectedRoute';
import LoginPage from './pages/LoginPage';
import AuthCallbackPage from './pages/AuthCallbackPage';
import BuildOverviewPage from './pages/BuildOverviewPage';
import PreconfigPage from './pages/PreconfigPage';
import AssignPage from './pages/AssignPage';
import BuildLogsPage from './pages/BuildLogsPage';
import CredentialsPage from './pages/CredentialsPage';

function App() {
  return (
    <AuthProvider>
      <Router>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/auth/callback" element={<AuthCallbackPage />} />
          
          <Route path="/" element={
            <ProtectedRoute>
              <Layout />
            </ProtectedRoute>
          }>
            <Route index element={<Navigate to="/dashboard" replace />} />
            <Route path="dashboard" element={<BuildOverviewPage />} />
            <Route path="preconfig" element={<PreconfigPage />} />
            <Route path="assign" element={<AssignPage />} />
            <Route path="build-logs" element={<BuildLogsPage />} />
            <Route path="credentials" element={<CredentialsPage />} />
          </Route>
          
          {/* Catch all route */}
          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </Router>
    </AuthProvider>
  );
}

export default App;