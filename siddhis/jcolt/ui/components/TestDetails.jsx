import React from 'react';
import { SyntaxHighlighter } from 'react-syntax-highlighter';
import { CopyToClipboard } from 'react-copy-to-clipboard';

export const TestDetails = ({ test }) => {
  return (
    <div className="test-details">
      <div className="test-header">
        <h3>{test.name}</h3>
        <span className="test-timing">{test.executionTime}ms</span>
      </div>
      
      <div className="test-content">
        <div className="test-request">
          <h4>Request</h4>
          <CopyToClipboard text={test.value}>
            <button>Copy</button>
          </CopyToClipboard>
          <SyntaxHighlighter language="json">
            {test.value}
          </SyntaxHighlighter>
        </div>
        
        <div className="test-response">
          <h4>Response</h4>
          <CopyToClipboard text={test.response_body}>
            <button>Copy</button>
          </CopyToClipboard>
          <SyntaxHighlighter language="json">
            {test.response_body}
          </SyntaxHighlighter>
        </div>
      </div>
    </div>
  );
}; 