import React, { useState, useEffect } from 'react';
import { Search, Filter, X, Info, ChevronDown, ChevronUp } from 'lucide-react';

// Exception type descriptions for tooltips
const EXCEPTION_DESCRIPTIONS = {
  // Python Built-in Exceptions
  'AttributeError': 'Raised when an attribute reference or assignment fails. Common in web apps when accessing undefined object properties.',
  'ImportError': 'Indicates an import statement failed to find or load a module. May reveal unpatched dependencies.',
  'IndexError': 'Raised when a sequence subscript is out of range. Can expose array bounds vulnerabilities.',
  'KeyError': 'Raised when a dictionary key is not found. May reveal attempts to access unauthorized data.',
  'NameError': 'Indicates an attempt to use an undefined variable. Could expose code injection attempts.',
  'RuntimeError': 'Generic runtime errors. Important for identifying unexpected program behavior.',
  'SyntaxError': 'Parse-time errors. May reveal template injection or code execution attempts.',
  'TypeError': 'Operation/function applied to inappropriate type. Common in parameter tampering.',
  'ValueError': 'Operation/function receives arg with right type but inappropriate value.',
  'ConnectionRefusedError': 'A network-level error indicating the target system actively refused the connection. Often occurs when a service is not running on the specified port or is blocked by firewall rules. In security testing, this can help identify service availability and network segmentation.',
  'UnicodeDecodeError': 'Occurs when the application fails to decode bytes into Unicode characters. In security contexts, this may indicate potential encoding-based attacks or improper handling of international character sets, which could lead to injection vulnerabilities.',
  'PermissionError': 'Indicates insufficient privileges to perform an operation. Critical for identifying privilege escalation vulnerabilities and access control issues in the application.',
  'AssertionError': 'Raised when an assert statement fails. In security testing, this might indicate broken security controls or validation mechanisms.',
  'FileNotFoundError': 'Indicates attempted access to a non-existent file. Security implications include path traversal vulnerabilities and information disclosure through error messages.',
  'OSError': 'Operating system related errors. Critical for identifying system-level vulnerabilities and resource exhaustion opportunities.',
  'IOError': 'Input/Output operation failures. In security contexts, these might indicate file handling vulnerabilities or resource exhaustion opportunities.',
  'NotImplementedError': 'Indicates unimplemented abstract methods. In security testing, these might reveal incomplete security controls or bypass opportunities.',
  'ZeroDivisionError': 'Occurs when dividing by zero. In security contexts, this might indicate DoS vulnerabilities through arithmetic operations.',
  'OverflowError': 'Indicates arithmetic operations exceeded limits. Critical for identifying potential integer overflow vulnerabilities.',
  'ModuleNotFoundError': 'Raised when a module cannot be found. Security implications include potential dependency confusion attacks or insecure module loading.',
  'SystemError': 'Indicates internal Python system errors. In security contexts, these might reveal deeper system-level vulnerabilities.',
  'MemoryError': 'Indicates insufficient memory. Critical for identifying resource exhaustion vulnerabilities and DoS opportunities.',
  'PermissionDenied': 'Django security exception when a user lacks required permissions. Critical for access control.',
  'ObjectDoesNotExist': 'Django ORM exception when querying non-existent objects. May reveal enumeration attempts.',
  'ValidationError': 'Django form/model validation failure. Important for input validation security.',
  'SuspiciousOperation': 'Django security exception for potentially malicious operations.',
  'DisallowedHost': 'Django security exception for requests from unauthorized hosts.',
  'IntegrityError': 'Database integrity constraint violation. May reveal data manipulation attempts.',
  'OperationalError': 'Database operation errors. Could indicate SQL injection attempts.',
  'DatabaseError': 'Generic database errors. Important for data access security.',
  'TimeoutError': 'Operation timeout. Could reveal timing attack vectors.',
  'SSLError': 'SSL/TLS related errors. Critical for transport security.',
  'DoesNotExist': 'Django ORM exception when querying non-existent objects. May reveal enumeration attempts.',
  'MultipleObjectsReturned': 'Django ORM exception when multiple objects are returned. May reveal enumeration attempts.',
  'ImproperlyConfigured': 'Django exception for improperly configured settings. Critical for security misconfigurations.',

};

const FilterSection = ({ 
  title, 
  items, 
  selected, 
  onChange,
  getTooltip = null,
  formatLabel = (x: string) => x 
}) => {
  const [isExpanded, setIsExpanded] = useState(true);

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-100 p-4">
      <div 
        className="flex items-center justify-between cursor-pointer mb-3"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <h3 className="font-medium text-gray-800">{title}</h3>
        {isExpanded ? (
          <ChevronUp className="h-4 w-4 text-gray-500" />
        ) : (
          <ChevronDown className="h-4 w-4 text-gray-500" />
        )}
      </div>
      
      {isExpanded && (
        <div className="space-y-2 max-h-48 overflow-y-auto pr-2">
          {items.map(item => (
            <label key={item} className="flex items-center group">
              <div className="flex-1 flex items-center space-x-2">
                <input
                  type="checkbox"
                  checked={selected.has(item)}
                  onChange={() => onChange(item)}
                  className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                />
                <span className="text-sm text-gray-700">{formatLabel(item)}</span>
              </div>
              
              {getTooltip && (
                <div className="relative flex items-center">
                  <div className="group relative">
                    <Info className="h-4 w-4 text-gray-400 opacity-0 group-hover:opacity-100 transition-opacity" />
                    <div className="absolute z-50 bottom-full right-0 mb-2 w-80 bg-gray-900 text-xs text-white p-3 rounded shadow-lg 
                      opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none max-h-60 overflow-y-auto">
                      <div className="text-sm font-medium mb-1">{item}</div>
                      <div className="text-xs text-gray-300 leading-relaxed">
                        {getTooltip(item)}
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </label>
          ))}
        </div>
      )}
    </div>
  );
};

interface ExceptionFiltersProps {
  fuzzingData: any[];
  onFiltersChange: (filters: any) => void;
  onSearchChange: (searchTerm: string) => void;
}

const ExceptionFilters: React.FC<ExceptionFiltersProps> = ({
  fuzzingData,
  onFiltersChange,
  onSearchChange
}) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [showFilters, setShowFilters] = useState(false);
  const [selectedExceptionTypes, setSelectedExceptionTypes] = useState<Set<string>>(new Set());
  const [selectedEndpoints, setSelectedEndpoints] = useState<Set<string>>(new Set());
  const [selectedApps, setSelectedApps] = useState<Set<string>>(new Set());
  const [selectedMethods, setSelectedMethods] = useState<Set<string>>(new Set());
  const [selectedSecurityIssues, setSelectedSecurityIssues] = useState<Set<string>>(new Set());

  // Extract unique values
  const getUniqueValues = () => {
    const apps = new Set<string>();
    const endpoints = new Set<string>();
    const methods = new Set<string>();
    const securityIssues = new Set<string>();
    const exceptionTypes = new Set<string>();

    fuzzingData.forEach(item => {
      // Extract app name from view_trigger
      if (item.raw_output) {
        try {
          const viewTrigger = JSON.parse(item.raw_output).view_trigger;
          if (viewTrigger?.app_name) {
            const appName = viewTrigger.app_name;
            apps.add(appName);
          }
        } catch (e) {
          console.error('Error parsing raw_output:', e);
        }
      }

      // Get relative endpoint path
      if (item.endpoint) {
        try {
          const url = new URL(item.endpoint);
          endpoints.add(url.pathname);
        } catch {
          endpoints.add(item.endpoint);
        }
      }

      // Method
      if (item.method) {
        methods.add(item.method);
      }

      // Exception type
      if (item.exception_type) {
        exceptionTypes.add(item.exception_type);
      }

      // Security issues
      if (item.security_issues) {
        item.security_issues.forEach((issue: any) => {
          if (issue.issue_type) {
            securityIssues.add(issue.issue_type);
          }
        });
      }
    });

    return {
      apps: Array.from(apps),
      endpoints: Array.from(endpoints),
      methods: Array.from(methods),
      exceptionTypes: Array.from(exceptionTypes),
      securityIssues: Array.from(securityIssues)
    };
  };

  const uniqueValues = getUniqueValues();

  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setSearchTerm(value);
    onSearchChange(value);
  };

  const clearSearch = () => {
    setSearchTerm('');
    onSearchChange('');
  };

  useEffect(() => {
    onFiltersChange({
      exceptionTypes: Array.from(selectedExceptionTypes),
      endpoints: Array.from(selectedEndpoints),
      apps: Array.from(selectedApps),
      methods: Array.from(selectedMethods),
      securityIssues: Array.from(selectedSecurityIssues)
    });
  }, [
    selectedExceptionTypes,
    selectedEndpoints,
    selectedApps,
    selectedMethods,
    selectedSecurityIssues
  ]);

  const clearFilters = () => {
    setSelectedExceptionTypes(new Set());
    setSelectedEndpoints(new Set());
    setSelectedApps(new Set());
    setSelectedMethods(new Set());
    setSelectedSecurityIssues(new Set());
  };

  return (
    <div className="mb-6 space-y-4">
      {/* Search Bar */}
      <div className="relative">
        <Search className="absolute left-3 top-2.5 h-5 w-5 text-gray-400" />
        <input
          type="text"
          placeholder="Search across all exceptions..."
          value={searchTerm}
          onChange={handleSearchChange}
          className="w-full pl-10 pr-10 py-2 rounded-lg border border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
        {searchTerm && (
          <button
            onClick={clearSearch}
            className="absolute right-3 top-2.5 text-gray-400 hover:text-gray-600"
          >
            <X className="h-5 w-5" />
          </button>
        )}
      </div>

      {/* Filters */}
      <div className="bg-gray-50 rounded-lg p-4">
        <div className="flex items-center justify-between mb-4">
          <button
            onClick={() => setShowFilters(!showFilters)}
            className="flex items-center space-x-2 text-gray-700 hover:text-gray-900"
          >
            <Filter className="h-5 w-5" />
            <span>Filters</span>
          </button>
          
          {/* Show clear filters only if any filter is active */}
          {(selectedExceptionTypes.size > 0 || 
            selectedEndpoints.size > 0 || 
            selectedApps.size > 0 || 
            selectedMethods.size > 0 || 
            selectedSecurityIssues.size > 0) && (
            <button
              onClick={clearFilters}
              className="flex items-center space-x-2 text-red-600 hover:text-red-700"
            >
              <X className="h-4 w-4" />
              <span>Clear filters</span>
            </button>
          )}
        </div>

        {showFilters && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {/* Exception Types */}
            <FilterSection
              title="Exception Types"
              items={uniqueValues.exceptionTypes}
              selected={selectedExceptionTypes}
              onChange={(type) => {
                setSelectedExceptionTypes(prev => {
                  const newSet = new Set(prev);
                  if (newSet.has(type)) {
                    newSet.delete(type);
                  } else {
                    newSet.add(type);
                  }
                  return newSet;
                });
              }}
              getTooltip={(type) => EXCEPTION_DESCRIPTIONS[type] || ' Additional exception type identified during testing. '}
            />

            {/* Applications */}
            <FilterSection
              title="Applications"
              items={uniqueValues.apps}
              selected={selectedApps}
              onChange={(app) => {
                setSelectedApps(prev => {
                  const newSet = new Set(prev);
                  if (newSet.has(app)) {
                    newSet.delete(app);
                  } else {
                    newSet.add(app);
                  }
                  return newSet;
                });
              }}
            />

            {/* Endpoints */}
            <FilterSection
              title="Endpoints"
              items={uniqueValues.endpoints}
              selected={selectedEndpoints}
              onChange={(endpoint) => {
                setSelectedEndpoints(prev => {
                  const newSet = new Set(prev);
                  if (newSet.has(endpoint)) {
                    newSet.delete(endpoint);
                  } else {
                    newSet.add(endpoint);
                  }
                  return newSet;
                });
              }}
            />

            {/* Methods */}
            <FilterSection
              title="HTTP Methods"
              items={uniqueValues.methods}
              selected={selectedMethods}
              onChange={(method) => {
                setSelectedMethods(prev => {
                  const newSet = new Set(prev);
                  if (newSet.has(method)) {
                    newSet.delete(method);
                  } else {
                    newSet.add(method);
                  }
                  return newSet;
                });
              }}
            />

            {/* Security Issues */}
            <FilterSection
              title="Security Issues"
              items={uniqueValues.securityIssues}
              selected={selectedSecurityIssues}
              onChange={(issue) => {
                setSelectedSecurityIssues(prev => {
                  const newSet = new Set(prev);
                  if (newSet.has(issue)) {
                    newSet.delete(issue);
                  } else {
                    newSet.add(issue);
                  }
                  return newSet;
                });
              }}
            />
          </div>
        )}
      </div>
    </div>
  );
};

export default ExceptionFilters;