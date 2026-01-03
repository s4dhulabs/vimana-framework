import React, { useState } from 'react';
import { CodeBlock } from './CodeBlock';
import { TestMetrics } from './TestMetrics';
import { CopyToClipboard } from 'react-copy-to-clipboard';
import { motion } from 'framer-motion';
import { sanitizeDisplay } from '../../utils/security';

export const TestDetails = ({ test }) => {
  const [showHeaders, setShowHeaders] = useState(false);
  
  const renderTestValue = (value) => {
    if (sanitizeDisplay.isPayload(value)) {
      return (
        <div className="payload-warning bg-yellow-50 p-2 rounded">
          <div className="text-yellow-800 text-sm mb-1">⚠️ Security Test Payload</div>
          <pre className="text-xs bg-gray-100 p-2 rounded overflow-x-auto">
            {sanitizeDisplay.formatPayload(value)}
          </pre>
        </div>
      );
    }
    
    return (
      <CodeBlock
        code={value}
        language="json"
        title="Test Value"
      />
    );
  };

  return (
    <motion.div 
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="test-details p-4 bg-white rounded-lg shadow"
    >
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-xl font-semibold">{test.name}</h3>
        <TestMetrics 
          executionTime={test.executionTime}
          memoryUsage={test.memoryUsage}
          complexity={test.complexity}
        />
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div className="request-section">
          <div className="flex justify-between items-center mb-2">
            <h4 className="font-medium">Request</h4>
            <CopyToClipboard text={JSON.stringify(test.request, null, 2)}>
              <button className="text-blue-500 hover:text-blue-700">
                Copy Request
              </button>
            </CopyToClipboard>
          </div>
          
          <button 
            onClick={() => setShowHeaders(!showHeaders)}
            className="text-sm text-gray-500 mb-2"
          >
            {showHeaders ? 'Hide Headers' : 'Show Headers'}
          </button>
          
          {showHeaders && (
            <CodeBlock
              code={JSON.stringify(test.request.headers, null, 2)}
              language="json"
              title="Headers"
            />
          )}
          
          <CodeBlock
            code={JSON.stringify(test.request.body, null, 2)}
            language="json"
            title="Body"
          />
        </div>

        <div className="response-section">
          <div className="flex justify-between items-center mb-2">
            <h4 className="font-medium">Response</h4>
            <CopyToClipboard text={JSON.stringify(test.response, null, 2)}>
              <button className="text-blue-500 hover:text-blue-700">
                Copy Response
              </button>
            </CopyToClipboard>
          </div>
          
          <div className="status-code mb-2">
            Status: <span className={`font-medium ${test.response.status < 400 ? 'text-green-600' : 'text-red-600'}`}>
              {test.response.status}
            </span>
          </div>
          
          <CodeBlock
            code={JSON.stringify(test.response.body, null, 2)}
            language="json"
            title="Body"
          />
        </div>
      </div>

      <div className="test-value mt-4">
        {renderTestValue(test.value)}
      </div>
    </motion.div>
  );
}; 