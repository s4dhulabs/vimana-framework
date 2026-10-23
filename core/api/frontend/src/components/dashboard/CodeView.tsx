import React, { useEffect, useRef } from 'react';

interface CodeViewProps {
  fragments?: Array<{
    code: string[];
    startLine: number;
    endLine: number;
  }>;
  highlightedLine?: number;
  onLineClick?: (lineNumber: number) => void;
}

const CodeView: React.FC<CodeViewProps> = ({ 
  fragments, 
  highlightedLine,
  onLineClick 
}) => {
  const codeRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (highlightedLine && codeRef.current) {
      const lineElement = codeRef.current.querySelector(
        `[data-line-number="${highlightedLine}"]`
      );

      if (lineElement) {
        lineElement.scrollIntoView({
          behavior: 'smooth',
          block: 'center'
        });

        lineElement.classList.add('bg-green-500/30');
        
        const pulseAnimation = lineElement.animate(
          [
            { backgroundColor: 'rgba(34, 197, 94, 0.3)' },  // green-500
            { backgroundColor: 'rgba(34, 197, 94, 0.1)' },
            { backgroundColor: 'rgba(34, 197, 94, 0.3)' }
          ],
          {
            duration: 2000,
            iterations: 2
          }
        );

        pulseAnimation.onfinish = () => {
          lineElement.classList.remove('bg-blue-500/30');
        };
      }
    }
  }, [highlightedLine]);

  if (!fragments || fragments.length === 0) {
    return (
      <div className="p-4 text-gray-500 text-center">
        Select a function to view its code
      </div>
    );
  }

  return (
    <div 
      ref={codeRef}
      className="bg-gray-900 p-4 rounded-lg overflow-x-auto"
    >
      <pre className="text-white font-mono text-sm">
        <code>
          {fragments.map((fragment, fragmentIndex) => (
            <React.Fragment key={fragmentIndex}>
              {fragment.code.map((line, lineIndex) => {
                // Extract the original line number from the code line
                const lineNumberMatch = line.match(/^\s*(\d+)/);
                const originalLineNumber = lineNumberMatch ? parseInt(lineNumberMatch[1]) : null;
                
                return (
                  <div
                    key={`${fragmentIndex}-${lineIndex}`}
                    className={`group transition-colors duration-200 flex whitespace-pre ${
                      originalLineNumber === highlightedLine ? 'bg-blue-500/30' : 'hover:bg-gray-800'
                    }`}
                    data-line-number={originalLineNumber}
                    onClick={() => onLineClick?.(originalLineNumber || lineIndex + 1)}
                  >
                    {/* Just the relative line count */}
                    <span className="w-8 text-right pr-2 select-none text-gray-500">
                      {(lineIndex + 1).toString().padStart(2, ' ')}
                    </span>
                    {/* The rest of the line (which includes the original line number) */}
                    <span className="flex-1">
                      {line}
                    </span>
                  </div>
                );
              })}
              {fragmentIndex < fragments.length - 1 && (
                <div className="text-gray-500 my-2 pl-2 border-l-2 border-gray-700">
                  # ... missing code ...
                </div>
              )}
            </React.Fragment>
          ))}
        </code>
      </pre>
    </div>
  );
};

export default CodeView;