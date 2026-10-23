import React from 'react';
import { ChevronDown, ChevronUp, Play, Settings, Loader } from 'lucide-react';

const IntegratedControls = ({
  selectedCount,
  totalCount,
  isAllSelected,
  isAllExpanded,
  isAutoAnalyzeEnabled,
  onToggleSelectAll,
  onToggleExpandAll,
  onToggleAutoAnalyze,
  onAnalyze,
  isAnalyzing
}) => {
  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4 mb-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          {/* Selection Toggle */}
          <button
            onClick={onToggleSelectAll}
            className="flex items-center space-x-2 px-3 py-1.5 text-sm font-medium rounded-lg
              border border-gray-200 hover:bg-gray-50 transition-colors"
          >
            <span>{isAllSelected ? 'Deselect All' : 'Select All'}</span>
            <span className="text-gray-500">({selectedCount}/{totalCount})</span>
          </button>

          {/* Expand/Collapse Toggle */}
          <button
            onClick={onToggleExpandAll}
            className="flex items-center space-x-2 px-3 py-1.5 text-sm font-medium rounded-lg
              border border-gray-200 hover:bg-gray-50 transition-colors"
          >
            {isAllExpanded ? (
              <ChevronUp className="w-4 h-4" />
            ) : (
              <ChevronDown className="w-4 h-4" />
            )}
            <span>{isAllExpanded ? 'Collapse All' : 'Expand All'}</span>
          </button>
        </div>

        <div className="flex items-center space-x-4">
          {/* Auto-Analyze Toggle */}
          <div className="flex items-center space-x-2">
            <button
              onClick={onToggleAutoAnalyze}
              className={`flex items-center space-x-2 px-3 py-1.5 text-sm font-medium rounded-lg
                transition-colors ${
                  isAutoAnalyzeEnabled
                    ? 'bg-blue-100 text-blue-700 hover:bg-blue-200'
                    : 'border border-gray-200 hover:bg-gray-50'
                }`}
            >
              <Play className="w-4 h-4" />
              <span>Auto-Analyze</span>
            </button>
          </div>

          {/* Manual Analyze Button - Only show when items are selected and auto-analyze is off */}
          {selectedCount > 0 && !isAutoAnalyzeEnabled && (
            <button
              onClick={onAnalyze}
              disabled={isAnalyzing}
              className="flex items-center space-x-2 px-3 py-1.5 text-sm font-medium rounded-lg
                bg-blue-500 text-white hover:bg-blue-600 transition-colors disabled:bg-blue-300"
            >
              {isAnalyzing ? (
                <Loader className="w-4 h-4 animate-spin" />
              ) : (
                <Settings className="w-4 h-4" />
              )}
              <span>Analyze Selected</span>
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

export default IntegratedControls;