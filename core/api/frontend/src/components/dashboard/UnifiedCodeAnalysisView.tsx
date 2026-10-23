import React, { useState, useEffect } from 'react';
import { Code, GitBranchPlus } from 'lucide-react';
import DataFlowView from './DataFlowView';
import CodeView from './CodeView';
import TreeView from './TreeView';

interface TreeNode {
  id: string;
  type: 'folder' | 'file' | 'function';
  name: string;
  children?: TreeNode[];
  fragments?: {
    code: string[];
    startLine: number;
    endLine: number;
  }[];
  dataFlows?: Array<{
    variables: Record<string, any>;
    timestamp: string;
  }>;
  path: string;
}

interface UnifiedCodeAnalysisViewProps {
  codeFragments: Array<{
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
  }>;
  dataFlowEntries: Array<{
    functionName: string;
    dataFlows: Array<{
      variables: Record<string, any>;
      timestamp: string;
    }>;
  }>;
}

const UnifiedCodeAnalysisView: React.FC<UnifiedCodeAnalysisViewProps> = ({ 
  codeFragments,
  dataFlowEntries
}) => {
  const [treeData, setTreeData] = useState<TreeNode[]>([]);
  const [selectedNode, setSelectedNode] = useState<TreeNode | null>(null);
  const [activeView, setActiveView] = useState<'code' | 'dataflow'>('code');
  const [highlightedLine, setHighlightedLine] = useState<number | null>(null);

  useEffect(() => {
    const buildTree = () => {
      const tree: Record<string, TreeNode> = {};
      
      // Process code fragments
      codeFragments.forEach(fragment => {
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
              tree[currentPath].children?.push(tree[newPath]);
            }
          }
          
          currentPath = newPath;
        });

        // Add function node
        const functionPath = `${currentPath}.${fragment.location.object}`;
        if (!tree[functionPath]) {
          const functionNode: TreeNode = {
            id: functionPath,
            name: `${fragment.location.object}()`,
            type: 'function',
            path: functionPath,
            fragments: [],
            dataFlows: []
          };
          
          tree[currentPath].children?.push(functionNode);
          tree[functionPath] = functionNode;
        }
        
        // Add code fragments
        if (tree[functionPath].fragments) {
          tree[functionPath].fragments?.push({
            code: fragment.code,
            startLine: fragment.startLine,
            endLine: fragment.endLine
          });
        }
      });

      // Add data flow information
      dataFlowEntries.forEach(entry => {
        const functionPath = entry.functionName;
        if (tree[functionPath] && entry.dataFlows) {
          tree[functionPath].dataFlows = entry.dataFlows;
        }
      });

      // Return only root nodes (those without dots in path)
      return Object.values(tree).filter(node => !node.path.includes('.'));
    };

    // Build tree and set state
    const builtTree = buildTree();
    setTreeData(builtTree);
    console.log('Built tree:', builtTree); // Debug log
  }, [codeFragments, dataFlowEntries]);

  const handleNodeSelect = (node: TreeNode) => {
    setSelectedNode(node);
    setHighlightedLine(null);
  };

  const handleVariableClick = (lineNumber: number) => {
    setActiveView('code');
    setHighlightedLine(lineNumber);
  };

  console.log('Current selected node:', selectedNode); // Debug log

  return (
    <div className="flex h-full">
      <div className="w-1/3 border-r overflow-y-auto">
        <TreeView
          treeData={treeData}
          selectedPath={selectedNode?.path || null}
          onSelect={handleNodeSelect}
        />
      </div>
      <div className="flex-1 overflow-y-auto">
        {selectedNode?.type === 'function' && (
          <div className="p-4">
            <div className="flex gap-2 mb-4">
              <button
                onClick={() => setActiveView('code')}
                className={`flex items-center space-x-2 px-3 py-1.5 rounded ${
                  activeView === 'code' 
                    ? 'bg-blue-500 text-white' 
                    : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                }`}
              >
                <Code className="w-4 h-4" />
                <span>Code</span>
              </button>
              <button
                onClick={() => setActiveView('dataflow')}
                className={`flex items-center space-x-2 px-3 py-1.5 rounded ${
                  activeView === 'dataflow' 
                    ? 'bg-blue-500 text-white' 
                    : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                }`}
              >
                <GitBranchPlus className="w-4 h-4" />
                <span>Data Flow</span>
              </button>
            </div>
            {activeView === 'code' ? (
              <CodeView 
                fragments={selectedNode.fragments}
                highlightedLine={highlightedLine}
              />
            ) : (
              <DataFlowView
                dataFlows={selectedNode.dataFlows}
                codeFragments={selectedNode.fragments || []}
                onVariableClick={handleVariableClick}
              />
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default UnifiedCodeAnalysisView;