import React, { useEffect, useState } from 'react';
import { ShieldAlert, Database, GitBranch, Zap } from 'lucide-react';

const FinalVimanaHeader = () => {
  const [currentTime, setCurrentTime] = useState('');
  const [pulseActive, setPulseActive] = useState(false);
  
  // Update time and pulse animation periodically
  useEffect(() => {
    const updateTime = () => {
      const now = new Date();
      setCurrentTime(now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }));
      setPulseActive(true);
      
      // Reset pulse after animation completes
      setTimeout(() => setPulseActive(false), 1000);
    };
    
    updateTime();
    const interval = setInterval(updateTime, 10000);
    return () => clearInterval(interval);
  }, []);

  // Original Vimana error types 
  const leftErrors = [
    'SystemError',
    'TypeError',
    'ValueError',
    '    UnicodeError',
    '        UnicodeDecodeError',
    '        UnicodeEncodeError',
    '        UnicodeTranslateError',
    'Warning',
    '    DeprecationWarning',
    '    PendingDeprecationWarning',
    '    RuntimeWarning',
    '    SyntaxWarning',
    '    UserWarning',
    '    FutureWarning',
    '    ImportWarning',
    '    UnicodeWarning',
    '    BytesWarning',
    '    ResourceWarning'
  ];

  const rightErrors = [
    'OSError',
    '    BlockingIOError',
    '    ChildProcessError',
    '    ConnectionError',
    '        BrokenPipeError',
    '        ConnectionAbortedError',
    '        ConnectionRefusedError',
    '        ConnectionResetError',
    '    FileExistsError',
    '    FileNotFoundError',
    '    InterruptedError',
    '    IsADirectoryError',
    '    NotADirectoryError',
    '    PermissionError',
    '    ProcessLookupError',
    '    TimeoutError',
    'ReferenceError',
    'RuntimeError',
    '    NotImplementedError',
    '    RecursionError',
    'SyntaxError',
    '    IndentationError',
    '        TabError'
  ];

  // Tooltips for feature icons
  const tooltips = {
    exceptions: "Exception Analysis: Identifies and categorizes runtime errors and exceptions detected during fuzzing operations, helping locate vulnerabilities in application logic.",
    dataFlow: "Data Flow: Visualizes how data moves through the application, tracking input transformations and detecting potential data leakage points.",
    codeAnalysis: "Code Analysis: Examines source code to identify potential security issues, vulnerabilities, and quality concerns based on scanning results.",
    liveTesting: "Live Testing: Real-time fuzzing and monitoring of target applications with immediate feedback on discovered issues."
  };

  return (
    <div className="relative w-full h-40 bg-black overflow-hidden">
      {/* Background gradient overlay */}
      <div className="absolute inset-0 bg-gradient-to-r from-gray-900 via-black to-gray-900 opacity-90"></div>
      
      {/* Left column of errors - from original Vimana design */}
      <div className="absolute left-0 top-0 bottom-0 w-1/4 overflow-hidden font-mono text-xs opacity-20 mt-2">
        {leftErrors.map((error, index) => (
          <div key={`left-${index}`} className="whitespace-nowrap text-green-500 ml-2">
            {error.startsWith('    ') ? error : `+-- ${error}`}
          </div>
        ))}
      </div>
      
      {/* Right column of errors - from original Vimana design */}
      <div className="absolute right-0 top-0 bottom-0 w-1/4 overflow-hidden font-mono text-xs opacity-20 mt-2">
        {rightErrors.map((error, index) => (
          <div key={`right-${index}`} className="whitespace-nowrap text-green-500 ml-4">
            {error.startsWith('    ') ? error : `+-- ${error}`}
          </div>
        ))}
      </div>
      
      {/* Vimana structure from original design but with elegant details */}
      <div className="absolute inset-0 flex items-center justify-center opacity-20">
        <svg width="300" height="300" viewBox="0 0 300 300">
          {/* Top conical section - from original design */}
          <path d="M150,50 C170,70 200,80 200,100 C200,120 170,130 150,130 C130,130 100,120 100,100 C100,80 130,70 150,50 Z" 
                stroke="#f8e16c" 
                strokeWidth="0.8" 
                fill="none" />
          
          {/* Middle tiered section - from original design */}
          <path d="M100,100 L200,100 L215,170 L85,170 Z" 
                stroke="#f8e16c" 
                strokeWidth="0.8" 
                fill="url(#goldGradient)" 
                opacity="0.2" />
          
          {/* Base section - from original design */}
          <path d="M85,170 L215,170 L240,250 L60,250 Z" 
                stroke="#f8e16c" 
                strokeWidth="0.8" 
                fill="none" />
                
          {/* Detail lines on tiers - from original design */}
          <path d="M110,115 L190,115" stroke="#f8e16c" strokeWidth="0.5" opacity="0.7" />
          <path d="M105,130 L195,130" stroke="#f8e16c" strokeWidth="0.5" opacity="0.7" />
          <path d="M100,145 L200,145" stroke="#f8e16c" strokeWidth="0.5" opacity="0.7" />
          <path d="M95,160 L205,160" stroke="#f8e16c" strokeWidth="0.5" opacity="0.7" />
          
          <path d="M90,185 L210,185" stroke="#f8e16c" strokeWidth="0.5" opacity="0.7" />
          <path d="M95,200 L205,200" stroke="#f8e16c" strokeWidth="0.5" opacity="0.7" />
          <path d="M100,215 L200,215" stroke="#f8e16c" strokeWidth="0.5" opacity="0.7" />
          <path d="M105,230 L195,230" stroke="#f8e16c" strokeWidth="0.5" opacity="0.7" />
          
          {/* Central core/light - original but with animation from elegant version */}
          <circle cx="150" cy="130" r="10" fill="#f8e16c" opacity="0.6">
            <animate attributeName="opacity" values="0.4;0.7;0.4" dur="4s" repeatCount="indefinite" />
          </circle>
          
          {/* Sacred geometry accent lines - from elegant version */}
          <path d="M150,50 L150,250" stroke="#f8e16c" strokeWidth="0.2" opacity="0.3" />
          <path d="M60,250 L240,100" stroke="#f8e16c" strokeWidth="0.2" opacity="0.3" />
          <path d="M60,100 L240,250" stroke="#f8e16c" strokeWidth="0.2" opacity="0.3" />
          
          {/* Small lights matching the original image */}
          <circle cx="120" cy="160" r="3" fill="#f96e46" opacity="0.7">
            <animate attributeName="opacity" values="0.4;0.8;0.4" dur="3s" repeatCount="indefinite" />
          </circle>
          <circle cx="180" cy="160" r="3" fill="#f96e46" opacity="0.7">
            <animate attributeName="opacity" values="0.5;0.9;0.5" dur="2.5s" repeatCount="indefinite" />
          </circle>
          <circle cx="150" cy="200" r="3" fill="#f96e46" opacity="0.7">
            <animate attributeName="opacity" values="0.4;0.8;0.4" dur="3.5s" repeatCount="indefinite" />
          </circle>
          
          {/* Gradients from elegant version */}
          <defs>
            <linearGradient id="goldGradient" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="#f8e16c" stopOpacity="0.1" />
              <stop offset="50%" stopColor="#f9a826" stopOpacity="0.3" />
              <stop offset="100%" stopColor="#f8e16c" stopOpacity="0.1" />
            </linearGradient>
          </defs>
        </svg>
      </div>
      
      {/* Subtle horizontal lines from elegant version */}
      <div className="absolute w-full h-full">
        <svg width="100%" height="100%" className="opacity-15">
          <line x1="0" y1="50%" x2="100%" y2="50%" stroke="#f8e16c" strokeWidth="0.5" strokeDasharray="15,10" />
          <line x1="0" y1="25%" x2="100%" y2="25%" stroke="#f8e16c" strokeWidth="0.5" strokeDasharray="10,15" opacity="0.5" />
          <line x1="0" y1="75%" x2="100%" y2="75%" stroke="#f8e16c" strokeWidth="0.5" strokeDasharray="12,12" opacity="0.5" />
        </svg>
      </div>
      
      {/* Main content container with elegant styling */}
      <div className="relative h-full z-10">]
        
    
        {/* Top status bar with elegant styling */}
        <div className="absolute top-0 left-0 right-0 h-12 border-b border-yellow-800 border-opacity-30 flex items-center justify-between px-8">
        {/* Left side with monitoring status */}
        <div className="flex items-center">
            <div className={`w-2 h-2 rounded-full ${pulseActive ? 'animate-ping' : ''} bg-green-500 mr-3`}></div>
            <span className="text-yellow-400 opacity-90 font-light tracking-wider text-xs">ABDUCTING...  {currentTime}</span>
        </div>
        
        {/* Right side with version info and GitHub */}
        <div className="flex items-center space-x-6">
            {/* Version info with ancient name */}
            <div className="group relative flex items-center">
            <span className="text-gray-500 text-xs">VFMon 1.0</span>
            <span className="ml-2 text-green-600 text-xs italic opacity-60">Nirīkṣaṇa</span>
            {/* Hover tooltip for more info */}
            <div className="absolute bottom-full right-0 mb-2 w-48 bg-black bg-opacity-90 text-xs text-gray-300 p-2 rounded border border-yellow-900 border-opacity-40 shadow-lg opacity-0 group-hover:opacity-100 transition-opacity duration-300 pointer-events-none">
                Vimana Framework 1.0
            </div>
            </div>
            
            {/* GitHub link with icon */}
            <a 
            href="https://github.com/s4dhulabs" 
            target="_blank" 
            rel="noopener noreferrer" 
            className="flex items-center text-gray-500 hover:text-yellow-400 transition-colors duration-300"
            >
            <svg 
                viewBox="0 0 24 24" 
                className="w-4 h-4 mr-1" 
                fill="currentColor"
            >
                <path d="M12 .297c-6.63 0-12 5.373-12 12 0 5.303 3.438 9.8 8.205 11.385.6.113.82-.258.82-.577 0-.285-.01-1.04-.015-2.04-3.338.724-4.042-1.61-4.042-1.61C4.422 18.07 3.633 17.7 3.633 17.7c-1.087-.744.084-.729.084-.729 1.205.084 1.838 1.236 1.838 1.236 1.07 1.835 2.809 1.305 3.495.998.108-.776.417-1.305.76-1.605-2.665-.3-5.466-1.332-5.466-5.93 0-1.31.465-2.38 1.235-3.22-.135-.303-.54-1.523.105-3.176 0 0 1.005-.322 3.3 1.23.96-.267 1.98-.399 3-.405 1.02.006 2.04.138 3 .405 2.28-1.552 3.285-1.23 3.285-1.23.645 1.653.24 2.873.12 3.176.765.84 1.23 1.91 1.23 3.22 0 4.61-2.805 5.625-5.475 5.92.42.36.81 1.096.81 2.22 0 1.606-.015 2.896-.015 3.286 0 .315.21.69.825.57C20.565 22.092 24 17.592 24 12.297c0-6.627-5.373-12-12-12"/>
            </svg>
            <span className="text-xs font-mono">s4dhulabs</span>
            </a>
        </div>
        </div>
        
        {/* Main title and controls area - elegant styling */}
        <div className="absolute bottom-0 left-0 right-0 flex items-center justify-between px-12 py-3">
          <div className="flex items-center">
            {/* Small Vimana hovering next to title */}
            <div className="mr-3 opacity-80">
              <svg width="32" height="32" viewBox="0 0 32 32">
                <path d="M16,4 C18,6 21,7 21,9 C21,11 18,12 16,12 C14,12 11,11 11,9 C11,7 14,6 16,4 Z" 
                      stroke="#f8e16c" 
                      strokeWidth="0.8" 
                      fill="none" />
                <path d="M11,9 L21,9 L23,17 L9,17 Z" 
                      stroke="#f8e16c" 
                      strokeWidth="0.8" 
                      fill="none" />
                <path d="M9,17 L23,17 L26,26 L6,26 Z" 
                      stroke="#f8e16c" 
                      strokeWidth="0.8" 
                      fill="none" />
                <circle cx="16" cy="13" r="1.5" fill="#f8e16c" opacity="0.8">
                  <animate attributeName="opacity" values="0.6;0.9;0.6" dur="3s" repeatCount="indefinite" />
                </circle>
              </svg>
            </div>
            
            <h1 className="text-4xl font-light text-yellow-300 tracking-widest">
              VIMANA 
            </h1>
            <div className="w-px h-8 bg-yellow-700 mx-4 opacity-30"></div>
            <h2 className="text-lg font-light text-yellow-100 opacity-80">
              MONITOR
            </h2>
          </div>
          
          {/* Feature controls with elegant styling - BIGGER and MORE BEAUTIFUL */}
          <div className="flex space-x-12">
            {/* Exception Analysis */}
            <div className="group flex flex-col items-center relative">
              <div className="w-14 h-14 rounded-lg bg-gradient-to-br from-red-900 to-red-800 border border-red-700 border-opacity-40 shadow-lg flex items-center justify-center transform group-hover:scale-105 transition-all duration-300">
                <div className="absolute inset-0 bg-black bg-opacity-60 rounded-lg"></div>
                <ShieldAlert className="w-7 h-7 text-red-400 relative z-10" />
                <div className="absolute w-full h-full bg-red-500 rounded-lg opacity-0 group-hover:opacity-10 transition-opacity duration-300"></div>
              </div>
              <span className="text-gray-300 text-xs mt-2 group-hover:text-red-300 transition-colors duration-300">Exception Analysis</span>
              
              {/* Tooltip */}
              <div className="absolute bottom-full mb-2 w-64 bg-black bg-opacity-90 text-xs text-gray-300 p-3 rounded border border-red-900 border-opacity-40 shadow-lg opacity-0 group-hover:opacity-100 transition-opacity duration-300 pointer-events-none">
                {tooltips.exceptions}
              </div>
            </div>
            
            {/* Data Flow */}
            <div className="group flex flex-col items-center relative">
              <div className="w-14 h-14 rounded-lg bg-gradient-to-br from-blue-900 to-blue-800 border border-blue-700 border-opacity-40 shadow-lg flex items-center justify-center transform group-hover:scale-105 transition-all duration-300">
                <div className="absolute inset-0 bg-black bg-opacity-60 rounded-lg"></div>
                <Database className="w-7 h-7 text-blue-400 relative z-10" />
                <div className="absolute w-full h-full bg-blue-500 rounded-lg opacity-0 group-hover:opacity-10 transition-opacity duration-300"></div>
              </div>
              <span className="text-gray-300 text-xs mt-2 group-hover:text-blue-300 transition-colors duration-300">Data Flow</span>
              
              {/* Tooltip */}
              <div className="absolute bottom-full mb-2 w-64 bg-black bg-opacity-90 text-xs text-gray-300 p-3 rounded border border-blue-900 border-opacity-40 shadow-lg opacity-0 group-hover:opacity-100 transition-opacity duration-300 pointer-events-none">
                {tooltips.dataFlow}
              </div>
            </div>
            
            {/* Code Analysis */}
            <div className="group flex flex-col items-center relative">
              <div className="w-14 h-14 rounded-lg bg-gradient-to-br from-green-900 to-green-800 border border-green-700 border-opacity-40 shadow-lg flex items-center justify-center transform group-hover:scale-105 transition-all duration-300">
                <div className="absolute inset-0 bg-black bg-opacity-60 rounded-lg"></div>
                <GitBranch className="w-7 h-7 text-green-400 relative z-10" />
                <div className="absolute w-full h-full bg-green-500 rounded-lg opacity-0 group-hover:opacity-10 transition-opacity duration-300"></div>
              </div>
              <span className="text-gray-300 text-xs mt-2 group-hover:text-green-300 transition-colors duration-300">Code Analysis</span>
              
              {/* Tooltip */}
              <div className="absolute bottom-full mb-2 w-64 bg-black bg-opacity-90 text-xs text-gray-300 p-3 rounded border border-green-900 border-opacity-40 shadow-lg opacity-0 group-hover:opacity-100 transition-opacity duration-300 pointer-events-none">
                {tooltips.codeAnalysis}
              </div>
            </div>
            
            {/* Live Testing */}
            <div className="group flex flex-col items-center relative">
              <div className="w-14 h-14 rounded-lg bg-gradient-to-br from-yellow-900 to-yellow-800 border border-yellow-700 border-opacity-40 shadow-lg flex items-center justify-center transform group-hover:scale-105 transition-all duration-300">
                <div className="absolute inset-0 bg-black bg-opacity-60 rounded-lg"></div>
                <Zap className="w-7 h-7 text-yellow-400 relative z-10" />
                <div className="absolute w-full h-full bg-yellow-500 rounded-lg opacity-0 group-hover:opacity-10 transition-opacity duration-300"></div>
              </div>
              <span className="text-gray-300 text-xs mt-2 group-hover:text-yellow-300 transition-colors duration-300">Live Testing</span>
              
              {/* Tooltip */}
              <div className="absolute bottom-full mb-2 w-64 bg-black bg-opacity-90 text-xs text-gray-300 p-3 rounded border border-yellow-900 border-opacity-40 shadow-lg opacity-0 group-hover:opacity-100 transition-opacity duration-300 pointer-events-none">
                {tooltips.liveTesting}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default FinalVimanaHeader;