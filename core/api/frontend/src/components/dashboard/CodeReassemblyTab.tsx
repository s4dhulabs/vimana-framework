import React, { useState } from 'react';
import { Alert, AlertTitle, AlertDescription } from '@/components/ui/alert';
import HierarchicalCodeView from './HierarchicalCodeView';

interface CodeReassemblyTabProps {
  selectedExceptions: Set<string>;
  fuzzingData: any[];
}

interface CodeFragment {
  id: string;
  location: {
    fullpath: string;
    shortpath: string;
    object: string;
    line_number: string;
  };
  code: string[];
  startLine: number;
  endLine: number;
}

const CodeReassemblyTab: React.FC<CodeReassemblyTabProps> = ({
  selectedExceptions,
  fuzzingData
}) => {
  const [codeFragments, setCodeFragments] = useState<CodeFragment[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isReassembled, setIsReassembled] = useState(false);

  const processExceptions = (exceptions: any[]) => {
    // Group code by module and function
    const moduleSnippets: Record<string, Record<string, Map<number, string>>> = {};

    exceptions.forEach(exc => {
      try {
        const rawOutput = JSON.parse(exc.raw_output || '{}');
        const viewTrigger = rawOutput.view_trigger;
        
        if (!viewTrigger) return;

        // Find the relevant stack trace entry that matches the view trigger
        const relevantTrace = exc.stack_trace?.find((trace: any) => 
          trace.file === viewTrigger.fullpath &&
          trace.code_snippet
        );

        if (!relevantTrace || !relevantTrace.code_snippet) return;

        const moduleKey = viewTrigger.shortpath;
        const functionKey = viewTrigger.object;

        if (!moduleSnippets[moduleKey]) {
          moduleSnippets[moduleKey] = {};
        }
        
        if (!moduleSnippets[moduleKey][functionKey]) {
          moduleSnippets[moduleKey][functionKey] = new Map();
        }

        // Process each line from code_snippet
        relevantTrace.code_snippet.forEach((line: string) => {
          const match = line.match(/^\s*(\d+)\s+(.*)$/);
          if (match) {
            const [, lineNum, code] = match;
            moduleSnippets[moduleKey][functionKey].set(
              parseInt(lineNum),
              line // Keep the original line with number and indentation
            );
          }
        });
      } catch (err) {
        console.error('Error processing exception:', err);
      }
    });

    // Convert to fragments
    const fragments: CodeFragment[] = [];

    Object.entries(moduleSnippets).forEach(([modulePath, functions]) => {
      Object.entries(functions).forEach(([functionName, codeLines]) => {
        // Sort lines by line number and get continuous blocks
        const sortedLines = Array.from(codeLines.entries())
          .sort(([a], [b]) => a - b)
          .map(([_, line]) => line);

        if (sortedLines.length === 0) return;

        // Get start and end line numbers
        const lineNumbers = sortedLines.map(line => {
          const match = line.match(/^\s*(\d+)/);
          return match ? parseInt(match[1]) : 0;
        }).filter(num => num > 0);

        fragments.push({
          id: `${modulePath}.${functionName}`,
          location: {
            fullpath: modulePath,
            shortpath: modulePath,
            object: functionName,
            line_number: Math.min(...lineNumbers).toString()
          },
          code: sortedLines,
          startLine: Math.min(...lineNumbers),
          endLine: Math.max(...lineNumbers)
        });
      });
    });

    return fragments;
  };

  const handleReassemble = () => {
    setIsLoading(true);
    setError(null);

    try {
      const selectedData = fuzzingData.filter(exc => selectedExceptions.has(exc.id));
      const fragments = processExceptions(selectedData);
      setCodeFragments(fragments);
      setIsReassembled(true);
    } catch (err) {
      setError(`Error processing code: ${err}`);
    } finally {
      setIsLoading(false);
    }
  };

  if (selectedExceptions.size === 0) {
    return (
      <Alert>
        <AlertTitle>No Exceptions Selected</AlertTitle>
        <AlertDescription>
          Select exceptions from the Exceptions tab to view their reassembled code.
        </AlertDescription>
      </Alert>
    );
  }

  if (!isReassembled) {
    return (
      <div className="flex flex-col items-center justify-center p-8 space-y-4">
        <Alert>
          <AlertTitle>Ready to Reassemble</AlertTitle>
          <AlertDescription>
            {selectedExceptions.size} exception{selectedExceptions.size !== 1 ? 's' : ''} selected.
            Click the button below to reassemble the code.
          </AlertDescription>
        </Alert>
        <button
          onClick={handleReassemble}
          disabled={isLoading}
          className="flex items-center space-x-2 px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:bg-blue-300"
        >
          <span>Reassemble Code</span>
        </button>
      </div>
    );
  }

  if (error) {
    return (
      <Alert variant="destructive">
        <AlertTitle>Error</AlertTitle>
        <AlertDescription>{error}</AlertDescription>
      </Alert>
    );
  }

  return (
    <div className="h-full">
      <div className="border rounded-lg h-[calc(100vh-250px)]">
        <HierarchicalCodeView codeFragments={codeFragments} />
      </div>
    </div>
  );
};

export default CodeReassemblyTab;