import React, { useState } from 'react';
import { 
  ChevronDown, 
  ChevronRight,
  ShieldAlert,
  Terminal,
  Code,
  ArrowRight,
  X
} from 'lucide-react';

interface SecurityIssue {
  issue_type?: string;
  confidence?: number;
  description?: string;
  evidence?: string;
  recommendation?: string;
}

interface Endpoint {
  id: string;
  endpoint?: string;
  method?: string;
  exception_type?: string;
  severity?: string;
  description?: string;
  timestamp?: string;
  security_issues?: SecurityIssue[];
  stack_trace?: any[];
  request_data?: any;
  variables?: any;
  raw_output?: string;
  issues?: any[];
}

interface EndpointItemProps {
  endpoint: Endpoint;
  isSelected: boolean;
  onSelect: (endpoint: Endpoint) => void;
  onRemove?: (id: string) => void;
  isExpanded?: boolean;
  onToggleExpand?: (id: string) => void;
}

const CodeBlock = ({ content }: { content: string }) => (
  <pre className="bg-black text-gray-100 p-4 rounded-lg overflow-x-auto font-mono text-sm">
    <code>
      {content}
    </code>
  </pre>
);

const CollapsibleSection = ({ 
  title, 
  icon: Icon = Terminal, 
  children 
}: {
  title: string;
  icon?: React.ElementType;
  children: React.ReactNode;
}) => {
  const [isExpanded, setIsExpanded] = useState(false);
  
  return (
    <div className="bg-gray-900 rounded-lg overflow-hidden">
      <button 
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full px-4 py-3 flex items-center justify-between text-white hover:bg-gray-800 transition-colors"
      >
        <div className="flex items-center space-x-2">
          <Icon className="w-4 h-4" />
          <span className="font-mono text-sm">{title}</span>
        </div>
        {isExpanded ? (
          <ChevronDown className="w-4 h-4" />
        ) : (
          <ChevronRight className="w-4 h-4" />
        )}
      </button>
      {isExpanded && (
        <div className="px-4 pb-4">
          {children}
        </div>
      )}
    </div>
  );
};
const CollapsibleIssue = ({ issue, index }: { issue: SecurityIssue; index: number }) => {
  const [isExpanded, setIsExpanded] = useState(false);
  
  const getValue = (value: any): string => {
    if (typeof value === 'object' && value !== null) {
      return JSON.stringify(value);
    }
    return String(value);
  };

  return (
    <div className="border-l-2 border-gray-700">
      <button 
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full px-4 py-2 flex items-center justify-between text-white hover:bg-gray-800 transition-colors"
      >
        <div className="flex items-center space-x-2">
          <span className="text-sm font-mono">
            {index + 1}. {getValue(issue.issue_type)}
          </span>
        </div>
        {isExpanded ? (
          <ChevronDown className="w-4 h-4" />
        ) : (
          <ChevronRight className="w-4 h-4" />
        )}
      </button>
      {isExpanded && (
        <div className="px-4 py-2 space-y-2">
          {issue.confidence !== undefined && (
            <div className="flex items-center justify-between">
              <span className="text-sm bg-blue-500 px-2 py-0.5 rounded">
                Confidence: {Math.round(Number(issue.confidence) * 100)}%
              </span>
            </div>
          )}
          {issue.description && (
            <p className="text-sm text-gray-300">{getValue(issue.description)}</p>
          )}
          {issue.evidence && (
            <div className="text-sm bg-gray-800 p-2 rounded">
              <div className="font-medium mb-1">Evidence:</div>
              <code className="text-gray-300">{getValue(issue.evidence)}</code>
            </div>
          )}
          {issue.recommendation && (
            <div className="mt-2">
              <div className="font-medium text-sm">Recommendation:</div>
              <p className="text-sm text-gray-300">{getValue(issue.recommendation)}</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

const CollapsibleStackTrace = ({ 
  trace, 
  index, 
  isViewTrigger 
}: { 
  trace: any; 
  index: number; 
  isViewTrigger: boolean;
}) => {
  const [isExpanded, setIsExpanded] = useState(isViewTrigger);
  
  return (
    <div className="border-l-2 border-gray-700">
      <button 
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full px-4 py-2 flex items-center justify-between text-white hover:bg-gray-800 transition-colors"
      >
        <div className="flex items-center space-x-2 font-mono text-sm">
          <span>{index + 1}. File: {trace.file}</span>
        </div>
        {isExpanded ? (
          <ChevronDown className="w-4 h-4" />
        ) : (
          <ChevronRight className="w-4 h-4" />
        )}
      </button>
      {isExpanded && (
        <div className="px-4 py-2">
          <div className="space-y-2 text-sm">
            <div><span className="text-gray-400">Function:</span> {trace.function}</div>
            <div><span className="text-gray-400">Line:</span> {trace.line}</div>
            {trace.code_snippet && (
              <div className="mt-2">
                <CodeBlock content={trace.code_snippet.join('\n')} />
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
const EndpointItem: React.FC<EndpointItemProps> = ({ 
  endpoint, 
  isSelected, 
  onSelect,
  onRemove,
  isExpanded = false,
  onToggleExpand
}) => {
  // Format exception description to limit length
  const formatDescription = (desc: string) => {
    if (!desc) return '';
    return desc.length > 80 ? `${desc.substring(0, 80)}...` : desc;
  };
  
  const severity = endpoint.severity?.toLowerCase() || 'low';
  const severityColors = {
    critical: 'bg-red-500',
    high: 'bg-orange-500',
    medium: 'bg-yellow-500',
    low: 'bg-blue-500'
  };

  const formatPath = (endpoint: Endpoint) => {
    try {
      const url = endpoint.endpoint || '';
      const path = new URL(url).pathname;
      return { path, method: endpoint.method };
    } catch {
      return { 
        path: endpoint.endpoint || '', 
        method: endpoint.method || '' 
      };
    }
  };

  const { path, method } = formatPath(endpoint);

  // Handle card click - both select and toggle expansion
  const handleCardClick = () => {
    onSelect(endpoint);
    if (onToggleExpand) {
      onToggleExpand(endpoint.id);
    }
  };

  const handleRemove = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (onRemove) {
      onRemove(endpoint.id);
    }
  };

  return (
    <div className="mb-4 relative group">
      <div 
        className={`flex items-center p-4 rounded-lg border border-gray-200 cursor-pointer transition-all
          ${isSelected ? 'bg-gray-50 border-blue-500 shadow-sm' : 'bg-white hover:bg-gray-50 hover:border-gray-300'}`}
        onClick={handleCardClick}
      >
        <div className={`w-2 h-2 rounded-full mr-3 ${severityColors[severity as keyof typeof severityColors]}`} />
        <div className="flex-1">
          <div className="flex flex-col">
            <div className="flex items-center space-x-2">
              <div className="flex flex-wrap gap-2 items-center">
                <span className="font-semibold text-gray-600 bg-gray-100 px-2 py-0.5 rounded">
                  {endpoint.id}
                </span>
                <ArrowRight className="w-4 h-4 text-gray-400 flex-shrink-0" />
                <span className="font-mono">
                  <span className="font-semibold text-gray-800">{endpoint.exception_type}</span>
                  <span className="text-gray-600">: {formatDescription(endpoint.description)}</span>
                </span>
              </div>
            </div>
            <div className="flex items-center mt-2">
              <span className="text-base font-mono truncate max-w-lg">
                {path}
              </span>
              <span className="px-2 py-0.5 rounded font-mono font-bold bg-blue-100 text-blue-800 ml-2 flex-shrink-0">
                {method}
              </span>
            </div>
            <div className="flex items-center mt-1.5">
              <span className="text-xs bg-gray-100 px-2 py-0.5 rounded-full text-gray-600 font-medium">
                {endpoint.issues?.length || 1} issues
              </span>
              <span className="text-xs text-gray-500 ml-2">
                {endpoint.timestamp && new Date(endpoint.timestamp).toLocaleString()}
              </span>
            </div>
          </div>
        </div>
        <div 
          onClick={(e) => {
            e.stopPropagation();
            if (onToggleExpand) {
              onToggleExpand(endpoint.id);
            }
          }} 
          className="focus:outline-none cursor-pointer"
        >
          {isExpanded ? (
            <ChevronDown className="w-5 h-5 text-gray-400" />
          ) : (
            <ChevronRight className="w-5 h-5 text-gray-400" />
          )}
        </div>
      </div>

      {/* Remove button */}
      {onRemove && (
        <button
          onClick={handleRemove}
          className="absolute top-2 right-2 p-1 rounded-full bg-gray-100 opacity-0 
            group-hover:opacity-100 transition-opacity hover:bg-gray-200 z-10"
        >
          <X className="h-4 w-4 text-gray-500" />
        </button>
      )}

      {isExpanded && (
        <div className="mt-3 ml-6 pl-4 border-l-2 border-gray-200 space-y-3">
          {endpoint.security_issues && endpoint.security_issues.length > 0 && (
            <CollapsibleSection title="Security Issues" icon={ShieldAlert}>
              <div className="space-y-4">
                {endpoint.security_issues.map((issue, index) => (
                  <CollapsibleIssue 
                    key={index}
                    index={index}
                    issue={issue}
                  />
                ))}
              </div>
            </CollapsibleSection>
          )}

          <CollapsibleSection title="Exception Details">
            <CodeBlock
              content={`${endpoint.exception_type}
    Reason: ${endpoint.description}
    Category: ${endpoint.severity}
    Request Method: ${endpoint.method}`}
            />
          </CollapsibleSection>

          {endpoint.request_data && (
            <CollapsibleSection title="Test Payload">
              <CodeBlock
                content={JSON.stringify(endpoint.request_data, null, 2)}
              />
            </CollapsibleSection>
          )}

          {endpoint.stack_trace && (
            <CollapsibleSection title="Stack Trace">
              <div className="space-y-1">
                {endpoint.stack_trace.map((trace, index) => {
                  const viewTrigger = endpoint.raw_output ? 
                    JSON.parse(endpoint.raw_output).view_trigger : null;
                  const isViewTrigger = viewTrigger && 
                    trace.file === viewTrigger.fullpath;
                  
                  return (
                    <CollapsibleStackTrace
                      key={index}
                      index={index}
                      trace={trace}
                      isViewTrigger={isViewTrigger}
                    />
                  );
                })}
              </div>
            </CollapsibleSection>
          )}

          {endpoint.variables && Object.keys(endpoint.variables).length > 0 && (
            <CollapsibleSection title="Variables">
              <CodeBlock
                content={JSON.stringify(endpoint.variables, null, 2)}
              />
            </CollapsibleSection>
          )}
          
          {endpoint.raw_output && (
            <CollapsibleSection title="Raw Output">
              <CodeBlock
                content={endpoint.raw_output}
              />
            </CollapsibleSection>
          )}
        </div>
      )}
    </div>
  );
};

export default EndpointItem;