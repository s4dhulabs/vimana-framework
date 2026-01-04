import { useEffect } from 'react';

export const useKeyboardShortcuts = (shortcuts) => {
  useEffect(() => {
    const handleKeyPress = (event) => {
      const { key, ctrlKey, shiftKey } = event;
      
      Object.entries(shortcuts).forEach(([shortcut, callback]) => {
        const [modifier, k] = shortcut.split('+');
        
        if (
          (modifier === 'ctrl' && ctrlKey && key.toLowerCase() === k.toLowerCase()) ||
          (modifier === 'shift' && shiftKey && key.toLowerCase() === k.toLowerCase())
        ) {
          event.preventDefault();
          callback();
        }
      });
    };
    
    window.addEventListener('keydown', handleKeyPress);
    return () => window.removeEventListener('keydown', handleKeyPress);
  }, [shortcuts]);
}; 