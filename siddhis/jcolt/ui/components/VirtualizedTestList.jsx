import React from 'react';
import { FixedSizeList } from 'react-window';
import AutoSizer from 'react-virtualized-auto-sizer';

export const VirtualizedTestList = ({ tests }) => {
  const Row = ({ index, style }) => {
    const test = tests[index];
    return (
      <div style={style} className="test-row p-4 border-b">
        <h3 className="font-medium">{test.name}</h3>
        <p className="text-gray-600">{test.description}</p>
      </div>
    );
  };

  return (
    <div className="h-[500px]">
      <AutoSizer>
        {({ height, width }) => (
          <FixedSizeList
            height={height}
            width={width}
            itemCount={tests.length}
            itemSize={100}
          >
            {Row}
          </FixedSizeList>
        )}
      </AutoSizer>
    </div>
  );
}; 