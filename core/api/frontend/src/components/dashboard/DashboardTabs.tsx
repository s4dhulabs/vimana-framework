// DashboardTabs.tsx
import React from 'react';
import { Bug, Code, GitBranch } from 'lucide-react';

const TabIcon = ({ icon: Icon, isActive }) => (
  <Icon className={`w-4 h-4 ${isActive ? 'text-blue-600' : 'text-gray-500'}`} />
);

export const TabButton = ({ isActive, onClick, children, icon: Icon }) => (
  <button
    onClick={onClick}
    className={`px-4 py-2 font-medium rounded-t-lg flex items-center space-x-2 ${
      isActive 
        ? 'bg-white text-gray-900 border-t border-x border-gray-200' 
        : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
    }`}
  >
    <TabIcon icon={Icon} isActive={isActive} />
    <span>{children}</span>
  </button>
);

export interface DashboardTabsProps {
  activeTab: string;
  onTabChange: (tab: string) => void;
}

export const DashboardTabs: React.FC<DashboardTabsProps> = ({ activeTab, onTabChange }) => {
  const tabs = [
    { id: 'exceptions', label: 'Exceptions', icon: Bug },
    { id: 'code-analysis', label: 'Code Analysis', icon: Code },
    { id: 'data-flows', label: 'Data Flows', icon: GitBranch }
  ];

  return (
    <div className="flex space-x-2">
      {tabs.map(({ id, label, icon }) => (
        <TabButton 
          key={id}
          isActive={activeTab === id} 
          onClick={() => onTabChange(id)}
          icon={icon}
        >
          {label}
        </TabButton>
      ))}
    </div>
  );
};