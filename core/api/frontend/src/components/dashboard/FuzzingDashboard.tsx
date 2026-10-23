import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { 
  Activity, 
  AlertCircle, 
  Terminal, 
  Bug,
  Code,
  GitBranch,
  Settings,
  Shield,
  X
} from 'lucide-react';
import ExceptionFilters from './ExceptionFilters';
import SelectionControls from './SelectionControls';
import CodeAnalysisTab from './CodeAnalysisTab';
import DataFlowsTab from './DataFlowsTab';
import EndpointItem from './EndpointItem';
import FuzzingDashboardHeader from './FuzzingDashboardHeader';

/** Exception Monitor API base (no trailing slash). */
function resolveMonitorHttp(): string {
  if (typeof window !== 'undefined') {
    const q = new URLSearchParams(window.location.search).get('monitor');
    if (q) return q.replace(/\/$/, '');
  }
  const env = process.env.NEXT_PUBLIC_MONITOR_URL;
  if (env && env.trim()) return env.replace(/\/$/, '');
  return 'http://127.0.0.1:8000';
}

function resolveInitialScanId(): string {
  if (typeof window === 'undefined') return '';
  return new URLSearchParams(window.location.search).get('scan') || '';
}

function resolveMonitorWs(httpBase: string): string {
  const env = process.env.NEXT_PUBLIC_MONITOR_WS;
  if (env && env.trim()) return env.replace(/\/$/, '');
  if (httpBase.startsWith('https://')) return 'wss://' + httpBase.slice('https://'.length);
  if (httpBase.startsWith('http://')) return 'ws://' + httpBase.slice('http://'.length);
  return httpBase;
}

function syncScanQuery(scanId: string) {
  if (typeof window === 'undefined') return;
  const url = new URL(window.location.href);
  if (scanId) url.searchParams.set('scan', scanId);
  else url.searchParams.delete('scan');
  window.history.replaceState({}, '', url.toString());
}

const LiveUpdatesIndicator = () => (
  <div className="fixed bottom-4 right-4 bg-green-500 text-white px-4 py-2 rounded-full 
                  flex items-center gap-2 shadow-lg">
    <div className="w-2 h-2 bg-white rounded-full animate-pulse" />
    <span>Live Updates</span>
  </div>
);

const FuzzingDashboard = () => {
  // State Management
  const [isFiltersOpen, setIsFiltersOpen] = useState(true);
  const [expandedExceptions, setExpandedExceptions] = useState(new Set());
  const [activeTab, setActiveTab] = useState('exceptions');
  const [fuzzingData, setFuzzingData] = useState([]);
  const [selectedExceptions, setSelectedExceptions] = useState(new Set());
  const [isAnalyzed, setIsAnalyzed] = useState(false);
  const [processedCodeFragments, setProcessedCodeFragments] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [isAutoAnalyzeEnabled, setIsAutoAnalyzeEnabled] = useState(false);
  const [isAllExpanded, setIsAllExpanded] = useState(false);
  const [scans, setScans] = useState([]);
  const [selectedScanId, setSelectedScanId] = useState(() => resolveInitialScanId());
  const [monitorHttp, setMonitorHttp] = useState(() => resolveMonitorHttp());
  const [apiOnline, setApiOnline] = useState(null);
  
  const [filters, setFilters] = useState({
    exceptionTypes: [],
    endpoints: [],
    apps: [],
    methods: [],
    securityIssues: []
  });
  
  const [stats, setStats] = useState({
    uniqueEndpoints: 0,
    totalExceptions: 0,
    securityIssues: 0,
    uniqueExceptionTypes: new Set()
  });

  const applyExceptionBatch = (exceptions, autoAnalyze) => {
    setFuzzingData(exceptions);
    updateStats(exceptions);
    processCodeFragments(exceptions);
    if (autoAnalyze) {
      setSelectedExceptions(new Set(exceptions.map(e => e.id)));
      setIsAnalyzed(true);
      setActiveTab('code-analysis');
    }
  };

  const handleScanChange = (scanId) => {
    setSelectedScanId(scanId);
    syncScanQuery(scanId);
    setSelectedExceptions(new Set());
  };

  // Stats reflect the selected scan (before type/app filters)
  useEffect(() => {
    const scoped = selectedScanId
      ? fuzzingData.filter((e) => (e.scan_id || '') === selectedScanId)
      : fuzzingData;
    updateStats(scoped);
  }, [selectedScanId, fuzzingData]);

  // Helper Functions
  const updateStats = (data) => {
    const uniqueEndpoints = new Set(data.map(d => {
      try {
        const url = new URL(d.endpoint || '');
        return url.pathname;
      } catch {
        return d.endpoint;
      }
    }));

    const securityIssuesCount = data.reduce((acc, d) => {
      return acc + (d.security_issues?.length || 0);
    }, 0);

    setStats({
      uniqueEndpoints: uniqueEndpoints.size,
      totalExceptions: data.reduce((acc, d) => acc + (d.issues?.length || 1), 0),
      securityIssues: securityIssuesCount,
      uniqueExceptionTypes: new Set(data.map(d => d.exception_type))
    });
  };

  const processCodeFragments = (exceptions) => {
    const fragments = [];
    exceptions.forEach(exc => {
      try {
        const rawOutput = JSON.parse(exc.raw_output || '{}');
        const viewTrigger = rawOutput.view_trigger;
        
        if (!viewTrigger) return;

        const relevantTrace = exc.stack_trace?.find(trace => 
          trace.file === viewTrigger.fullpath &&
          trace.code_snippet
        );

        if (!relevantTrace || !relevantTrace.code_snippet) return;

        fragments.push({
          id: `${viewTrigger.shortpath}.${viewTrigger.object}`,
          location: {
            fullpath: viewTrigger.fullpath,
            shortpath: viewTrigger.shortpath,
            object: viewTrigger.object,
            line_number: relevantTrace.line
          },
          code: relevantTrace.code_snippet,
          startLine: parseInt(relevantTrace.code_snippet[0].match(/^\s*(\d+)/)?.[1] || '0'),
          endLine: parseInt(relevantTrace.code_snippet[relevantTrace.code_snippet.length - 1].match(/^\s*(\d+)/)?.[1] || '0')
        });
      } catch (error) {
        console.error('Error processing code fragment:', error);
      }
    });

    setProcessedCodeFragments(fragments);
  };

  const handleDeleteSelected = () => {
    if (selectedExceptions.size === 0) return;
    
    const newData = fuzzingData.filter(exception => !selectedExceptions.has(exception.id));
    setFuzzingData(newData);
    setSelectedExceptions(new Set());
    updateStats(newData);
  };
  
  const handleExceptionSelect = (exceptionId) => {
    setSelectedExceptions(prev => {
      const newSet = new Set(prev);
      if (newSet.has(exceptionId)) {
        newSet.delete(exceptionId);
      } else {
        newSet.add(exceptionId);
      }
      return newSet;
    });
  };

  const handleToggleExceptionExpand = (exceptionId) => {
    setExpandedExceptions(prev => {
      const newSet = new Set(prev);
      if (newSet.has(exceptionId)) {
        newSet.delete(exceptionId);
      } else {
        newSet.add(exceptionId);
      }
      return newSet;
    });
  };
  
  const handleAnalyzeCode = () => {
    setIsAnalyzed(true);
    setActiveTab('code-analysis');
  };

  const handleRemoveException = (exceptionId) => {
    setFuzzingData(prev => prev.filter(e => e.id !== exceptionId));
    setSelectedExceptions(prev => {
      const newSet = new Set(prev);
      newSet.delete(exceptionId);
      return newSet;
    });
  };
  // WebSocket and Data Fetching Effect
  useEffect(() => {
    const httpBase = resolveMonitorHttp();
    const wsBase = resolveMonitorWs(httpBase);
    setMonitorHttp(httpBase);

    const fetchScans = async () => {
      try {
        const response = await fetch(`${httpBase}/scans`);
        const data = await response.json();
        if (data.scans) setScans(data.scans);
      } catch (error) {
        console.error('Error fetching scans:', error);
      }
    };

    const fetchData = async () => {
      try {
        const response = await fetch(`${httpBase}/exceptions?limit=5000`);
        const data = await response.json();
        setApiOnline(true);
        if (data.exceptions) {
          applyExceptionBatch(data.exceptions, isAutoAnalyzeEnabled);
        }
        await fetchScans();
      } catch (error) {
        setApiOnline(false);
        console.error('Error fetching initial data:', error);
      }
    };

    fetchData();

    const ws = new WebSocket(`${wsBase}/ws`);

    ws.onopen = () => {
      console.log('Connected to dashboard backend', httpBase);
      setApiOnline(true);
    };

    ws.onmessage = (event) => {
      const message = JSON.parse(event.data);
      
      if (message.type === 'initial_data') {
        applyExceptionBatch(message.data || [], isAutoAnalyzeEnabled);
        fetchScans();
      } else if (message.type === 'new_exception') {
        setFuzzingData(prevData => {
          const newData = [...prevData, message.data];
          updateStats(newData);
          processCodeFragments(newData);
          if (isAutoAnalyzeEnabled) {
            setSelectedExceptions(new Set(newData.map(e => e.id)));
            setIsAnalyzed(true);
            setActiveTab('code-analysis');
          }
          return newData;
        });
        fetchScans();
      }
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    return () => {
      ws.close();
    };
  }, [isAutoAnalyzeEnabled]);

  // Filter exceptions based on scan, search and filters
  const getFilteredExceptions = () => {
    return fuzzingData.filter(exception => {
      const matchesScan = !selectedScanId ||
        (exception.scan_id || '') === selectedScanId;

      // Search term filter
      const searchString = JSON.stringify(exception).toLowerCase();
      const matchesSearch = searchTerm === '' || searchString.includes(searchTerm.toLowerCase());

      // Exception type filter
      const matchesExceptionType = filters.exceptionTypes.length === 0 || 
        filters.exceptionTypes.includes(exception.exception_type);

      // Endpoint filter
      let endpointPath = '';
      try {
        const url = new URL(exception.endpoint || '');
        endpointPath = url.pathname;
      } catch {
        endpointPath = exception.endpoint || '';
      }
      const matchesEndpoint = filters.endpoints.length === 0 || 
        filters.endpoints.includes(endpointPath);

      // App filter
      let appName = '';
      try {
        const viewTrigger = JSON.parse(exception.raw_output || '{}').view_trigger;
        appName = viewTrigger?.app_name || '';
      } catch {
        // Ignore parsing errors
      }
      const matchesApp = filters.apps.length === 0 || 
        filters.apps.includes(appName);

      // Method filter
      const matchesMethod = filters.methods.length === 0 || 
        filters.methods.includes(exception.method);

      // Security issues filter
      const hasMatchingSecurityIssue = filters.securityIssues.length === 0 || 
        exception.security_issues?.some(issue => 
          filters.securityIssues.includes(issue.issue_type)
        );

      return matchesScan &&
             matchesSearch && 
             matchesExceptionType && 
             matchesEndpoint && 
             matchesApp && 
             matchesMethod && 
             hasMatchingSecurityIssue;
    });
  };

  const renderScanBar = () => {
    const visibleCount = getFilteredExceptions().length;
    return (
      <div className="bg-white border border-gray-200 rounded-lg shadow-sm px-4 py-3 flex flex-wrap items-center gap-3">
        <label className="text-sm font-medium text-gray-700" htmlFor="scan-select">
          Scan
        </label>
        <select
          id="scan-select"
          value={selectedScanId}
          onChange={(e) => handleScanChange(e.target.value)}
          className="text-sm border border-gray-300 rounded-md px-2 py-1.5 min-w-[16rem] max-w-full bg-white"
        >
          <option value="">All scans ({fuzzingData.length})</option>
          {scans.map((s) => (
            <option key={s.scan_id} value={s.scan_id}>
              {s.scan_id} · {s.count || 0} exc
              {(s.plugins || []).length ? ` · ${(s.plugins || []).join(',')}` : ''}
            </option>
          ))}
        </select>
        {selectedScanId && (
          <button
            type="button"
            onClick={() => handleScanChange('')}
            className="text-xs text-gray-600 hover:text-gray-900 underline"
          >
            Clear
          </button>
        )}
        <span className="text-xs text-gray-500 ml-auto">
          showing {visibleCount}
          {apiOnline === false && (
            <span className="text-red-600 ml-2">API offline</span>
          )}
          {apiOnline !== false && (
            <span className="text-gray-400 ml-2" title="Exception Monitor API">
              {monitorHttp}
            </span>
          )}
        </span>
      </div>
    );
  };
  // Render Functions
  const renderStatsCards = () => (
    <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
      <Card className="shadow-sm">
        <CardHeader className="flex flex-row items-center justify-between pb-2">
          <CardTitle className="text-sm font-medium">
            Unique Endpoints
          </CardTitle>
          <Activity className="w-4 h-4 text-gray-500" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{stats.uniqueEndpoints}</div>
        </CardContent>
      </Card>
      
      <Card className="shadow-sm">
        <CardHeader className="flex flex-row items-center justify-between pb-2">
          <CardTitle className="text-sm font-medium">
            Total Exceptions
          </CardTitle>
          <AlertCircle className="w-4 h-4 text-gray-500" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{stats.totalExceptions}</div>
        </CardContent>
      </Card>

      <Card className="shadow-sm">
        <CardHeader className="flex flex-row items-center justify-between pb-2">
          <CardTitle className="text-sm font-medium">
            Security Issues
          </CardTitle>
          <Shield className="w-4 h-4 text-gray-500" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{stats.securityIssues}</div>
        </CardContent>
      </Card>

      <Card className="shadow-sm">
        <CardHeader className="flex flex-row items-center justify-between pb-2">
          <CardTitle className="text-sm font-medium">
            Unique Exceptions
          </CardTitle>
          <Terminal className="w-4 h-4 text-gray-500" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{stats.uniqueExceptionTypes.size}</div>
        </CardContent>
      </Card>
    </div>
  );

  const renderExceptionsTab = () => {
    const filteredExceptions = getFilteredExceptions();
    
    return (
      <div className="space-y-4">
        {renderScanBar()}
        {isFiltersOpen && (
          <ExceptionFilters
            fuzzingData={selectedScanId
              ? fuzzingData.filter(e => (e.scan_id || '') === selectedScanId)
              : fuzzingData}
            onFiltersChange={setFilters}
            onSearchChange={setSearchTerm}
          />
        )}
        
        <SelectionControls
          onSelectAll={() => setSelectedExceptions(new Set(filteredExceptions.map(e => e.id)))}
          onDeselectAll={() => setSelectedExceptions(new Set())}
          onExpandAll={() => {
            const allIds = new Set(filteredExceptions.map(e => e.id));
            setExpandedExceptions(allIds);
            setIsAllExpanded(true);
          }}
          onCollapseAll={() => {
            setExpandedExceptions(new Set());
            setIsAllExpanded(false);
          }}
          onToggleAutoAnalyze={() => setIsAutoAnalyzeEnabled(!isAutoAnalyzeEnabled)}
          onToggleFilters={() => setIsFiltersOpen(!isFiltersOpen)}
          onDeleteSelected={handleDeleteSelected}
          selectedCount={selectedExceptions.size}
          totalCount={filteredExceptions.length}
          isExpanded={isAllExpanded}
          isAutoAnalyzeEnabled={isAutoAnalyzeEnabled}
          isFiltersOpen={isFiltersOpen}
          onAnalyze={handleAnalyzeCode}
        />
  
        {filteredExceptions.map((exception) => (
          <div key={exception.id} className="flex items-start space-x-2">
            <input
              type="checkbox"
              checked={selectedExceptions.has(exception.id)}
              onChange={() => handleExceptionSelect(exception.id)}
              className="mt-4"
            />
            <div className="flex-1">
              <EndpointItem
                endpoint={exception}
                isSelected={selectedExceptions.has(exception.id)}
                onSelect={() => handleExceptionSelect(exception.id)}
                onRemove={handleRemoveException}
                isExpanded={isAllExpanded || expandedExceptions.has(exception.id)}
                onToggleExpand={handleToggleExceptionExpand}
              />
            </div>
          </div>
        ))}
      </div>
    );
  };
  
  const TabIcon = ({ icon: Icon, isActive }) => (
    <Icon className={`w-4 h-4 ${isActive ? 'text-blue-600' : 'text-gray-500'}`} />
  );

  const TabButton = ({ isActive, onClick, children, icon: Icon }) => (
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
  // Main render
  return (
    <div className="p-4 space-y-4 bg-gray-50 min-h-screen -mt-7">
      <FuzzingDashboardHeader />
      {renderStatsCards()}
      <LiveUpdatesIndicator />
      
      <Card className="shadow-sm">
        <CardHeader className="flex flex-row items-center justify-between">
          <div className="flex space-x-2">
            <TabButton 
              isActive={activeTab === 'exceptions'} 
              onClick={() => setActiveTab('exceptions')}
              icon={Bug}
            >
              Exceptions
            </TabButton>
            <TabButton 
              isActive={activeTab === 'code-analysis'} 
              onClick={() => setActiveTab('code-analysis')}
              icon={Code}
              dataTab="code-analysis"
            >
              Code Analysis
            </TabButton>
            <TabButton 
              isActive={activeTab === 'data-flows'} 
              onClick={() => setActiveTab('data-flows')}
              icon={GitBranch}
            >
              Data Flows
            </TabButton>
          </div>
        </CardHeader>
        <CardContent>
          {activeTab === 'exceptions' && renderExceptionsTab()}
          {activeTab === 'code-analysis' && (
            <CodeAnalysisTab
              selectedExceptions={selectedExceptions}
              fuzzingData={fuzzingData}
              isAnalyzed={isAnalyzed}
            />
          )}
          {activeTab === 'data-flows' && (
            <DataFlowsTab
              fuzzingData={fuzzingData}
              codeFragments={processedCodeFragments}
            />
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default FuzzingDashboard;