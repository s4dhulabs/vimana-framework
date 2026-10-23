import React, { useState } from 'react';

interface VariableCodeLinkProps {
  name: string;
  value: any;
  codeLine: string;
  lineNumber: number;
  onVariableClick?: (lineNumber: number) => void;
}

const VariableCodeLink: React.FC<VariableCodeLinkProps> = ({
  name,
  value,
  codeLine,
  lineNumber,
  onVariableClick
}) => {
  const [showTooltip, setShowTooltip] = useState(false);
  const [tooltipPosition, setTooltipPosition] = useState({ x: 0, y: 0 });

  const handleMouseEnter = (e: React.MouseEvent) => {
    const rect = e.currentTarget.getBoundingClientRect();
    setTooltipPosition({
      x: rect.x,
      y: rect.bottom + 5
    });
    setShowTooltip(true);
  };

  const handleClick = () => {
    if (onVariableClick && lineNumber) {
      onVariableClick(lineNumber);
    }
  };

  return (
    <div className="relative">
      <div
        className="flex items-start"
        onMouseEnter={handleMouseEnter}
        onMouseLeave={() => setShowTooltip(false)}
      >
        <span 
          className="font-mono text-blue-400 hover:text-blue-300 transition-colors cursor-pointer"
          onClick={handleClick}
        >
          {name}
        </span>
        <span className="ml-4 font-mono text-green-300">
          {typeof value === 'object' ? JSON.stringify(value) : String(value)}
        </span>
      </div>
      {showTooltip && codeLine && (
        <div
          className="fixed z-50 px-4 py-2 bg-gray-900/90 text-white rounded-lg shadow-lg border border-gray-700 backdrop-blur-sm"
          style={{
            left: tooltipPosition.x,
            top: tooltipPosition.y
          }}
        >
          <div className="flex items-center space-x-2 font-mono text-sm">
            {codeLine}
          </div>
        </div>
      )}
    </div>
  );
};

export default VariableCodeLink;