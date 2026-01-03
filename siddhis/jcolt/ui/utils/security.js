export const enhancedSanitization = (value) => {
  if (typeof value !== 'string') {
    return value;
  }

  // Basic XSS prevention
  const escaped = value
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');

  // Prevent JavaScript execution
  const sanitized = escaped
    .replace(/javascript:/gi, '')
    .replace(/on\w+=/gi, '')
    .replace(/data:/gi, '')
    .replace(/vbscript:/gi, '');

  return sanitized;
};

export const validateInput = (input, schema) => {
  try {
    return schema.parse(input);
  } catch (error) {
    console.error('Validation error:', error);
    return null;
  }
};

export const secureStorage = {
  set: (key, value) => {
    const encrypted = btoa(JSON.stringify(value)); // Basic encoding, use proper encryption in production
    localStorage.setItem(key, encrypted);
  },
  get: (key) => {
    try {
      const encrypted = localStorage.getItem(key);
      return encrypted ? JSON.parse(atob(encrypted)) : null;
    } catch (error) {
      console.error('Error decrypting data:', error);
      return null;
    }
  }
};

export const sanitizeDisplay = {
  decode: (content) => {
    if (typeof content !== 'string') return content;
    
    // Decode hex-encoded content for display
    const decoded = content.replace(/\\x([0-9a-fA-F]{2})/g, 
      (_, hex) => String.fromCharCode(parseInt(hex, 16)));
    
    // Ensure HTML entities remain escaped
    return decoded
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  },
  
  isPayload: (content) => {
    if (typeof content !== 'string') return false;
    const dangerous = [
      '<script',
      'javascript:',
      'onerror=',
      'alert(',
      'onclick=',
      'onload=',
      'eval(',
      'document.'
    ];
    return dangerous.some(pattern => 
      content.toLowerCase().includes(pattern));
  },
  
  formatPayload: (content) => {
    if (!sanitizeDisplay.isPayload(content)) return content;
    return `[SECURITY] ${sanitizeDisplay.decode(content)}`;
  }
}; 