import React, { useState } from 'react';
import { Search } from 'lucide-react';
import DataFlowEntry from './DataFlowEntry';
import DataFlowControls from './DataFlowControls';
import CodeView from './CodeView';

interface DataFlowsTabProps {
  fuzzingData: any[];
  codeFragments: any[];
}

const DataFlowsTab: React.FC<DataFlowsTabProps> = ({
  fuzzingData,
  codeFragments
}) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedFunction, setSelectedFunction] = useState('');
  const [expandedFlows, setExpandedFlows] = useState(new Set<number>());
  const [selectedFlows, setSelectedFlows] = useState(new Set<number>());
  const [showCodeView, setShowCodeView] = useState(false);
  const [highlightedLine, setHighlightedLine] = useState<number | null>(null);

  const getFunctionNames = () => {
    const functions = new Set();
    fuzzingData.forEach(entry => {
      try {
        const rawOutput = JSON.parse(entry.raw_output || '{}');
        const viewTrigger = rawOutput.view_trigger;
        if (viewTrigger?.object) {
          functions.add(viewTrigger.object);
        }
      } catch (error) {
        console.error('Error parsing raw output:', error);
      }
    });
    return Array.from(functions);
  };

  const getDataFlowsFromExceptions = () => {
    const dataFlows = [];
    fuzzingData.forEach(exc => {
      try {
        const rawOutput = JSON.parse(exc.raw_output || '{}');
        const viewTrigger = rawOutput.view_trigger;
        
        if (!viewTrigger) return;

        const relevantTrace = exc.stack_trace?.find(trace => 
          trace.file === viewTrigger.fullpath &&
          trace.variables &&
          trace.code_snippet
        );

        if (relevantTrace?.variables) {
          const functionName = `${viewTrigger.shortpath}.${viewTrigger.object}()`;
          const relatedCodeFragments = codeFragments.filter(fragment => 
            fragment.location.shortpath === viewTrigger.shortpath &&
            fragment.location.object === viewTrigger.object
          );
          
          dataFlows.push({
            functionName,
            variables: relevantTrace.variables,
            timestamp: exc.timestamp || new Date().toISOString(),
            codeFragments: relatedCodeFragments
          });
        }
      } catch (error) {
        console.error('Error processing data flow:', error);
      }
    });
    return dataFlows;
  };

  const handleVariableClick = (lineNumber: number) => {
    setHighlightedLine(lineNumber);
    setShowCodeView(true);
  };

  const filteredDataFlows = getDataFlowsFromExceptions().filter(entry => {
    const matchesSearch = searchTerm === '' || 
      entry.functionName.toLowerCase().includes(searchTerm.toLowerCase()) ||
      JSON.stringify(entry.variables).toLowerCase().includes(searchTerm.toLowerCase());
    
    const matchesFunction = selectedFunction === '' || 
      entry.functionName.includes(selectedFunction);

    return matchesSearch && matchesFunction;
  });

  return (
    <div className="space-y-4">
      <div className="flex space-x-4 mb-4">
        <div className="flex-1">
          <div className="relative">
            <Search className="absolute left-3 top-2.5 h-4 w-4 text-gray-500" />
            <input
              type="text"
              placeholder="Search by function name or variables..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10 pr-4 py-2 w-full rounded-lg border border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
        </div>
        <div className="w-64">
          <select
            value={selectedFunction}
            onChange={(e) => setSelectedFunction(e.target.value)}
            className="w-full p-2 rounded-lg border border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">All Functions</option>
            {getFunctionNames().map(func => (
              <option key={func} value={func}>{func}</option>
            ))}
          </select>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div className="space-y-4">
          <DataFlowControls
            totalFlows={filteredDataFlows.length}
            selectedFlows={selectedFlows}
            expandedFlows={expandedFlows}
            onToggleAllExpand={() => {
              if (expandedFlows.size === filteredDataFlows.length) {
                setExpandedFlows(new Set());
              } else {
                setExpandedFlows(new Set(filteredDataFlows.map((_, i) => i)));
              }
            }}
            onToggleAllSelect={() => {
              if (selectedFlows.size === filteredDataFlows.length) {
                setSelectedFlows(new Set());
              } else {
                setSelectedFlows(new Set(filteredDataFlows.map((_, i) => i)));
              }
            }}
          />
          {filteredDataFlows.map((flow, index) => (
            <DataFlowEntry
              key={`${flow.timestamp}-${index}`}
              index={index}
              variables={flow.variables}
              codeLines={flow.codeFragments}
              timestamp={flow.timestamp}
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
              onVariableClick={handleVariableClick}
            />
          ))}
        </div>

        {showCodeView && (
          <div className="h-full border-l">
            <CodeView
              fragments={codeFragments}
              highlightedLine={highlightedLine}
            />
          </div>
        )}
      </div>
    </div>
  );
};

export default DataFlowsTab;