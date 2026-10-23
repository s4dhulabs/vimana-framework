import React, { useState, useEffect } from 'react';
import { ChevronRight, ChevronDown, Code, Folder, FileCode } from 'lucide-react';

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
  path: string;
}

const TreeNodeComponent = ({ 
  node, 
  onSelect, 
  selectedPath,
  level = 0 
}: { 
  node: TreeNode;
  onSelect: (node: TreeNode) => void;
  selectedPath: string;
  level?: number;
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

  return (
    <div>
      <div
        className={`flex items-center py-1 px-2 cursor-pointer hover:bg-gray-100 ${
          selectedPath === node.path ? 'bg-blue-50' : ''
        }`}
        style={{ paddingLeft: `${indent}px` }}
        onClick={() => {
          if (node.children?.length) {
            setIsExpanded(!isExpanded);
          }
          onSelect(node);
        }}
      >
        {node.children && node.children.length > 0 && (
          <div className="p-1 hover:bg-gray-200 rounded">
            {isExpanded ? (
              <ChevronDown className="w-4 h-4" />
            ) : (
              <ChevronRight className="w-4 h-4" />
            )}
          </div>
        )}
        {!node.children && <div className="w-6" />}
        {getIcon()}
        <span className="ml-2 font-mono text-sm">{node.name}</span>
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

const CodeView = ({ fragments }: { fragments?: { code: string[]; startLine: number; endLine: number; }[] }) => {
  if (!fragments || fragments.length === 0) {
    return (
      <div className="p-4 text-gray-500 text-center">
        Select a function to view its code
      </div>
    );
  }

  return (
    <div className="bg-gray-900 p-4 rounded-lg">
      <pre className="text-white font-mono text-sm">
        <code>
          {fragments.map((fragment, fragmentIndex) => (
            <React.Fragment key={fragmentIndex}>
              {fragment.code.map((line, lineIndex) => (
                <div key={`${fragmentIndex}-${lineIndex}`} className="group hover:bg-gray-800">
                  {line}
                </div>
              ))}
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

const HierarchicalCodeView = ({ 
  codeFragments 
}: { 
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
}) => {
  const [treeData, setTreeData] = useState<TreeNode[]>([]);
  const [selectedNode, setSelectedNode] = useState<TreeNode | null>(null);

  useEffect(() => {
    const buildTree = () => {
      const tree: Record<string, TreeNode> = {};
      
      codeFragments.forEach(fragment => {
        const parts = fragment.location.shortpath.split('.');
        let currentPath = '';
        
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
            fragments: []
          };
          
          tree[currentPath].children?.push(functionNode);
          tree[functionPath] = functionNode;
        }
        
        if (tree[functionPath].fragments) {
          tree[functionPath].fragments?.push({
            code: fragment.code,
            startLine: fragment.startLine,
            endLine: fragment.endLine
          });
        }
      });

      return Object.values(tree).filter(node => !node.path.includes('.'));
    };

    setTreeData(buildTree());
  }, [codeFragments]);

  const handleNodeSelect = (node: TreeNode) => {
    setSelectedNode(node);
  };

  return (
    <div className="flex h-full">
      <div className="w-1/3 border-r overflow-y-auto">
        {treeData.map(node => (
          <TreeNodeComponent
            key={node.id}
            node={node}
            onSelect={handleNodeSelect}
            selectedPath={selectedNode?.path || ''}
          />
        ))}
      </div>
      <div className="flex-1 p-4 overflow-y-auto">
        <CodeView fragments={selectedNode?.fragments} />
      </div>
    </div>
  );
};

export default HierarchicalCodeView;