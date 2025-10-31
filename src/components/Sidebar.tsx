import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { 
  Menu, 
  X, 
  BarChart3, 
  Settings, 
  UserCheck,
  FileText
} from 'lucide-react';

interface SidebarProps {
  isCollapsed: boolean;
  toggleSidebar: () => void;
}

const navigationItems = [
  {
    name: 'Build Overview',
    path: '/dashboard',
    icon: BarChart3,
  },
  {
    name: 'Preconfig',
    path: '/preconfig',
    icon: Settings,
  },
  {
    name: 'Assign',
    path: '/assign',
    icon: UserCheck,
  },
  {
    name: 'Build Logs',
    path: '/build-logs',
    icon: FileText,
  },
];

const Sidebar: React.FC<SidebarProps> = ({ isCollapsed, toggleSidebar }) => {
  const location = useLocation();

  return (
    <div className={`bg-gray-800 border-r border-gray-700 transition-all duration-300 ${
      isCollapsed ? 'w-16' : 'w-64'
    }`}>
      <div className="flex items-center justify-between p-4 border-b border-gray-700">
        {!isCollapsed && (
          <h1 className="text-lg font-bold text-green-400 font-mono">{import.meta.env.VITE_APP_NAME || 'Server Dashboard'}</h1>
        )}
        <button
          onClick={toggleSidebar}
          className="p-1.5 rounded-lg hover:bg-gray-700 transition-colors text-gray-300"
        >
          {isCollapsed ? <Menu size={16} /> : <X size={16} />}
        </button>
      </div>
      
      <nav className="mt-6">
        <ul className="space-y-1 px-2">
          {navigationItems.map((item) => {
            const Icon = item.icon;
            const isActive = location.pathname === item.path;
            
            return (
              <li key={item.path}>
                <Link
                  to={item.path}
                  className={`flex items-center p-2.5 rounded-lg transition-colors text-sm ${
                    isActive
                      ? 'bg-green-600 text-white'
                      : 'text-gray-300 hover:bg-gray-700 hover:text-white'
                  }`}
                  title={isCollapsed ? item.name : undefined}
                >
                  <Icon size={16} className="flex-shrink-0" />
                  {!isCollapsed && (
                    <span className="ml-2.5 font-medium">{item.name}</span>
                  )}
                </Link>
              </li>
            );
          })}
        </ul>
      </nav>
    </div>
  );
};

export default Sidebar;