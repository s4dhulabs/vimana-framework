import React, { useState } from 'react';
import { Search } from 'lucide-react';
import DataFlowControls from './DataFlowControls';
import DataFlowEntry from './DataFlowEntry';

interface DataFlow {
  variables: Record<string, any>;
  timestamp: string;
}

interface UnifiedDataFlowViewProps {
  dataFlows?: Array<DataFlow>;
  functionName?: string;
  availableFunctions?: string[];
}

const UnifiedDataFlowView: React.FC<UnifiedDataFlowViewProps> = ({
  dataFlows,
  functionName,
  availableFunctions = []
}) => {
  const [expandedFlows, setExpandedFlows] = useState(new Set<number>());
  const [selectedFlows, setSelectedFlows] = useState(new Set<number>());
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedFunction, setSelectedFunction] = useState('');

  if (!dataFlows || dataFlows.length === 0) {
    return (
      <div className="p-4 text-gray-500 text-center">
        No data flows available
      </div>
    );
  }

  const filteredDataFlows = dataFlows.filter(flow => {
    const matchesSearch = searchTerm === '' || 
      JSON.stringify(flow.variables).toLowerCase().includes(searchTerm.toLowerCase());
    
    const matchesFunction = selectedFunction === '' || 
      (functionName && functionName.includes(selectedFunction));

    return matchesSearch && matchesFunction;
  });

  const handleToggleAllExpand = () => {
    if (expandedFlows.size === filteredDataFlows.length) {
      setExpandedFlows(new Set());
    } else {
      setExpandedFlows(new Set(filteredDataFlows.map((_, i) => i)));
    }
  };

  const handleToggleAllSelect = () => {
    if (selectedFlows.size === filteredDataFlows.length) {
      setSelectedFlows(new Set());
    } else {
      setSelectedFlows(new Set(filteredDataFlows.map((_, i) => i)));
    }
  };

  return (
    <div className="p-4 space-y-4">
      <div className="flex space-x-4 mb-4">
        <div className="flex-1">
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
        </div>
        {availableFunctions.length > 0 && (
          <div className="w-64">
            <select
              value={selectedFunction}
              onChange={(e) => setSelectedFunction(e.target.value)}
              className="w-full p-2 rounded-lg border border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">All Functions</option>
              {availableFunctions.map(func => (
                <option key={func} value={func}>{func}</option>
              ))}
            </select>
          </div>
        )}
      </div>
      <DataFlowControls
        totalFlows={filteredDataFlows.length}
        selectedFlows={selectedFlows}
        expandedFlows={expandedFlows}
        onToggleAllExpand={handleToggleAllExpand}
        onToggleAllSelect={handleToggleAllSelect}
      />
      <div className="space-y-4">
        {filteredDataFlows.map((flow, index) => (
          <DataFlowEntry
            key={`${flow.timestamp}-${index}`}
            functionName={functionName || `Instance ${index + 1}`}
            variables={flow.variables}
            timestamp={flow.timestamp}
            index={index}
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
          />
        ))}
      </div>
    </div>
  );
};

export default UnifiedDataFlowView;