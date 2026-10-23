import React, { useState } from 'react';
import { ChevronRight, ChevronDown, Code, Folder, FileCode } from 'lucide-react';

interface TreeNode {
  id: string;
  type: 'folder' | 'file' | 'function';
  name: string;
  children?: TreeNode[];
  path: string;
}

interface TreeViewProps {
  treeData: TreeNode[];
  selectedPath: string | null;
  onSelect: (node: TreeNode) => void;
}

const TreeNodeComponent = ({ 
  node, 
  onSelect, 
  selectedPath,
  level = 0 
}: { 
  node: TreeNode;
  onSelect: (node: TreeNode) => void;
  selectedPath: string | null;
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

const TreeView: React.FC<TreeViewProps> = ({
  treeData,
  selectedPath,
  onSelect
}) => {
  return (
    <div className="overflow-y-auto h-full">
      {treeData.map(node => (
        <TreeNodeComponent
          key={node.id}
          node={node}
          onSelect={onSelect}
          selectedPath={selectedPath}
          level={0}
        />
      ))}
    </div>
  );
};

export default TreeView;