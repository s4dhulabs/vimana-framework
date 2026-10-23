import React, { useState } from 'react';
import { ChevronDown, ChevronUp } from 'lucide-react';

interface VariableRowProps {
  name: string;
  value: any;
  codeLine?: string;
  lineNumber?: number;
  onVariableClick?: (lineNumber: number) => void;
}

const VariableRow: React.FC<VariableRowProps> = ({
  name,
  value,
  codeLine,
  lineNumber,
  onVariableClick
}) => {
  const displayValue = typeof value === 'object' ? JSON.stringify(value) : String(value);
  const [isExpanded, setIsExpanded] = useState(false);
  const [showTooltip, setShowTooltip] = useState(false);
  const [tooltipPosition, setTooltipPosition] = useState({ x: 0, y: 0 });
  const isLongValue = displayValue.length > 100;

  const handleMouseEnter = (e: React.MouseEvent) => {
    if (codeLine) {
      const rect = e.currentTarget.getBoundingClientRect();
      setTooltipPosition({
        x: rect.x,
        y: rect.bottom + 5
      });
      setShowTooltip(true);
    }
  };

  const handleClick = () => {
    if (lineNumber && onVariableClick) {
      onVariableClick(lineNumber);
    }
  };

  return (
    <tr className="border-b border-gray-800">
      <td 
        className="relative"
        onMouseEnter={handleMouseEnter}
        onMouseLeave={() => setShowTooltip(false)}
      >
        <div className={`py-2 px-4 font-mono cursor-pointer transition-colors ${
          lineNumber ? 'text-blue-400 hover:text-blue-300' : 'text-gray-400'
        }`}
        onClick={handleClick}>
          <div className="flex items-center space-x-2">
            {isLongValue && (
              <button 
                onClick={(e) => {
                  e.stopPropagation();
                  setIsExpanded(!isExpanded);
                }}
                className="p-1 hover:bg-gray-700 rounded"
              >
                {isExpanded ? (
                  <ChevronUp className="w-4 h-4" />
                ) : (
                  <ChevronDown className="w-4 h-4" />
                )}
              </button>
            )}
            <span>{name}</span>
          </div>

          {/* Code line tooltip */}
          {showTooltip && codeLine && (
            <div
              className="fixed z-50 px-4 py-2 bg-gray-900/90 text-white rounded-lg shadow-lg border border-gray-700 backdrop-blur-sm"
              style={{
                left: tooltipPosition.x,
                top: tooltipPosition.y
              }}
            >
              <div className="font-mono text-sm whitespace-pre">
                {codeLine}
              </div>
            </div>
          )}
        </div>
      </td>
      <td className="py-2 px-4 font-mono text-green-300">
        {isLongValue ? (
          isExpanded ? displayValue : displayValue.slice(0, 100) + '...'
        ) : (
          displayValue
        )}
      </td>
    </tr>
  );
};

export default VariableRow;