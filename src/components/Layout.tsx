import React, { useState } from 'react';
import { Outlet } from 'react-router-dom';
import { useNavigate } from 'react-router-dom';
import Sidebar from './Sidebar';
import TopBar from './TopBar';
import { Code } from 'lucide-react';

const DEV_MODE = import.meta.env.VITE_DEV_MODE === 'true';

const Layout: React.FC = () => {
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);
  const navigate = useNavigate();

  const toggleSidebar = () => {
    setIsSidebarCollapsed(!isSidebarCollapsed);
  };

  const handleDevModeClick = () => {
    navigate('/dashboard');
  };

  return (
    <div className="min-h-screen bg-gray-900 flex">
      <Sidebar isCollapsed={isSidebarCollapsed} toggleSidebar={toggleSidebar} />
      <div className="flex-1 flex flex-col">
        <TopBar />
        <main className="flex-1 p-6">
          <Outlet />
        </main>
        {DEV_MODE && (
          <button
            onClick={handleDevModeClick}
            className="fixed bottom-4 right-4 flex items-center space-x-1.5 px-2.5 py-1.5 bg-yellow-600 hover:bg-yellow-700 text-white rounded-lg shadow-lg transition-colors font-mono text-xs"
            title="Development Mode Active"
          >
            <Code size={14} />
            <span>Dev Mode</span>
          </button>
        )}
      </div>
    </div>
  );
};

export default Layout;