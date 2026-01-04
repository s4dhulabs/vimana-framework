import React, { useState } from 'react';
import { JsonViewer } from './JsonViewer';
import { TestDebugger } from './TestDebugger';
import { Documentation } from './Documentation';

export const DevTools = ({ test }) => {
  const [activeTab, setActiveTab] = useState('data');

  return (
    <div className="dev-tools border rounded-lg shadow-lg">
      <div className="tabs flex border-b">
        <button
          className={`px-4 py-2 ${activeTab === 'data' ? 'bg-blue-50 border-b-2 border-blue-500' : ''}`}
          onClick={() => setActiveTab('data')}
        >
          Test Data
        </button>
        <button
          className={`px-4 py-2 ${activeTab === 'debug' ? 'bg-blue-50 border-b-2 border-blue-500' : ''}`}
          onClick={() => setActiveTab('debug')}
        >
          Debugger
        </button>
        <button
          className={`px-4 py-2 ${activeTab === 'docs' ? 'bg-blue-50 border-b-2 border-blue-500' : ''}`}
          onClick={() => setActiveTab('docs')}
        >
          Documentation
        </button>
      </div>

      <div className="content p-4">
        {activeTab === 'data' && <JsonViewer data={test} />}
        {activeTab === 'debug' && <TestDebugger test={test} />}
        {activeTab === 'docs' && <Documentation testType={test.type} />}
      </div>
    </div>
  );
}; 