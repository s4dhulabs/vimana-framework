import React, { useState, useEffect, useRef } from 'react';
import { 
  ChevronDown, 
  ChevronUp, 
  ChevronRight,
  Code, 
  Folder, 
  FileCode, 
  GitBranch, 
  Copy, 
  Check,
  Search,
  Github,
  Square
} from 'lucide-react';

// TreeNode interface for file structure
interface TreeNode {
  id: string;
  type: 'folder' | 'file' | 'function';
  name: string;
  children?: TreeNode[];
  path: string;
  fragments?: {
    code: string[];
    startLine: number;
    endLine: number;
  }[];
  dataFlows?: Array<{
    variables: Record<string, any>;
    timestamp: string;
  }>;
}

// Props for the main component
interface CodeAnalysisTabProps {
  selectedExceptions: Set<string>;
  fuzzingData: any[];
  isAnalyzed: boolean;
}

// Tree node component for file structure navigation
const TreeNodeComponent = ({ 
  node, 
  onSelect, 
  selectedPath,
  level = 0 
}) => {
  const [isExpanded, setIsExpanded] = useState(true);
  const indent = level * 16;
  
  const getIcon = () => {
    switch (node.type) {
      case 'folder':
        return <Folder className="w-4 h-4 text-gray-400" />;
      case 'file':
        return <FileCode className="w-4 h-4 text-blue-400" />;
      case 'function':
        return <Code className="w-4 h-4 text-green-400" />;
    }
  };

  const isSelected = selectedPath === node.path;

  return (
    <div>
      <div
        className={`
          flex items-center py-2 px-2 cursor-pointer 
          transition-all duration-200 ease-in-out
          ${isSelected 
            ? 'bg-blue-100 border-l-4 border-blue-500 shadow-sm' 
            : 'hover:bg-gray-100 border-l-4 border-transparent'
          }
        `}
        style={{ paddingLeft: `${indent}px` }}
        onClick={() => {
          if (node.children?.length) {
            setIsExpanded(!isExpanded);
          }
          onSelect(node);
        }}
      >
        {node.children && node.children.length > 0 && (
          <div className={`
            p-1 rounded transition-colors duration-200
            ${isSelected ? 'hover:bg-blue-200' : 'hover:bg-gray-200'}
          `}>
            {isExpanded ? (
              <ChevronDown className="w-4 h-4" />
            ) : (
              <ChevronRight className="w-4 h-4" />
            )}
          </div>
        )}
        {!node.children && <div className="w-6" />}
        {getIcon()}
        <span className={`
          ml-2 font-mono text-sm
          ${isSelected ? 'font-semibold text-blue-800' : 'text-gray-700'}
        `}>
          {node.name}
        </span>
      </div>
      
      {isExpanded && node.children && (
        <div>
          {node.children.map((child) => (
            <TreeNodeComponent
              key={child.id}
              node={child}
              onSelect={onSelect}
              selectedPath={selectedPath}
              level={level + 1}
            />
          ))}
        </div>
      )}
    </div>
  );
};

// Code viewer component
const CodeView = ({ fragments, highlightedLine }) => {
  const [isCopied, setIsCopied] = useState(false);
  const codeRef = useRef(null);
  
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
  
  const handleCopy = () => {
    if (!fragments || fragments.length === 0) return;
    
    const codeText = fragments
      .map(fragment => fragment.code.join('\n'))
      .join('\n\n# ... missing code ...\n\n');
    
    navigator.clipboard.writeText(codeText);
    setIsCopied(true);
    
    setTimeout(() => {
      setIsCopied(false);
    }, 2000);
  };

  if (!fragments || fragments.length === 0) {
    return (
      <div className="p-4 text-gray-500 text-center">
        Select a function to view its code
      </div>
    );
  }

  return (
    <div className="relative bg-gray-900 p-4 rounded-lg">
      <button 
        onClick={handleCopy}
        className="absolute top-4 right-4 p-2 rounded-lg bg-gray-800 text-gray-300 hover:bg-gray-700 transition-colors"
        title="Copy code"
      >
        {isCopied ? <Check className="w-4 h-4 text-green-400" /> : <Copy className="w-4 h-4" />}
      </button>
      
      <pre 
        ref={codeRef}
        className="text-white font-mono text-sm pr-12 overflow-x-auto"
      >
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

// Variable row in data flow
const VariableRow = ({ name, value, codeLine, lineNumber, onVariableClick }) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const [showTooltip, setShowTooltip] = useState(false);
  const [tooltipPosition, setTooltipPosition] = useState({ x: 0, y: 0 });
  
  const displayValue = typeof value === 'object' ? JSON.stringify(value) : String(value);
  const isLongValue = displayValue.length > 100;

  const handleMouseEnter = (e) => {
    const rect = e.currentTarget.getBoundingClientRect();
    setTooltipPosition({
      x: rect.x,
      y: rect.bottom + 5
    });
    setShowTooltip(true);
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
        <div 
          className={`py-2 px-4 font-mono cursor-pointer transition-colors ${
            codeLine ? 'text-blue-400 hover:text-blue-300' : 'text-gray-400'
          }`}
          onClick={handleClick}
        >
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

          {/* Enhanced tooltip: Shows code line or message if variable not found */}
          {showTooltip && (
            <div
              className="fixed z-50 px-4 py-2 bg-gray-900/90 text-white rounded-lg shadow-lg border border-gray-700 backdrop-blur-sm"
              style={{
                left: tooltipPosition.x,
                top: tooltipPosition.y,
                maxWidth: '400px'
              }}
            >
              {codeLine ? (
                <div className="font-mono text-sm whitespace-pre">
                  {codeLine}
                </div>
              ) : (
                <div className="text-sm text-yellow-300">
                  <span className="font-semibold">Variable not found in code snippet.</span>
                  <p className="text-gray-300 mt-1">More tests and metadata are needed to reassemble this part of the code.</p>
                </div>
              )}
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

// Data flow entry component
const DataFlowEntry = ({ 
  variables, 
  timestamp, 
  index, 
  codeFragments, 
  onVariableClick,
  isExpanded = false,
  isSelected = false,
  onToggleExpand,
  onToggleSelect
}) => {
  const [isCopied, setIsCopied] = useState(false);
  
  // Find variable mapping in code
  const findVariableInCode = (varName) => {
    if (!codeFragments) return null;
    
    for (const fragment of codeFragments) {
      for (const line of fragment.code) {
        if (line.includes(varName)) {
          // Extract line number
          const match = line.match(/^\s*(\d+)/);
          const lineNumber = match ? parseInt(match[1]) : null;
          return { 
            codeLine: line,
            lineNumber
          };
        }
      }
    }
    return null;
  };
  
  const handleCopy = () => {
    // Copy all variables except 'request'
    const filteredVariables = { ...variables };
    delete filteredVariables.request;
    
    navigator.clipboard.writeText(JSON.stringify(filteredVariables, null, 2));
    setIsCopied(true);
    
    setTimeout(() => {
      setIsCopied(false);
    }, 2000);
  };

  // Handle the entire entry being clicked to toggle expansion
  const handleEntryClick = (e) => {
    // Avoid toggling when clicking copy button or variables
    if (e.target.closest('.no-toggle')) return;
    onToggleExpand();
  };

  return (
    <div 
      className={`mb-4 bg-gray-900 rounded-lg overflow-hidden border-2 cursor-pointer ${
        isSelected ? 'border-blue-500' : (isExpanded ? 'border-blue-300' : 'border-transparent hover:border-blue-300')
      }`}
      onClick={handleEntryClick}
    >
      <div className="bg-gray-800 px-4 py-2 flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div 
            className="no-toggle p-1 hover:bg-gray-700 rounded transition-colors"
            onClick={(e) => {
              e.stopPropagation();
              onToggleSelect();
            }}
          >
            {isSelected ? (
              <Check className="w-4 h-4 text-blue-400" />
            ) : (
              <Square className="w-4 h-4 text-gray-400" />
            )}
          </div>
          <span className="text-gray-300 font-mono">Data Flow Instance {index + 1}</span>
        </div>
        <div className="flex items-center space-x-3 no-toggle">
          <button
            onClick={(e) => {
              e.stopPropagation();
              handleCopy();
            }}
            className="p-1 rounded bg-gray-700 text-gray-300 hover:bg-gray-600 transition-colors"
            title="Copy variables as JSON"
          >
            {isCopied ? <Check className="w-4 h-4 text-green-400" /> : <Copy className="w-4 h-4" />}
          </button>
          {isExpanded ? (
            <ChevronUp className="w-4 h-4 text-gray-400" />
          ) : (
            <ChevronDown className="w-4 h-4 text-gray-400" />
          )}
        </div>
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
            <tbody className="no-toggle">
              {Object.entries(variables)
                .sort(([keyA], [keyB]) => keyA === 'request' ? 1 : (keyB === 'request' ? -1 : keyA.localeCompare(keyB)))
                .map(([key, value]) => {
                  const varInCode = findVariableInCode(key);
                  return (
                    <VariableRow
                      key={key}
                      name={key}
                      value={value}
                      codeLine={varInCode?.codeLine}
                      lineNumber={varInCode?.lineNumber}
                      onVariableClick={onVariableClick}
                    />
                  );
                })
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

// Data flow view component
const DataFlowView = ({ dataFlows, codeFragments, onVariableClick }) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [expandedFlows, setExpandedFlows] = useState(new Set());
  const [selectedFlows, setSelectedFlows] = useState(new Set());

  if (!dataFlows || dataFlows.length === 0) {
    return (
      <div className="p-4 text-gray-500 text-center">
        Select a function to view its data flow
      </div>
    );
  }

  // Filter data flows based on search term (checking both variable names and values)
  const filteredFlows = dataFlows.filter(flow => {
    if (searchTerm === '') return true;
    
    const searchTermLower = searchTerm.toLowerCase();
    
    // Check if any variable name or value contains the search term
    return Object.entries(flow.variables).some(([key, value]) => {
      const keyMatch = key.toLowerCase().includes(searchTermLower);
      const valueMatch = typeof value === 'object' 
        ? JSON.stringify(value).toLowerCase().includes(searchTermLower)
        : String(value).toLowerCase().includes(searchTermLower);
      
      return keyMatch || valueMatch;
    });
  });

  const handleToggleAllExpand = () => {
    if (expandedFlows.size === filteredFlows.length) {
      setExpandedFlows(new Set());
    } else {
      setExpandedFlows(new Set(filteredFlows.map((_, i) => i)));
    }
  };

  const handleToggleAllSelect = () => {
    if (selectedFlows.size === filteredFlows.length) {
      setSelectedFlows(new Set());
    } else {
      setSelectedFlows(new Set(filteredFlows.map((_, i) => i)));
    }
  };

  return (
    <div className="p-4 space-y-4">
      <div className="relative">
        <Search className="absolute left-3 top-2.5 h-4 w-4 text-gray-500" />
        <input
          type="text"
          placeholder="Search in variables and values..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="pl-10 pr-4 py-2 w-full rounded-lg border border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
      </div>

      <div className="flex items-center justify-between mb-4 px-4 py-2 bg-gray-800 rounded-lg">
        <div className="flex items-center space-x-4">
          <button
            onClick={handleToggleAllExpand}
            className="flex items-center space-x-2 text-gray-300 hover:text-white transition-colors"
          >
            {expandedFlows.size === filteredFlows.length ? (
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
            onClick={handleToggleAllSelect}
            className="flex items-center space-x-2 text-gray-300 hover:text-white transition-colors"
          >
            {selectedFlows.size === filteredFlows.length ? (
              <>
                <Check className="w-4 h-4" />
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
          {selectedFlows.size} of {filteredFlows.length} selected
        </div>
      </div>

      {filteredFlows.map((flow, index) => (
        <DataFlowEntry
          key={`${flow.timestamp}-${index}`}
          variables={flow.variables}
          timestamp={flow.timestamp}
          index={index}
          codeFragments={codeFragments}
          onVariableClick={onVariableClick}
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
  );
};

// Git search results component
const GitSearchView = ({ projectName }) => {
  const [isLoading, setIsLoading] = useState(true);
  const [results, setResults] = useState([]);

  useEffect(() => {
    // Simulate fetching Git search results
    setIsLoading(true);
    
    // Mock data for the demonstration
    setTimeout(() => {
      setResults([
        { name: `${projectName}`, owner: 'original-repo', stars: 245, url: '#', description: 'Original repository for the project' },
        { name: `${projectName}-fork`, owner: 'security-researcher', stars: 12, url: '#', description: 'Security-focused fork with vulnerability fixes' },
        { name: `${projectName}-extension`, owner: 'community-dev', stars: 87, url: '#', description: 'Extended version with additional modules' },
      ]);
      setIsLoading(false);
    }, 1500);
  }, [projectName]);

  if (isLoading) {
    return (
      <div className="flex justify-center items-center p-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
        <span className="ml-3 text-gray-500">Searching Git repositories...</span>
      </div>
    );
  }

  return (
    <div className="p-4 space-y-4">
      <div className="text-sm text-gray-500 mb-4">
        Found {results.length} repositories matching "{projectName}"
      </div>
      
      {results.map((repo, index) => (
        <div key={index} className="border border-gray-200 rounded-lg p-4 hover:bg-gray-50 transition-colors">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <Github className="w-5 h-5 text-gray-700" />
              <a href={repo.url} className="text-blue-600 hover:underline font-medium">{repo.name}</a>
            </div>
            <div className="flex items-center text-gray-500 text-sm">
              <span>⭐ {repo.stars}</span>
            </div>
          </div>
          <div className="mt-2 text-sm text-gray-600">
            {repo.description}
          </div>
          <div className="mt-2 text-xs text-gray-500">
            by {repo.owner}
          </div>
        </div>
      ))}
    </div>
  );
};

// Main code analysis tab component
const EnhancedCodeAnalysisTab = ({
  selectedExceptions,
  fuzzingData,
  isAnalyzed
}) => {
  const [treeData, setTreeData] = useState([]);
  const [selectedNode, setSelectedNode] = useState(null);
  const [activeView, setActiveView] = useState('code');
  const [highlightedLine, setHighlightedLine] = useState(null);
  const [codeFragments, setCodeFragments] = useState([]);
  const [dataFlowEntries, setDataFlowEntries] = useState([]);
  const [error, setError] = useState(null);

  // Process exceptions to extract code fragments and data flows
  useEffect(() => {
    if (isAnalyzed && selectedExceptions.size > 0) {
      try {
        const { fragments, dataFlows } = processExceptions(
          fuzzingData.filter(exc => selectedExceptions.has(exc.id))
        );
        setCodeFragments(fragments);
        setDataFlowEntries(dataFlows);
        
        // Build the tree structure
        const tree = buildTree(fragments, dataFlows);
        setTreeData(tree);
      } catch (err) {
        setError(`Error processing exceptions: ${err instanceof Error ? err.message : String(err)}`);
      }
    }
  }, [isAnalyzed, selectedExceptions, fuzzingData]);

  // Process exceptions to extract code fragments and data flows
  const processExceptions = (exceptions) => {
    // Group code by module and function
    const moduleSnippets = {};
    const dataFlowsByFunction = {};

    exceptions.forEach(exc => {
      try {
        const rawOutput = exc.raw_output ? JSON.parse(exc.raw_output) : {};
        const viewTrigger = rawOutput.view_trigger || {};
        
        if (!viewTrigger.shortpath) return;

        const relevantTrace = exc.stack_trace?.find(trace => 
          trace.file === viewTrigger.fullpath
        );

        if (!relevantTrace) return;

        const moduleKey = viewTrigger.shortpath;
        const functionKey = viewTrigger.object;
        const functionPath = `${moduleKey}.${functionKey}`;

        // Process code snippet if available
        if (relevantTrace.code_snippet) {
          if (!moduleSnippets[moduleKey]) {
            moduleSnippets[moduleKey] = {};
          }
          
          if (!moduleSnippets[moduleKey][functionKey]) {
            moduleSnippets[moduleKey][functionKey] = new Map();
          }

          // Process each line from code_snippet
          relevantTrace.code_snippet.forEach(line => {
            const match = line.match(/^\s*(\d+)\s+(.*)$/);
            if (match) {
              const [, lineNum] = match;
              const lineNumber = parseInt(lineNum);
              moduleSnippets[moduleKey][functionKey].set(lineNumber, line);
            }
          });
        }

        // Process data flow - Add ALL instances
        if (!dataFlowsByFunction[functionPath]) {
          dataFlowsByFunction[functionPath] = [];
        }

        // Only add if there are variables
        if (relevantTrace.variables && Object.keys(relevantTrace.variables).length > 0) {
          dataFlowsByFunction[functionPath].push({
            variables: relevantTrace.variables,
            timestamp: exc.timestamp || new Date().toISOString()
          });
        }
      } catch (error) {
        console.error('Error processing exception:', error);
      }
    });

    // Convert code snippets to fragments
    const fragments = [];

    Object.entries(moduleSnippets).forEach(([modulePath, functions]) => {
      Object.entries(functions).forEach(([functionName, codeLines]) => {
        // Sort lines by line number
        const sortedLines = Array.from(codeLines.entries())
          .sort(([a], [b]) => a - b)
          .map(([_, line]) => line);

        if (sortedLines.length === 0) return;

        // Find continuous blocks of code
        let currentBlock = {
          startLine: parseInt(sortedLines[0].match(/^\s*(\d+)/)[1]),
          lines: [sortedLines[0]]
        };
        const blocks = [];

        for (let i = 1; i < sortedLines.length; i++) {
          const currentLineNum = parseInt(sortedLines[i].match(/^\s*(\d+)/)[1]);
          const prevLineNum = parseInt(sortedLines[i-1].match(/^\s*(\d+)/)[1]);

          if (currentLineNum !== prevLineNum + 1) {
            // End current block and start new one
            blocks.push(currentBlock);
            currentBlock = {
              startLine: currentLineNum,
              lines: []
            };
          }
          currentBlock.lines.push(sortedLines[i]);
        }
        blocks.push(currentBlock);

        fragments.push({
          id: `${modulePath}.${functionName}`,
          location: {
            fullpath: modulePath,
            shortpath: modulePath,
            object: functionName,
            line_number: blocks[0].startLine.toString()
          },
          code: blocks.map(block => block.lines).flat(),
          startLine: blocks[0].startLine,
          endLine: parseInt(blocks[blocks.length - 1].lines[blocks[blocks.length - 1].lines.length - 1].match(/^\s*(\d+)/)[1])
        });
      });
    });

    // Convert data flows keeping ALL instances for each function
    const dataFlows = Object.entries(dataFlowsByFunction).map(([functionName, flows]) => ({
      functionName,
      dataFlows: flows
    }));

    return { fragments, dataFlows };
  };

  // Build tree structure from code fragments and data flows
  const buildTree = (fragments, dataFlows) => {
    const tree = {};
    
    // Process code fragments
    fragments.forEach(fragment => {
      const parts = fragment.location.shortpath.split('.');
      let currentPath = '';
      
      // Build folder structure
      parts.forEach((part, index) => {
        const newPath = currentPath ? `${currentPath}.${part}` : part;
        
        if (!tree[newPath]) {
          tree[newPath] = {
            id: newPath,
            name: part,
            type: index === parts.length - 1 ? 'file' : 'folder',
            path: newPath,
            children: []
          };
          
          if (currentPath && tree[currentPath]) {
            tree[currentPath].children.push(tree[newPath]);
          }
        }
        
        currentPath = newPath;
      });

      // Add function node
      const functionPath = `${currentPath}.${fragment.location.object}`;
      if (!tree[functionPath]) {
        const functionNode = {
          id: functionPath,
          name: `${fragment.location.object}()`,
          type: 'function',
          path: functionPath,
          fragments: [],
          dataFlows: []
        };
        
        tree[currentPath].children.push(functionNode);
        tree[functionPath] = functionNode;
      }
      
      // Add code fragments
      tree[functionPath].fragments.push({
        code: fragment.code,
        startLine: fragment.startLine,
        endLine: fragment.endLine
      });
    });

    // Add data flow information
    dataFlows.forEach(entry => {
      const functionPath = entry.functionName;
      if (tree[functionPath]) {
        tree[functionPath].dataFlows = entry.dataFlows;
      }
    });

    // Return only root nodes
    return Object.values(tree).filter(node => !node.path.includes('.'));
  };

  const handleNodeSelect = (node) => {
    setSelectedNode(node);
    setHighlightedLine(null);
  };

  const handleVariableClick = (lineNumber) => {
    setActiveView('code');
    setHighlightedLine(lineNumber);
  };

  if (selectedExceptions.size === 0) {
    return (
      <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
        <div className="text-lg font-medium text-blue-800">No Exceptions Selected</div>
        <p className="mt-2 text-blue-600">
          Select exceptions from the Exceptions tab to analyze their code and data flow.
        </p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
        <div className="text-lg font-medium text-red-800">Error</div>
        <p className="mt-2 text-red-600">{error}</p>
      </div>
    );
  }

  if (!isAnalyzed) {
    return (
      <div className="p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
        <div className="text-lg font-medium text-yellow-800">Analysis Required</div>
        <p className="mt-2 text-yellow-600">
          Click "Analyze" in the Exceptions tab to view the analysis.
        </p>
      </div>
    );
  }

  // Project name from the selected node
  const projectName = 
    selectedNode?.path?.split('.')[0] || 
    (treeData.length > 0 ? treeData[0].name : 'Unknown');

  return (
    <div className="h-full">
      <div className="border rounded-lg h-[calc(100vh-250px)] flex">
        {/* File/function tree */}
        <div className="w-1/4 border-r overflow-y-auto">
          {treeData.map(node => (
            <TreeNodeComponent
              key={node.id}
              node={node}
              onSelect={handleNodeSelect}
              selectedPath={selectedNode?.path || ''}
            />
          ))}
        </div>
        
        {/* Content area */}
        <div className="flex-1 overflow-y-auto">
          {selectedNode?.type === 'function' ? (
            <div className="p-4">
              {/* View selector tabs */}
              <div className="flex mb-4 border-b">
                <button
                  onClick={() => setActiveView('code')}
                  className={`flex items-center space-x-2 px-4 py-2 border-b-2 transition-colors ${
                    activeView === 'code' 
                      ? 'border-blue-500 text-blue-600' 
                      : 'border-transparent text-gray-500 hover:text-gray-700'
                  }`}
                >
                  <Code className="w-4 h-4" />
                  <span>Code</span>
                </button>
                <button
                  onClick={() => setActiveView('dataflow')}
                  className={`flex items-center space-x-2 px-4 py-2 border-b-2 transition-colors ${
                    activeView === 'dataflow' 
                      ? 'border-blue-500 text-blue-600' 
                      : 'border-transparent text-gray-500 hover:text-gray-700'
                  }`}
                >
                  <GitBranch className="w-4 h-4" />
                  <span>Data Flow</span>
                </button>
                <button
                  onClick={() => setActiveView('git')}
                  className={`flex items-center space-x-2 px-4 py-2 border-b-2 transition-colors ${
                    activeView === 'git' 
                      ? 'border-blue-500 text-blue-600' 
                      : 'border-transparent text-gray-500 hover:text-gray-700'
                  }`}
                >
                  <Github className="w-4 h-4" />
                  <span>Git Search</span>
                </button>
              </div>
              
              {/* Content based on selected view */}
              {activeView === 'code' && (
                <CodeView 
                  fragments={selectedNode.fragments} 
                  highlightedLine={highlightedLine}
                />
              )}
              
              {activeView === 'dataflow' && (
                <DataFlowView 
                  dataFlows={selectedNode.dataFlows}
                  codeFragments={selectedNode.fragments}
                  onVariableClick={handleVariableClick}
                />
              )}
              
              {activeView === 'git' && (
                <GitSearchView projectName={projectName} />
              )}
            </div>
          ) : (
            <div className="flex items-center justify-center h-full text-gray-500">
              Select a function from the tree to view its details
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default EnhancedCodeAnalysisTab;