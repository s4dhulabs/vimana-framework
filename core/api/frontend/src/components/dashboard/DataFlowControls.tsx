import React from 'react';
import { ChevronDown, ChevronUp, CheckSquare, Square } from 'lucide-react';

interface DataFlowControlsProps {
  totalFlows: number;
  selectedFlows: Set<string>;
  expandedFlows: Set<string>;
  onToggleAllExpand: () => void;
  onToggleAllSelect: () => void;
}

const DataFlowControls: React.FC<DataFlowControlsProps> = ({
  totalFlows,
  selectedFlows,
  expandedFlows,
  onToggleAllExpand,
  onToggleAllSelect
}) => {
  const allExpanded = expandedFlows.size === totalFlows;
  const allSelected = selectedFlows.size === totalFlows;

  return (
    <div className="flex items-center justify-between mb-4 px-4 py-2 bg-gray-800 rounded-lg">
      <div className="flex items-center space-x-4">
        <button
          onClick={onToggleAllExpand}
          className="flex items-center space-x-2 text-gray-300 hover:text-white transition-colors"
        >
          {allExpanded ? (
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
        <div className="w-px h-6 bg-gray-700" />
        <button
          onClick={onToggleAllSelect}
          className="flex items-center space-x-2 text-gray-300 hover:text-white transition-colors"
        >
          {allSelected ? (
            <>
              <CheckSquare className="w-4 h-4" />
              <span>Deselect All</span>
            </>
          ) : (
            <>
              <Square className="w-4 h-4" />
              <span>Select All</span>
            </>
          )}
        </button>
      </div>
      <div className="text-sm text-gray-400">
        {selectedFlows.size} of {totalFlows} selected
      </div>
    </div>
  );
};

export default DataFlowControls;