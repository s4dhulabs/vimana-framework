// ExceptionsPanel.tsx
import React from 'react';
import Search from 'lucide-react';
import ExceptionFilters from './ExceptionFilters';
import ExceptionControls from './ExceptionControls';
import EnhancedEndpointItem from './EnhancedEndpointItem';

export interface ExceptionsPanelProps {
  data: any[];
  selectedExceptions: Set<string>;
  onExceptionSelect: (id: string) => void;
  onExceptionRemove: (id: string) => void;
  searchTerm: string;
  onSearchChange: (term: string) => void;
  filters: { exceptionType: string; endpoint: string };
  onFiltersChange: (filters: any) => void;
  allExpanded: boolean;
  onToggleExpand: () => void;
  autoAnalyzeEnabled: boolean;
  onToggleAutoAnalyze: () => void;
  onAnalyze: () => void;
}

export const ExceptionsPanel: React.FC<ExceptionsPanelProps> = ({
  data,
  selectedExceptions,
  onExceptionSelect,
  onExceptionRemove,
  searchTerm,
  onSearchChange,
  filters,
  onFiltersChange,
  allExpanded,
  onToggleExpand,
  autoAnalyzeEnabled,
  onToggleAutoAnalyze,
  onAnalyze
}) => {
  const filteredData = data.filter(exception => {
    const matchesSearch = searchTerm === '' || 
      JSON.stringify(exception).toLowerCase().includes(searchTerm.toLowerCase());
    
    const matchesExceptionType = filters.exceptionType === '' ||
      exception.exception_type?.toLowerCase().includes(filters.exceptionType.toLowerCase());
    
    const matchesEndpoint = filters.endpoint === '' ||
      exception.endpoint?.toLowerCase().includes(filters.endpoint.toLowerCase());

    return matchesSearch && matchesExceptionType && matchesEndpoint;
  });

  return (
    <div className="space-y-4">
      {/* Search Bar */}
      <div className="relative">
        <Search className="absolute left-3 top-2.5 h-4 w-4 text-gray-500" />
        <input
          type="text"
          placeholder="Search across all exceptions..."
          value={searchTerm}
          onChange={(e) => onSearchChange(e.target.value)}
          className="pl-10 pr-4 py-2 w-full rounded-lg border focus:ring-2 focus:ring-blue-500"
        />
      </div>

      {/* Filters */}
      <ExceptionFilters onFilterChange={onFiltersChange} />

      {/* Controls */}
      <ExceptionControls
        allExpanded={allExpanded}
        allSelected={selectedExceptions.size === filteredData.length}
        onToggleExpand={onToggleExpand}
        onToggleSelect={() => {
          if (selectedExceptions.size === filteredData.length) {
            selectedExceptions.clear();
          } else {
            filteredData.forEach(e => selectedExceptions.add(e.id));
          }
        }}
        onToggleAutoAnalyze={onToggleAutoAnalyze}
        autoAnalyzeEnabled={autoAnalyzeEnabled}
        selectedCount={selectedExceptions.size}
        onAnalyze={onAnalyze}
      />

      {/* Exception List */}
      <div className="space-y-2">
        {filteredData.map((exception) => (
          <div key={exception.id} className="flex items-start space-x-2">
            <input
              type="checkbox"
              checked={selectedExceptions.has(exception.id)}
              onChange={() => onExceptionSelect(exception.id)}
              className="mt-4"
            />
            <div className="flex-1">
              <EnhancedEndpointItem
                endpoint={exception}
                isSelected={selectedExceptions.has(exception.id)}
                onSelect={() => onExceptionSelect(exception.id)}
                onRemove={onExceptionRemove}
              />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};