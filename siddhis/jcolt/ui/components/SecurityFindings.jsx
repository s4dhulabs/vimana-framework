import React from 'react';
import { OWASP_2023_REFERENCES } from '../utils/owaspReferences';

export const SecurityFindings = ({ findings }) => {
  return (
    <div className="security-findings">
      <h3 className="text-xl font-semibold mb-4">Security Findings</h3>
      {findings.map((finding, index) => (
        <div key={index} className="finding-card mb-4 p-4 border rounded-lg shadow-sm">
          <div className="flex items-center justify-between">
            <h4 className="text-lg font-medium">{finding.title}</h4>
            <span className={`px-3 py-1 rounded-full ${finding.severity === 'HIGH' ? 'bg-red-100 text-red-800' : 
              finding.severity === 'MEDIUM' ? 'bg-yellow-100 text-yellow-800' : 'bg-blue-100 text-blue-800'}`}>
              {finding.severity}
            </span>
          </div>
          
          <div className="mt-2">
            <p className="text-gray-600">{finding.description}</p>
            
            {finding.owaspReferences.map((ref, i) => {
              const owaspRef = OWASP_2023_REFERENCES[ref];
              return (
                <div key={i} className="mt-2 p-2 bg-gray-50 rounded">
                  <a 
                    href={owaspRef.link}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-blue-600 hover:text-blue-800"
                  >
                    {owaspRef.id} - {owaspRef.title}
                  </a>
                  <p className="text-sm text-gray-500 mt-1">{owaspRef.description}</p>
                </div>
              );
            })}
          </div>
          
          {finding.remediation && (
            <div className="mt-3">
              <h5 className="font-medium">Remediation</h5>
              <p className="text-gray-600">{finding.remediation}</p>
            </div>
          )}
        </div>
      ))}
    </div>
  );
}; 