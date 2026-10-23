import React from 'react';
import { ChevronDown, ChevronUp, Zap, Filter, Trash2 } from 'lucide-react';

interface SelectionControlsProps {
  onSelectAll: () => void;
  onDeselectAll: () => void;
  onExpandAll: () => void;
  onCollapseAll: () => void;
  onToggleAutoAnalyze: () => void;
  onToggleFilters: () => void;
  onDeleteSelected: () => void;
  selectedCount: number;
  totalCount: number;
  isExpanded: boolean;
  isAutoAnalyzeEnabled: boolean;
  isFiltersOpen: boolean;
  onAnalyze: () => void;
}

const ControlButton = ({ 
  icon: Icon, 
  active = false, 
  onClick, 
  tooltip,
  showBadge = false,
  badgeCount = 0,
}: { 
  icon: React.ElementType; 
  active?: boolean; 
  onClick: () => void; 
  tooltip: string;
  showBadge?: boolean;
  badgeCount?: number;
}) => (
  <div className="relative group">
    <button
      onClick={onClick}
      className={`p-2 rounded-lg transition-all duration-200 ease-in-out 
        hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-offset-2 
        ${active ? 'text-blue-500' : 'text-gray-500'}`}
    >
      <Icon 
        className={`w-6 h-6 ${active ? 'animate-pulse' : ''}`}
        strokeWidth={2.2}
      />
      
      {/* Badge for showing count */}
      {showBadge && badgeCount > 0 && (
        <div className="absolute -top-1 -right-1 flex items-center justify-center w-5 h-5 bg-blue-500 text-white text-xs font-bold rounded-full">
          {badgeCount > 99 ? '99+' : badgeCount}
        </div>
      )}
    </button>
    <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 
      min-w-max z-10 pointer-events-none">
      <div className="px-3 py-2 text-xs font-medium text-white bg-gray-900 rounded-md 
        opacity-0 group-hover:opacity-100 transition-opacity">
        {tooltip}
      </div>
    </div>
  </div>
);

const SelectionControls: React.FC<SelectionControlsProps> = ({
  onSelectAll,
  onDeselectAll,
  onExpandAll,
  onCollapseAll,
  onToggleAutoAnalyze,
  onToggleFilters,
  onDeleteSelected,
  selectedCount,
  totalCount,
  isExpanded,
  isAutoAnalyzeEnabled,
  isFiltersOpen,
  onAnalyze
}) => {
  const isAllSelected = selectedCount === totalCount && totalCount > 0;

  return (
    <div className="flex items-center justify-between bg-white p-4 rounded-lg shadow-sm">
      <div className="flex items-center space-x-4">
        <button
          onClick={isAllSelected ? onDeselectAll : onSelectAll}
          className="px-3 py-1.5 text-sm font-medium rounded-lg border border-gray-300 
            hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          {isAllSelected ? 'Deselect All' : 'Select All'}
        </button>

        <button
          onClick={isExpanded ? onCollapseAll : onExpandAll}
          className="px-3 py-1.5 text-sm font-medium rounded-lg border border-gray-300 
            hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500 
            inline-flex items-center space-x-2"
        >
          {isExpanded ? (
            <>
              <ChevronUp className="w-4 h-4" />
              <span>Collapse All</span>
            </>
          ) : (
            <>
              <ChevronDown className="w-4 h-4" />
              <span>Expand All</span>
            </>
          )}
        </button>

        <div className="border-l h-8 border-gray-200" />
        
        <div className="flex items-center space-x-2">
          <ControlButton 
            icon={Zap}
            active={isAutoAnalyzeEnabled}
            onClick={onToggleAutoAnalyze}
            tooltip={`Auto Analyze: ${isAutoAnalyzeEnabled ? 'Enabled' : 'Disabled'}`}
          />
          
          <ControlButton 
            icon={Filter}
            active={isFiltersOpen}
            onClick={onToggleFilters}
            tooltip="Show/Hide Filters"
          />
          
          <ControlButton 
            icon={Trash2}
            onClick={onDeleteSelected}
            tooltip="Delete Selected Exceptions"
            showBadge={true}
            badgeCount={selectedCount}
          />
        </div>
      </div>

      {selectedCount > 0 && !isAutoAnalyzeEnabled && (
        <button
          onClick={onAnalyze}
          className="inline-flex items-center space-x-2 px-3 py-1.5 bg-blue-500 
            text-white rounded-lg hover:bg-blue-600 focus:outline-none 
            focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
        >
          <span>Analyze Selected ({selectedCount})</span>
        </button>
      )}
    </div>
  );
};

export default SelectionControls;