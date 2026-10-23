import React, { useState } from 'react';
import { Search } from 'lucide-react';
import DataFlowEntry from './DataFlowEntry';
import DataFlowControls from './DataFlowControls';

interface DataFlowViewProps {
  dataFlows?: Array<{
    variables: Record<string, any>;
    timestamp: string;
  }>;
  codeFragments: Array<{
    code: string[];
    startLine: number;
    endLine: number;
  }>;
  onVariableClick?: (lineNumber: number) => void;
}

const DataFlowView: React.FC<DataFlowViewProps> = ({
  dataFlows,
  codeFragments,
  onVariableClick
}) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [expandedFlows, setExpandedFlows] = useState(new Set<number>());
  const [selectedFlows, setSelectedFlows] = useState(new Set<number>());

  if (!dataFlows || dataFlows.length === 0) {
    return (
      <div className="p-4 text-gray-500 text-center">
        Select a function to view its data flow
      </div>
    );
  }

  const filteredFlows = dataFlows.filter(flow => 
    searchTerm === '' || 
    JSON.stringify(flow.variables).toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="p-4 space-y-4">
      <div className="relative">
        <Search className="absolute left-3 top-2.5 h-4 w-4 text-gray-500" />
        <input
          type="text"
          placeholder="Search in variables..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="pl-10 pr-4 py-2 w-full rounded-lg border border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
      </div>

      <DataFlowControls
        totalFlows={filteredFlows.length}
        selectedFlows={selectedFlows}
        expandedFlows={expandedFlows}
        onToggleAllExpand={() => {
          if (expandedFlows.size === filteredFlows.length) {
            setExpandedFlows(new Set());
          } else {
            setExpandedFlows(new Set(filteredFlows.map((_, i) => i)));
          }
        }}
        onToggleAllSelect={() => {
          if (selectedFlows.size === filteredFlows.length) {
            setSelectedFlows(new Set());
          } else {
            setSelectedFlows(new Set(filteredFlows.map((_, i) => i)));
          }
        }}
      />

      <div className="space-y-4">
        {filteredFlows.map((flow, index) => (
          <DataFlowEntry
            key={`${flow.timestamp}-${index}`}
            index={index}
            variables={flow.variables}
            timestamp={flow.timestamp}
            codeFragments={codeFragments}
            isExpanded={expandedFlows.has(index)}
            isSelected={selectedFlows.has(index)}
            onToggleExpand={() => {
              setExpandedFlows(prev => {
                const newSet = new Set(prev);
                if (newSet.has(index)) {
                  newSet.delete(index);
                } else {
                  newSet.add(index);
                }
                return newSet;
              });
            }}
            onToggleSelect={() => {
              setSelectedFlows(prev => {
                const newSet = new Set(prev);
                if (newSet.has(index)) {
                  newSet.delete(index);
                } else {
                  newSet.add(index);
                }
                return newSet;
              });
            }}
            onVariableClick={onVariableClick}
          />
        ))}
      </div>
    </div>
  );
};

export default DataFlowView;