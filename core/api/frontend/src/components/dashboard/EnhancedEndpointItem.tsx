import React from 'react';
import EndpointItem from './EndpointItem';

interface EnhancedEndpointItemProps {
  endpoint: any;
  isSelected: boolean;
  onSelect: () => void;
  onRemove: (id: string) => void;
}

const EnhancedEndpointItem: React.FC<EnhancedEndpointItemProps> = ({
  endpoint,
  isSelected,
  onSelect,
  onRemove
}) => {
  const handleRemove = (e: React.MouseEvent) => {
    e.stopPropagation();
    onRemove(endpoint.id);
  };

  return (
    <div className="relative group">
      <div className="mb-2 font-mono text-sm text-gray-600">
        <span className="font-bold">{`X-${endpoint.id}`}</span>
      </div>
      <EndpointItem
        endpoint={endpoint}
        isSelected={isSelected}
        onSelect={onSelect}
      />
      <button
        onClick={handleRemove}
        className="absolute top-2 right-2 p-1 rounded-full bg-gray-100 opacity-0 
          group-hover:opacity-100 transition-opacity hover:bg-gray-200"
      >
        <X className="h-4 w-4 text-gray-500" />
      </button>
    </div>
  );
};

export default EnhancedEndpointItem;