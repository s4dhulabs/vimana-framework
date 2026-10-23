// DashboardStats.tsx
import React from 'react';
import { Activity, AlertCircle, Shield, Bug } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export interface StatsData {
  uniqueEndpoints: number;
  totalExceptions: number;
  securityIssues: number;
  uniqueExceptionTypes: number;
}

interface StatCardProps {
  title: string;
  value: number;
  icon: React.ElementType;
}

const StatCard: React.FC<StatCardProps> = ({ title, value, icon: Icon }) => (
  <Card className="shadow-sm">
    <CardHeader className="flex flex-row items-center justify-between pb-2">
      <CardTitle className="text-sm font-medium">
        {title}
      </CardTitle>
      <Icon className="w-4 h-4 text-gray-500" />
    </CardHeader>
    <CardContent>
      <div className="text-2xl font-bold">{value}</div>
    </CardContent>
  </Card>
);

const statsConfig = [
  {
    id: 'uniqueEndpoints',
    title: "Unique Endpoints",
    icon: Activity,
    description: "Total number of unique endpoints discovered"
  },
  {
    id: 'totalExceptions',
    title: "Total Exceptions",
    icon: AlertCircle,
    description: "Total number of exceptions captured"
  },
  {
    id: 'securityIssues',
    title: "Security Issues",
    icon: Shield,
    description: "Total number of security-related issues found"
  },
  {
    id: 'uniqueExceptionTypes',
    title: "Unique Exception Types",
    icon: Bug,
    description: "Number of different exception types encountered"
  }
] as const;

export interface DashboardStatsProps {
  data: StatsData;
  className?: string;
}

export const DashboardStats: React.FC<DashboardStatsProps> = ({ 
  data,
  className = ""
}) => {
  return (
    <div className={`grid grid-cols-1 md:grid-cols-4 gap-4 ${className}`}>
      {statsConfig.map(({ id, title, icon, description }) => (
        <div key={id} className="relative group">
          <StatCard
            title={title}
            value={data[id as keyof StatsData]}
            icon={icon}
          />
          {/* Tooltip */}
          <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 w-48 
                        bg-gray-800 text-white text-xs rounded py-1 px-2 opacity-0 
                        group-hover:opacity-100 transition-opacity duration-200 pointer-events-none">
            {description}
          </div>
        </div>
      ))}
    </div>
  );
};

// Helper functions to calculate stats from raw data
export const calculateStats = (fuzzingData: any[]): StatsData => {
  return {
    uniqueEndpoints: new Set(fuzzingData.map(d => d.endpoint)).size,
    totalExceptions: fuzzingData.length,
    securityIssues: fuzzingData.reduce((acc, d) => acc + (d.security_issues?.length || 0), 0),
    uniqueExceptionTypes: new Set(fuzzingData.map(d => d.exception_type)).size
  };
};

// StatsContext for potential global access to stats
export const StatsContext = React.createContext<{
  stats: StatsData;
  updateStats: (data: any[]) => void;
}>({
  stats: {
    uniqueEndpoints: 0,
    totalExceptions: 0,
    securityIssues: 0,
    uniqueExceptionTypes: 0
  },
  updateStats: () => {}
});

// Optional StatsProvider component for global stats management
export const StatsProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [stats, setStats] = React.useState<StatsData>({
    uniqueEndpoints: 0,
    totalExceptions: 0,
    securityIssues: 0,
    uniqueExceptionTypes: 0
  });

  const updateStats = React.useCallback((data: any[]) => {
    setStats(calculateStats(data));
  }, []);

  return (
    <StatsContext.Provider value={{ stats, updateStats }}>
      {children}
    </StatsContext.Provider>
  );
};

// Custom hook for accessing stats
export const useStats = () => {
  const context = React.useContext(StatsContext);
  if (!context) {
    throw new Error('useStats must be used within a StatsProvider');
  }
  return context;
};

export default DashboardStats;