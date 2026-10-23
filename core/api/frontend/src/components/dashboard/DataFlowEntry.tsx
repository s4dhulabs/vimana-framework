import React from 'react';
import { ChevronDown, ChevronUp, CheckSquare, Square } from 'lucide-react';
import VariableRow from './VariableRow';
import { correlateVariablesWithCode } from '@/lib/codeProcessing';

interface DataFlowEntryProps {
  index: number;
  variables: Record<string, any>;
  timestamp: string;
  codeFragments?: Array<{ code: string[]; startLine: number; endLine: number; }>;
  isExpanded: boolean;
  isSelected: boolean;
  onToggleExpand: () => void;
  onToggleSelect: () => void;
  onVariableClick?: (lineNumber: number) => void;
}

const DataFlowEntry: React.FC<DataFlowEntryProps> = ({
  index,
  variables,
  timestamp,
  codeFragments = [],
  isExpanded,
  isSelected,
  onToggleExpand,
  onToggleSelect,
  onVariableClick
}) => {
  // Correlate variables with their code lines
  const variableMapping = correlateVariablesWithCode(variables, codeFragments);

  return (
    <div className={`mb-4 bg-gray-900 rounded-lg overflow-hidden border-2 transition-colors
      ${isSelected ? 'border-blue-500' : 'border-transparent'}`}
    >
      <div className="bg-gray-800 px-4 py-2 flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <button
            onClick={onToggleSelect}
            className="text-gray-400 hover:text-white transition-colors"
          >
            {isSelected ? (
              <CheckSquare className="w-4 h-4" />
            ) : (
              <Square className="w-4 h-4" />
            )}
          </button>
          <span className="text-gray-300 font-mono">Instance {index + 1}</span>
        </div>
        <button
          onClick={onToggleExpand}
          className="text-gray-400 hover:text-white transition-colors"
        >
          {isExpanded ? (
            <ChevronUp className="w-4 h-4" />
          ) : (
            <ChevronDown className="w-4 h-4" />
          )}
        </button>
      </div>
      {isExpanded && (
        <div className="p-4">
          <table className="w-full">
            <thead>
              <tr>
                <th className="text-left py-2 px-4 text-gray-400 border-b border-gray-700">
                  Variable
                </th>
                <th className="text-left py-2 px-4 text-gray-400 border-b border-gray-700">
                  Value
                </th>
              </tr>
            </thead>
            <tbody>
              {Object.entries(variables)
                .sort(([keyA], [keyB]) => 
                  keyA === 'request' ? 1 : (keyB === 'request' ? -1 : keyA.localeCompare(keyB))
                )
                .map(([key, value]) => (
                  <VariableRow
                    key={key}
                    name={key}
                    value={value}
                    codeLine={variableMapping[key]?.code}
                    lineNumber={variableMapping[key]?.lineNumber}
                    onVariableClick={onVariableClick}
                  />
                ))
              }
            </tbody>
          </table>
          <div className="mt-2 text-xs text-gray-500">
            Captured at: {new Date(timestamp).toLocaleString()}
          </div>
        </div>
      )}
    </div>
  );
};

export default DataFlowEntry;