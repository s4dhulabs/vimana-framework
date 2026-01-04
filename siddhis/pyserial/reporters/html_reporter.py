import os
import json
from datetime import datetime
import webbrowser
import html
import base64

class HTMLReporter:
    """Generate HTML reports with embedded React dashboard for PySerial results"""
    
    def __init__(self, results_data, output_dir=None):
        self.results_data = results_data
        self.output_dir = output_dir or os.getcwd()
    
    def _sanitize_data_for_embedding(self, data):
        """
        Safely prepare data for embedding in HTML
        Uses Base64 encoding to prevent XSS issues completely
        """
        if not data:
            return "null"
            
        # Convert to JSON string
        json_str = json.dumps(data)
        
        # Base64 encode to avoid any possible XSS issues
        # This is a safer approach than trying to escape HTML 
        encoded = base64.b64encode(json_str.encode('utf-8')).decode('utf-8')
        
        return encoded
        
    def generate_report(self):
        """Generate HTML report with embedded React dashboard"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"pyserial_report_{timestamp}.html"
        filepath = os.path.join(self.output_dir, filename)
        
        # Process data for safe embedding (Base64 encode)
        encoded_data = self._sanitize_data_for_embedding(self.results_data)
        
        # Create HTML template with safety mechanisms in place
        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>PySerial Test Results</title>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <!-- Include React -->
            <script src="https://cdnjs.cloudflare.com/ajax/libs/react/17.0.2/umd/react.production.min.js"></script>
            <script src="https://cdnjs.cloudflare.com/ajax/libs/react-dom/17.0.2/umd/react-dom.production.min.js"></script>
            <script src="https://cdnjs.cloudflare.com/ajax/libs/babel-standalone/7.18.13/babel.min.js"></script>
            <!-- Include Tailwind CSS -->
            <link href="https://cdnjs.cloudflare.com/ajax/libs/tailwindcss/2.2.19/tailwind.min.css" rel="stylesheet">
            <style>
                pre { overflow-x: auto; white-space: pre-wrap; }
                .test-pass { background-color: #e6ffed; }
                .test-fail { background-color: #ffebe9; }
            </style>
        </head>
        <body class="bg-gray-50">
            <div id="root"></div>
            
            <script>
                // Data will be decoded from Base64 for safety
                window.encodedPydanticData = "ENCODED_DATA_PLACEHOLDER";
                
                // Create a function to safely decode the data when needed
                window.getPydanticData = function() {
                    try {
                        const jsonStr = atob(window.encodedPydanticData);
                        return JSON.parse(jsonStr);
                    } catch (e) {
                        console.error("Error decoding data:", e);
                        return {};
                    }
                };
            </script>
            
            <script type="text/babel">
                const { useState } = React;
                
                function JColtDashboard() {
                    const [selectedModel, setSelectedModel] = useState(null);
                    const [selectedField, setSelectedField] = useState(null);
                    const [selectedTest, setSelectedTest] = useState(null);
                    const [searchTerm, setSearchTerm] = useState("");
                    const [filterPassed, setFilterPassed] = useState(null); // null = all, true = passed, false = failed
                    
                    // Get the data safely from our decoder function
                    const pydanticData = window.getPydanticData() || {};
                    
                    // Sanitize function for displaying values
                    const sanitizeOutput = (value) => {
                        if (value === null || value === undefined) return "null";
                        
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
                        return String(value)
                            .replace(/&/g, "&amp;")
                            .replace(/</g, "&lt;")
                            .replace(/>/g, "&gt;")
                            .replace(/"/g, "&quot;")
                            .replace(/'/g, "&#039;");
                    };
                    
                    // Calculate overall stats
                    const calculateOverallStats = () => {
                        let totalTests = 0;
                        let passedTests = 0;
                        
                        Object.values(pydanticData).forEach(modelData => {
                            Object.values(modelData.fields || {}).forEach(fieldTests => {
                                // Handle both array and object with tests property
                                const tests = Array.isArray(fieldTests) ? fieldTests : (fieldTests.tests || []);
                                
                                tests.forEach(test => {
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
                    
                    const stats = calculateOverallStats();
                    
                    // Generate stats for a model
                    const getModelStats = (modelData) => {
                        let totalTests = 0;
                        let passedTests = 0;
                        
                        Object.values(modelData.fields || {}).forEach(fieldTests => {
                            // Handle both array and object with tests property
                            const tests = Array.isArray(fieldTests) ? fieldTests : (fieldTests.tests || []);
                            
                            tests.forEach(test => {
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
                    
                    // Filter models based on search and filters
                    const filteredModels = Object.entries(pydanticData).filter(([modelName, modelData]) => {
                        if (searchTerm && !modelName.toLowerCase().includes(searchTerm.toLowerCase())) {
                            return false;
                        }
                        
                        // If filtering for pass/fail
                        if (filterPassed !== null) {
                            let modelHasMatchingTests = false;
                            
                            Object.values(modelData.fields || {}).forEach(fieldTests => {
                                // Handle both array and object with tests property
                                const tests = Array.isArray(fieldTests) ? fieldTests : (fieldTests.tests || []);
                                
                                const hasFailedTests = tests.some(test => !test.pass);
                                
                                if ((filterPassed === true && !hasFailedTests) || 
                                    (filterPassed === false && hasFailedTests)) {
                                    modelHasMatchingTests = true;
                                }
                            });
                            
                            return modelHasMatchingTests;
                        }
                        
                        return true;
                    });
                    
                    // Handle model click
                    const toggleModel = (modelName) => {
                        if (selectedModel === modelName) {
                            setSelectedModel(null);
                            setSelectedField(null);
                            setSelectedTest(null);
                        } else {
                            setSelectedModel(modelName);
                            setSelectedField(null);
                            setSelectedTest(null);
                        }
                    };
                    
                    // Handle field click
                    const toggleField = (fieldName) => {
                        if (selectedField === fieldName) {
                            setSelectedField(null);
                            setSelectedTest(null);
                        } else {
                            setSelectedField(fieldName);
                            setSelectedTest(null);
                        }
                    };
                    
                    // Export results as JSON
                    const exportJSON = () => {
                        const dataStr = JSON.stringify(pydanticData, null, 2);
                        const dataUri = `data:application/json;charset=utf-8,${encodeURIComponent(dataStr)}`;
                        const exportName = `jcolt_pydantic_results_${new Date().toISOString().slice(0, 19).replace(/:/g, "-")}.json`;
                        
                        const linkElement = document.createElement('a');
                        linkElement.setAttribute('href', dataUri);
                        linkElement.setAttribute('download', exportName);
                        linkElement.click();
                    };
                    
                    return (
                        <div className="container mx-auto px-4 py-8">
                            {/* Header */}
                            <div className="flex flex-col md:flex-row justify-between items-center mb-8">
                                <h1 className="text-3xl font-bold mb-4 md:mb-0">JColt Pydantic Testing Dashboard</h1>
                                <button 
                                    onClick={exportJSON}
                                    className="bg-blue-500 hover:bg-blue-600 text-white py-2 px-4 rounded flex items-center"
                                >
                                    <span className="mr-2">⬇️</span> Export JSON
                                </button>
                            </div>
                            
                            {/* Summary Stats */}
                            <div className="bg-white p-6 rounded-lg shadow-sm mb-8">
                                <h2 className="text-xl font-bold mb-4">Test Summary</h2>
                                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                                    <div className="bg-gray-50 p-4 rounded">
                                        <div className="text-sm text-gray-500">Total Tests</div>
                                        <div className="text-2xl font-bold">{stats.totalTests}</div>
                                    </div>
                                    <div className="bg-gray-50 p-4 rounded">
                                        <div className="text-sm text-gray-500">Passed</div>
                                        <div className="text-2xl font-bold text-green-600">{stats.passedTests}</div>
                                    </div>
                                    <div className="bg-gray-50 p-4 rounded">
                                        <div className="text-sm text-gray-500">Failed</div>
                                        <div className="text-2xl font-bold text-red-600">{stats.failedTests}</div>
                                    </div>
                                    <div className="bg-gray-50 p-4 rounded">
                                        <div className="text-sm text-gray-500">Pass Rate</div>
                                        <div className="text-2xl font-bold">{stats.passRate}%</div>
                                    </div>
                                </div>
                                {/* Progress Bar */}
                                <div className="w-full bg-gray-200 rounded-full h-4 mt-4">
                                    <div 
                                        className={`h-4 rounded-full ${
                                            stats.passRate > 80 ? 'bg-green-500' : 
                                            stats.passRate > 50 ? 'bg-yellow-500' : 
                                            'bg-red-500'
                                        }`}
                                        style={{ width: `${stats.passRate}%` }}
                                    ></div>
                                </div>
                            </div>
                            
                            {/* Filters */}
                            <div className="mb-6">
                                <div className="flex flex-col md:flex-row items-start md:items-center">
                                    <div className="flex items-center mb-4 md:mb-0 md:mr-4">
                                        <input
                                            type="text"
                                            placeholder="Search models and fields..."
                                            className="px-3 py-2 border rounded-md"
                                            value={searchTerm}
                                            onChange={(e) => setSearchTerm(e.target.value)}
                                        />
                                    </div>
                                    <div className="flex space-x-2">
                                        <button
                                            className={`px-3 py-2 rounded ${filterPassed === null ? 'bg-blue-500 text-white' : 'bg-gray-200'}`}
                                            onClick={() => setFilterPassed(null)}
                                        >
                                            All Tests
                                        </button>
                                        <button
                                            className={`px-3 py-2 rounded ${filterPassed === true ? 'bg-green-500 text-white' : 'bg-gray-200'}`}
                                            onClick={() => setFilterPassed(true)}
                                        >
                                            Passing Only
                                        </button>
                                        <button
                                            className={`px-3 py-2 rounded ${filterPassed === false ? 'bg-red-500 text-white' : 'bg-gray-200'}`}
                                            onClick={() => setFilterPassed(false)}
                                        >
                                            Failing Only
                                        </button>
                                    </div>
                                </div>
                            </div>
                            
                            {/* No Results Message */}
                            {filteredModels.length === 0 && (
                                <div className="bg-white p-8 text-center rounded-lg shadow">
                                    <h3 className="text-xl font-bold mb-2">No Results Found</h3>
                                    <p className="text-gray-600">
                                        {Object.keys(pydanticData).length === 0 
                                            ? "No test data available. Run Pydantic tests to see results." 
                                            : "No results match your current filters."
                                        }
                                    </p>
                                </div>
                            )}
                            
                            {/* Models */}
                            <div className="space-y-6">
                                {filteredModels.map(([modelName, modelData]) => {
                                    const modelStats = getModelStats(modelData);
                                    const isSelected = selectedModel === modelName;
                                    
                                    return (
                                        <div key={modelName} className="bg-white rounded-lg shadow-sm border">
                                            {/* Model Header */}
                                            <div className="p-4 border-b">
                                                <div className="flex justify-between items-center">
                                                    <h3 className="text-lg font-semibold">{sanitizeOutput(modelName)}</h3>
                                                    <span className="text-sm text-gray-500">
                                                        {modelData.method?.toUpperCase() || ''} {sanitizeOutput(modelData.path || '')}
                                                    </span>
                                                </div>
                                                {modelData.operation_id && (
                                                    <p className="text-sm text-gray-500">ID: {sanitizeOutput(modelData.operation_id)}</p>
                                                )}
                                            </div>
                                            
                                            {/* Model Stats */}
                                            <div className="p-4">
                                                <div className="flex flex-wrap text-sm mb-2">
                                                    <div className="mr-4 mb-2">
                                                        <span className="font-medium">Tests:</span> {modelStats.totalTests}
                                                    </div>
                                                    <div className="mr-4 mb-2">
                                                        <span className="font-medium text-green-600">Passed:</span> {modelStats.passedTests}
                                                    </div>
                                                    <div className="mr-4 mb-2">
                                                        <span className="font-medium text-red-600">Failed:</span> {modelStats.failedTests}
                                                    </div>
                                                    <div className="mb-2">
                                                        <span className="font-medium">Pass Rate:</span> {modelStats.passRate}%
                                                    </div>
                                                </div>
                                                
                                                {/* Progress Bar */}
                                                <div className="w-full bg-gray-200 rounded-full h-2 mb-4">
                                                    <div 
                                                        className={`h-2 rounded-full ${
                                                            modelStats.passRate > 80 ? 'bg-green-500' : 
                                                            modelStats.passRate > 50 ? 'bg-yellow-500' : 
                                                            'bg-red-500'
                                                        }`}
                                                        style={{ width: `${modelStats.passRate}%` }}
                                                    ></div>
                                                </div>
                                                
                                                {/* Fields (if model is selected) */}
                                                {isSelected && Object.entries(modelData.fields || {}).map(([fieldName, fieldTests]) => {
                                                    // Convert to array if necessary
                                                    const tests = Array.isArray(fieldTests) ? fieldTests : (fieldTests.tests || []);
                                                    
                                                    // Skip fields that don't match search or filter
                                                    if (searchTerm && !fieldName.toLowerCase().includes(searchTerm.toLowerCase())) {
                                                        return null;
                                                    }
                                                    
                                                    const fieldPassedTests = tests.filter(test => test.pass).length;
                                                    const fieldFailedTests = tests.length - fieldPassedTests;
                                                    
                                                    if (filterPassed === true && fieldFailedTests > 0) {
                                                        return null;
                                                    }
                                                    
                                                    if (filterPassed === false && fieldFailedTests === 0) {
                                                        return null;
                                                    }
                                                    
                                                    const isFieldSelected = selectedField === fieldName;
                                                    
                                                    return (
                                                        <div key={fieldName} className="border rounded-md p-3 mb-3">
                                                            <div 
                                                                className="flex justify-between items-center cursor-pointer"
                                                                onClick={() => toggleField(fieldName)}
                                                            >
                                                                <h4 className="font-medium">{sanitizeOutput(fieldName)}</h4>
                                                                <div className="flex items-center">
                                                                    <span className="text-green-600 mr-1">{fieldPassedTests}</span>
                                                                    <span className="text-gray-400">/</span>
                                                                    <span className="ml-1">{tests.length}</span>
                                                                    <span className="ml-2">
                                                                        {isFieldSelected ? '▼' : '▶'}
                                                                    </span>
                                                                </div>
                                                            </div>
                                                            
                                                            {isFieldSelected && (
                                                                <div className="mt-3">
                                                                    {/* Test Results Table */}
                                                                    <div className="overflow-x-auto">
                                                                        <table className="min-w-full border-collapse">
                                                                            <thead>
                                                                                <tr className="bg-gray-100">
                                                                                    <th className="p-2 text-left border">Test</th>
                                                                                    <th className="p-2 text-left border">Type</th>
                                                                                    <th className="p-2 text-left border">Result</th>
                                                                                    <th className="p-2 text-left border">Expected</th>
                                                                                    <th className="p-2 text-left border">Actual</th>
                                                                                    <th className="p-2 text-left border">Status</th>
                                                                                </tr>
                                                                            </thead>
                                                                            <tbody>
                                                                                {tests.map((test, index) => (
                                                                                    <tr 
                                                                                        key={index} 
                                                                                        className={`${test.pass ? 'test-pass' : 'test-fail'} cursor-pointer hover:bg-gray-50`}
                                                                                        onClick={() => setSelectedTest(selectedTest === index ? null : index)}
                                                                                    >
                                                                                        <td className="p-2 border">{sanitizeOutput(test.name)}</td>
                                                                                        <td className="p-2 border">{sanitizeOutput(test.test_type)}</td>
                                                                                        <td className="p-2 border">
                                                                                            {test.pass 
                                                                                                ? <span className="text-green-500">✓</span> 
                                                                                                : <span className="text-red-500">✗</span>
                                                                                            }
                                                                                        </td>
                                                                                        <td className="p-2 border">{sanitizeOutput(test.expected_result)}</td>
                                                                                        <td className="p-2 border">{sanitizeOutput(test.actual_result)}</td>
                                                                                        <td className="p-2 border">{sanitizeOutput(test.status_code)}</td>
                                                                                    </tr>
                                                                                ))}
                                                                            </tbody>
                                                                        </table>
                                                                    </div>
                                                                    
                                                                    {/* Test Details (if a test is selected) */}
                                                                    {selectedTest !== null && tests[selectedTest] && (
                                                                        <div className="mt-4 p-4 bg-gray-50 rounded-md">
                                                                            <h5 className="font-semibold mb-2">{sanitizeOutput(tests[selectedTest].name)}</h5>
                                                                            <p className="text-gray-600 mb-4">{sanitizeOutput(tests[selectedTest].description)}</p>
                                                                            
                                                                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                                                                <div>
                                                                                    <h6 className="font-medium mb-1">Test Value:</h6>
                                                                                    <pre className="bg-gray-100 p-2 rounded text-sm overflow-x-auto">
                                                                                        {sanitizeOutput(tests[selectedTest].value)}
                                                                                    </pre>
                                                                                </div>
                                                                                
                                                                                <div>
                                                                                    <h6 className="font-medium mb-1">Response:</h6>
                                                                                    <pre className="bg-gray-100 p-2 rounded text-sm overflow-x-auto">
                                                                                        {sanitizeOutput(tests[selectedTest].response_body)}
                                                                                    </pre>
                                                                                </div>
                                                                            </div>
                                                                        </div>
                                                                    )}
                                                                </div>
                                                            )}
                                                        </div>
                                                    );
                                                })}
                                            </div>
                                            
                                            {/* Toggle Button */}
                                            <div className="p-4 border-t bg-gray-50">
                                                <button 
                                                    className={`w-full py-2 px-4 rounded ${isSelected ? 'bg-gray-200' : 'bg-gray-100 hover:bg-gray-200'}`}
                                                    onClick={() => toggleModel(modelName)}
                                                >
                                                    {isSelected ? 'Hide Details' : 'Show Details'}
                                                </button>
                                            </div>
                                        </div>
                                    );
                                })}
                            </div>
                            
                            {/* Footer */}
                            <div className="mt-8 pt-4 border-t text-center text-gray-500 text-sm">
                                Generated by JColt on {new Date().toLocaleString()}
                            </div>
                        </div>
                    );
                }
                
                // Render the component to the DOM
                ReactDOM.render(<JColtDashboard />, document.getElementById('root'));
            </script>
        </body>
        </html>
        """
        
        # Inject the encoded data using string replacement
        html_content = html_content.replace("ENCODED_DATA_PLACEHOLDER", encoded_data)
        
        # Write the HTML file
        with open(filepath, 'w') as f:
            f.write(html_content)
            
        print(f"\nHTML report generated: {filepath}")
        
        # Open the report in browser
        try:
            webbrowser.open(f"file://{os.path.abspath(filepath)}")
            print("Opening dashboard in your default browser...")
        except Exception as e:
            print(f"Note: Could not automatically open browser: {e}")
            print(f"Please open the HTML file manually: {filepath}")
        
        return filepath