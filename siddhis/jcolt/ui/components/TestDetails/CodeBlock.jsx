import React from 'react';
import { Light as SyntaxHighlighter } from 'react-syntax-highlighter';

export const CodeBlock = ({ code, language, title }) => {
  const decodeSanitizedContent = (content) => {
    try {
      // Handle hex-encoded content
      if (typeof content === 'string' && content.includes('\\x')) {
        return content.replace(/\\x([0-9a-fA-F]{2})/g, 
          (_, hex) => String.fromCharCode(parseInt(hex, 16)));
      }
      return content;
    } catch (error) {
      console.error('Error decoding content:', error);
      return content;
    }
  };

  const renderContent = () => {
    const decodedContent = decodeSanitizedContent(code);
    return (
      <SyntaxHighlighter
        language={language}
        className="rounded p-4 text-sm"
        useInlineStyles={false}
      >
        {decodedContent}
      </SyntaxHighlighter>
    );
  };

  return (
    <div className="code-block">
      {title && <div className="code-title text-sm text-gray-500 mb-1">{title}</div>}
      <div className="relative">
        {renderContent()}
      </div>
    </div>
  );
}; 