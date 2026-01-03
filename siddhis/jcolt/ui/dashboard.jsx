import React, { useState, useEffect } from 'react';

const JColtDashboard = ({ pydanticData, fuzzingData }) => {
  const [activeTab, setActiveTab] = useState('pydantic');
  const [selectedModel, setSelectedModel] = useState(null);
  const [selectedField, setSelectedField] = useState(null);
  const [selectedTest, setSelectedTest] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterPassed, setFilterPassed] = useState(null); // null: all, true: passed, false: failed
  const [exportFormat, setExportFormat] = useState('json');
  const [showExportOptions, setShowExportOptions] = useState(false);
    
  // Enhanced sanitization function with extra XSS protection
  const sanitizeOutput = (value) => {
    if (value === null || value === undefined) return "";
    
    // Handle objects safely
    if (typeof value === "object") {
      try {
        return JSON.stringify(value, null, 2)
          .replace(/&/g, "&amp;")
          .replace(/</g, "&lt;")
          .replace(/>/g, "&gt;")
          .replace(/"/g, "&quot;")
          .replace(/'/g, "&#039;");
      } catch (e) {
        return "[Complex Object]";
      }
    }
    
    // Convert to string and escape HTML entities
    // Double-escape potentially malicious content
    const escapedStr = String(value)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
      
    // Additional protection for script-like content
    return escapedStr
      .replace(/javascript:/gi, "blocked-javascript:")
      .replace(/data:/gi, "blocked-data:")
      .replace(/on\w+=/gi, "blocked-event=");
  };
  
  // Calculate model stats
  const getModelStats = (modelName, modelData) => {
    let totalTests = 0;
    let passedTests = 0;
    
    Object.entries(modelData.fields || {}).forEach(([fieldName, fieldData]) => {
      // Handle both array of tests or object with tests property
      const fieldTests = Array.isArray(fieldData) ? fieldData : (fieldData.tests || []);
      
      fieldTests.forEach(test => {
        totalTests++;
        if (test.pass) passedTests++;
      });
    });
    
    return {
      totalTests,
      passedTests,
      failedTests: totalTests - passedTests,
      passRate: totalTests > 0 ? Math.round((passedTests / totalTests) * 100) : 0
    };
  };
  
  // Render test table
  const renderTestTable = (tests) => {
    // Apply filters
    const filteredTests = tests.filter(test => {
      // Filter by search term
      if (searchTerm && !String(test.name).toLowerCase().includes(searchTerm.toLowerCase())) {
        return false;
      }
      
      // Filter by passed/failed status
      if (filterPassed !== null && test.pass !== filterPassed) {
        return false;
      }
      
      return true;
    });
    
    if (filteredTests.length === 0) {
      return (
        <div className="p-4 text-center text-gray-500">
          No tests match your filters.
        </div>
      );
    }
    
    return (
      <div className="overflow-x-auto">
        <table className="w-full border-collapse">
          <thead className="bg-gray-100">
            <tr>
              <th className="px-4 py-2 text-left border">Test</th>
              <th className="px-4 py-2 text-left border">Type</th>
              <th className="px-4 py-2 text-left border">Result</th>
              <th className="px-4 py-2 text-left border">Expected</th>
              <th className="px-4 py-2 text-left border">Actual</th>
              <th className="px-4 py-2 text-left border">Status</th>
            </tr>
          </thead>
          <tbody>
            {filteredTests.map((test, index) => (
              <tr 
                key={index} 
                className={`${test.pass ? "bg-green-50" : "bg-red-50"} hover:bg-gray-100 cursor-pointer`}
                onClick={() => setSelectedTest(selectedTest === index ? null : index)}
              >
                <td className="px-4 py-2 border" title={sanitizeOutput(test.name)}>
                  <div className="max-w-xs truncate">{sanitizeOutput(test.name)}</div>
                </td>
                <td className="px-4 py-2 border">{sanitizeOutput(test.test_type)}</td>
                <td className="px-4 py-2 border">
                  {test.pass ? 
                    <span className="text-green-500">✓</span> : 
                    <span className="text-red-500">✗</span>
                  }
                </td>
                <td className="px-4 py-2 border">
                  <div className="max-w-xs truncate">{sanitizeOutput(test.expected_result)}</div>
                </td>
                <td className="px-4 py-2 border">
                  <div className="max-w-xs truncate">{sanitizeOutput(test.actual_result)}</div>
                </td>
                <td className="px-4 py-2 border">{sanitizeOutput(test.status_code)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    );
  };
  
  // Render test details
  const renderTestDetails = (test) => {
    if (!test) return null;
    
    return (
      <div className="mt-4 p-4 bg-gray-50 rounded-md">
        <h4 className="text-lg font-semibold mb-2">{sanitizeOutput(test.name)}</h4>
        <p className="text-gray-700 mb-2">{sanitizeOutput(test.description)}</p>
        
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 mt-4">
          <div>
            <h5 className="font-semibold mb-1">Test Value:</h5>
            <pre className="bg-gray-100 p-2 rounded text-xs overflow-x-auto whitespace-pre-wrap">
              {sanitizeOutput(test.value)}
            </pre>
          </div>
          
          <div>
            <h5 className="font-semibold mb-1">Response:</h5>
            <pre className="bg-gray-100 p-2 rounded text-xs overflow-x-auto whitespace-pre-wrap">
              {sanitizeOutput(test.response_body)}
            </pre>
          </div>
        </div>
      </div>
    );
  };
  
  // Render model card
  const renderModelCard = (modelName, modelData) => {
    const stats = getModelStats(modelName, modelData);
    const isSelected = selectedModel === modelName;
    
    // Apply search filter to model name
    if (searchTerm && !modelName.toLowerCase().includes(searchTerm.toLowerCase())) {
      return null;
    }
    
    return (
      <div key={modelName} className="border rounded-lg mb-4 shadow-sm">
        <div className="p-4 border-b">
          <div className="flex justify-between">
            <h3 className="text-lg font-semibold">{modelName}</h3>
            <span className="text-sm font-normal text-gray-500">
              {(modelData.method || "").toUpperCase()} {modelData.path || ""}
            </span>
          </div>
          <p className="text-sm text-gray-500">{modelData.operation_id || ""}</p>
        </div>
        
        <div className="p-4">
          <div className="flex flex-wrap justify-between text-sm mb-2">
            <div className="mb-1">
              <span className="font-semibold">Total Tests:</span> {stats.totalTests}
            </div>
            <div className="mb-1">
              <span className="font-semibold text-green-600">Passed:</span> {stats.passedTests}
            </div>
            <div className="mb-1">
              <span className="font-semibold text-red-600">Failed:</span> {stats.failedTests}
            </div>
            <div className="mb-1">
              <span className="font-semibold">Pass Rate:</span> {stats.passRate}%
            </div>
          </div>
          
          <div className="w-full bg-gray-200 rounded-full h-2 mb-4">
            <div 
              className={`rounded-full h-2 ${stats.passRate > 80 ? 'bg-green-500' : stats.passRate > 50 ? 'bg-yellow-500' : 'bg-red-500'}`}
              style={{ width: `${stats.passRate}%` }}
            />
          </div>
          
          {isSelected && (
            <div>
              <h4 className="font-semibold mb-2">Fields:</h4>
              <div className="space-y-4">
                {Object.entries(modelData.fields || {}).map(([fieldName, fieldData]) => {
                  // Handle both array of tests or object with tests property
                  const fieldTests = Array.isArray(fieldData) ? fieldData : (fieldData.tests || []);
                  
                  // Skip fields that don't match search term
                  if (searchTerm && !fieldName.toLowerCase().includes(searchTerm.toLowerCase())) {
                    return null;
                  }
                  
                  // Skip fields that don't match pass/fail filter
                  if (filterPassed !== null) {
                    const passedTests = fieldTests.filter(t => t.pass).length;
                    const failedTests = fieldTests.length - passedTests;
                    
                    if (filterPassed && failedTests > 0) {
                      return null;
                    }
                    
                    if (!filterPassed && failedTests === 0) {
                      return null;
                    }
                  }
                  
                  const passedFieldTests = fieldTests.filter(t => t.pass).length;
                  const isFieldSelected = selectedField === fieldName;
                  
                  return (
                    <div key={fieldName} className="border rounded-md p-3">
                      <div 
                        className="flex justify-between items-center cursor-pointer"
                        onClick={() => setSelectedField(isFieldSelected ? null : fieldName)}
                      >
                        <h5 className="font-medium">{fieldName}</h5>
                        <div className="text-sm">
                          <span className="text-green-600">{passedFieldTests}</span>
                          <span className="text-gray-400">/</span>
                          <span>{fieldTests.length}</span>
                          <span className="ml-2">
                            {isFieldSelected ? '▼' : '▶'}
                          </span>
                        </div>
                      </div>
                      
                      {isFieldSelected && (
                        <div className="mt-3">
                          {renderTestTable(fieldTests)}
                          {selectedTest !== null && selectedTest < fieldTests.length && 
                            renderTestDetails(fieldTests[selectedTest])
                          }
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </div>
        
        <div className="p-4 border-t bg-gray-50">
          <button 
            className={`w-full py-2 px-4 rounded-md ${isSelected ? "bg-gray-200 text-gray-800" : "bg-gray-100 text-gray-700 hover:bg-gray-200"}`}
            onClick={() => {
              setSelectedModel(isSelected ? null : modelName);
              setSelectedField(null);
              setSelectedTest(null);
            }}
          >
            {isSelected ? "Hide Details" : "Show Details"}
          </button>
        </div>
      </div>
    );
  };
  
  // Render fuzzing data
  const renderFuzzingData = () => {
    if (!fuzzingData || Object.keys(fuzzingData).length === 0) {
      return (
        <div className="p-8 text-center bg-gray-50 rounded-lg">
          <h3 className="text-lg font-semibold mb-2">No Fuzzing Data Available</h3>
          <p className="text-gray-600">Run fuzzing tests to see results here.</p>
        </div>
      );
    }
    
    return (
      <div>
        <h3 className="text-lg font-semibold mb-4">Fuzzing Results</h3>
        
        {Object.entries(fuzzingData).map(([path, requests]) => (
          <div key={path} className="border rounded-lg mb-4 shadow-sm">
            <div className="p-4 border-b">
              <h3 className="text-lg font-semibold">{path}</h3>
              <p className="text-sm text-gray-500">{requests.length} requests</p>
            </div>
            
            <div className="p-4">
              <div className="overflow-x-auto">
                <table className="w-full border-collapse">
                  <thead className="bg-gray-100">
                    <tr>
                      <th className="px-4 py-2 text-left border">Method</th>
                      <th className="px-4 py-2 text-left border">Status</th>
                      <th className="px-4 py-2 text-left border">Response Time</th>
                      <th className="px-4 py-2 text-left border">Size</th>
                    </tr>
                  </thead>
                  <tbody>
                    {requests.map((req, index) => (
                      <tr key={index} className={req.response && req.response.status < 400 ? "bg-green-50" : "bg-red-50"}>
                        <td className="px-4 py-2 border">{req.method}</td>
                        <td className="px-4 py-2 border">{req.response ? req.response.status : 'N/A'}</td>
                        <td className="px-4 py-2 border">{req.response_time ? req.response_time.toFixed(3) + 's' : 'N/A'}</td>
                        <td className="px-4 py-2 border">{req.response_size || 'N/A'} bytes</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        ))}
      </div>
    );
  };
  
  // Calculate overall stats
  const calculateOverallStats = () => {
    let totalTests = 0;
    let passedTests = 0;
    
    Object.values(pydanticData || {}).forEach(modelData => {
      Object.values(modelData.fields || {}).forEach(fieldData => {
        // Handle both array of tests or object with tests property
        const fieldTests = Array.isArray(fieldData) ? fieldData : (fieldData.tests || []);
        
        fieldTests.forEach(test => {
          totalTests++;
          if (test.pass) passedTests++;
        });
      });
    });
    
    return {
      totalTests,
      passedTests,
      failedTests: totalTests - passedTests,
      passRate: totalTests > 0 ? Math.round((passedTests / totalTests) * 100) : 0
    };
  };
  
  const overallStats = calculateOverallStats();
  
  return (
    <div className="container mx-auto p-4">
      <div className="flex flex-col md:flex-row justify-between items-center mb-6">
        <h1 className="text-2xl font-bold mb-2 md:mb-0">JColt Testing Dashboard</h1>
        
        <div className="flex items-center space-x-2">
          <button 
            className="py-2 px-4 bg-blue-500 text-white rounded-md flex items-center hover:bg-blue-600"
            onClick={() => setShowExportOptions(!showExportOptions)}
          >
            <span className="mr-2">⬇️</span>
            Export Results
          </button>
          
          {showExportOptions && (
            <div className="flex space-x-2">
              <button 
                className="py-2 px-3 bg-gray-100 text-gray-800 rounded-md flex items-center hover:bg-gray-200"
                onClick={() => {
                  const dataStr = JSON.stringify(
                    activeTab === 'pydantic' ? pydanticData : fuzzingData, 
                    null, 
                    2
                  );
                  const dataUri = `data:application/json;charset=utf-8,${encodeURIComponent(dataStr)}`;
                  const linkElement = document.createElement('a');
                  linkElement.setAttribute('href', dataUri);
                  linkElement.setAttribute('download', `jcolt_${activeTab}_results.json`);
                  linkElement.click();
                }}
              >
                JSON
              </button>
              
              <button 
                className="py-2 px-3 bg-gray-100 text-gray-800 rounded-md flex items-center hover:bg-gray-200"
                onClick={() => {
                  alert("HTML export functionality is handled server-side. Use the export button in the JColt CLI.");
                }}
              >
                HTML
              </button>
              
              <button 
                className="py-2 px-3 bg-gray-100 text-gray-800 rounded-md flex items-center hover:bg-gray-200"
                onClick={() => {
                  alert("CSV export functionality is handled server-side. Use the export button in the JColt CLI.");
                }}
              >
                CSV
              </button>
            </div>
          )}
        </div>
      </div>
      
      <div className="mb-6 p-4 bg-gray-50 rounded-lg shadow-sm">
        <h2 className="text-lg font-semibold mb-2">Summary</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="p-3 bg-white rounded shadow-sm">
            <div className="text-sm text-gray-500">Total Tests</div>
            <div className="text-2xl font-bold">{overallStats.totalTests}</div>
          </div>
          <div className="p-3 bg-white rounded shadow-sm">
            <div className="text-sm text-gray-500">Passed</div>
            <div className="text-2xl font-bold text-green-600">{overallStats.passedTests}</div>
          </div>
          <div className="p-3 bg-white rounded shadow-sm">
            <div className="text-sm text-gray-500">Failed</div>
            <div className="text-2xl font-bold text-red-600">{overallStats.failedTests}</div>
          </div>
          <div className="p-3 bg-white rounded shadow-sm">
            <div className="text-sm text-gray-500">Pass Rate</div>
            <div className="text-2xl font-bold">{overallStats.passRate}%</div>
          </div>
        </div>
        <div className="mt-4 w-full bg-gray-200 rounded-full h-3">
          <div 
            className={`rounded-full h-3 ${overallStats.passRate > 80 ? 'bg-green-500' : overallStats.passRate > 50 ? 'bg-yellow-500' : 'bg-red-500'}`}
            style={{ width: `${overallStats.passRate}%` }}
          />
        </div>
      </div>
      
      <div className="mb-6">
        <div className="border-b">
          <div className="flex">
            <button 
              className={`px-4 py-2 ${activeTab === 'pydantic' ? 'border-b-2 border-blue-500 -mb-px' : 'text-gray-500'}`}
              onClick={() => setActiveTab('pydantic')}
            >
              Pydantic Model Tests
            </button>
            <button 
              className={`px-4 py-2 ${activeTab === 'fuzzing' ? 'border-b-2 border-blue-500 -mb-px' : 'text-gray-500'}`}
              onClick={() => setActiveTab('fuzzing')}
            >
              Fuzzing Tests
            </button>
          </div>
        </div>
      </div>
      
      <div className="mb-4">
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center">
          <div className="flex flex-col md:flex-row items-start md:items-center space-y-2 md:space-y-0 md:space-x-2 mb-3 md:mb-0">
            <input
              type="text"
              placeholder="Search models and fields..."
              className="px-3 py-2 border rounded w-full md:w-64"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
            <div className="flex space-x-1">
              <button
                className={`px-3 py-2 rounded ${filterPassed === null ? 'bg-blue-500 text-white' : 'bg-gray-200'}`}
                onClick={() => setFilterPassed(null)}
              >
                All
              </button>
              <button
                className={`px-3 py-2 rounded ${filterPassed === true ? 'bg-green-500 text-white' : 'bg-gray-200'}`}
                onClick={() => setFilterPassed(true)}
              >
                Passed
              </button>
              <button
                className={`px-3 py-2 rounded ${filterPassed === false ? 'bg-red-500 text-white' : 'bg-gray-200'}`}
                onClick={() => setFilterPassed(false)}
              >
                Failed
              </button>
            </div>
          </div>
          
          {activeTab === 'pydantic' && (
            <div className="flex items-center bg-yellow-50 text-yellow-800 px-3 py-1 rounded-md text-sm">
              <span className="mr-2">⚠️</span>
              <span>Schema-based validation test results</span>
            </div>
          )}
        </div>
      </div>
      
      {activeTab === 'pydantic' && (
        <div>
          <div className="mb-4">
            <h2 className="text-xl font-semibold">Pydantic Model Test Results</h2>
            <p className="text-gray-600 mt-1">
              Testing results for Pydantic models extracted from the API schema
            </p>
          </div>
          
          <div className="space-y-4">
            {pydanticData && Object.entries(pydanticData).map(([modelName, modelData]) => 
              renderModelCard(modelName, modelData)
            )}
            
            {(!pydanticData || Object.keys(pydanticData).length === 0) && (
              <div className="p-8 text-center bg-gray-50 rounded-lg">
                <h3 className="text-lg font-semibold mb-2">No Pydantic Test Data Available</h3>
                <p className="text-gray-600">Run Pydantic tests to see results here.</p>
              </div>
            )}
          </div>
        </div>
      )}
      
      {activeTab === 'fuzzing' && renderFuzzingData()}
      
      <div className="mt-8 pt-4 border-t text-center text-gray-500 text-sm">
        Generated by JColt - {new Date().toLocaleString()}
      </div>
    </div>
  );
};

export default JColtDashboard;