import React, { useState } from 'react';
import { ChevronDown, ChevronUp, Settings, Play } from 'lucide-react';

const ExceptionsControlPanel = ({
  selectedExceptions,
  totalExceptions,
  onSelectAll,
  onDeselectAll,
  onToggleExpand,
  isAllExpanded,
  onAnalyze,
  autoAnalyzeEnabled,
  onToggleAutoAnalyze
}) => {
  return (
    <div className="flex items-center justify-between bg-gray-50 p-3 rounded-lg mb-4">
      <div className="flex items-center space-x-4">
        {/* Selection Toggle */}
        <button
          onClick={selectedExceptions.size === totalExceptions ? onDeselectAll : onSelectAll}
          className="flex items-center space-x-2 px-3 py-1.5 bg-white border rounded-lg 
                    hover:bg-gray-50 transition-colors text-sm font-medium"
        >
          <span>{selectedExceptions.size === totalExceptions ? 'Deselect All' : 'Select All'}</span>
          <span className="text-gray-500">({selectedExceptions.size}/{totalExceptions})</span>
        </button>

        {/* Expand/Collapse Toggle */}
        <button
          onClick={onToggleExpand}
          className="flex items-center space-x-2 px-3 py-1.5 bg-white border rounded-lg 
                    hover:bg-gray-50 transition-colors text-sm font-medium"
        >
          {isAllExpanded ? (
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
      </div>

      <div className="flex items-center space-x-4">
        {/* Auto-Analyze Toggle */}
        <button
          onClick={onToggleAutoAnalyze}
          className={`flex items-center space-x-2 px-3 py-1.5 rounded-lg transition-colors text-sm font-medium
            ${autoAnalyzeEnabled 
              ? 'bg-green-100 text-green-700 hover:bg-green-200' 
              : 'bg-gray-100 text-gray-600 hover:bg-gray-200'}`}
          title="Auto-analyze new exceptions"
        >
          <Play className={`w-4 h-4 ${autoAnalyzeEnabled ? 'text-green-600' : 'text-gray-500'}`} />
          <span>Auto-Analyze</span>
        </button>

        {/* Manual Analyze Button */}
        {selectedExceptions.size > 0 && (
          <button
            onClick={onAnalyze}
            className="flex items-center space-x-2 px-3 py-1.5 bg-blue-500 text-white rounded-lg 
                      hover:bg-blue-600 transition-colors text-sm font-medium"
          >
            <Settings className="w-4 h-4" />
            <span>Analyze Selected</span>
          </button>
        )}
      </div>
    </div>
  );
};

export default ExceptionsControlPanel;