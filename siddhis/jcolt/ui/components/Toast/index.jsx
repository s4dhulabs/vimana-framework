import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';

export const Toast = ({ message, type, onClose }) => {
  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0, y: 50 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, y: 50 }}
        className={`toast fixed bottom-4 right-4 p-4 rounded-lg shadow-lg ${
          type === 'success' ? 'bg-green-500' :
          type === 'error' ? 'bg-red-500' :
          'bg-blue-500'
        } text-white`}
      >
        <div className="flex items-center">
          <span className="mr-2">
            {type === 'success' ? '✅' :
             type === 'error' ? '❌' :
             'ℹ️'}
          </span>
          <p>{message}</p>
          <button
            onClick={onClose}
            className="ml-4 text-white hover:text-gray-200"
          >
            ×
          </button>
        </div>
      </motion.div>
    </AnimatePresence>
  );
}; 