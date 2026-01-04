import React, { useState, useEffect } from 'react';
import { format } from 'date-fns';
import { motion } from 'framer-motion';

export const TestHistory = ({ testId }) => {
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchTestHistory(testId);
  }, [testId]);

  const fetchTestHistory = async (id) => {
    try {
      const response = await fetch(`/api/test-history/${id}`);
      const data = await response.json();
      setHistory(data);
    } catch (error) {
      console.error('Error fetching test history:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div>Loading history...</div>;
  }

  return (
    <div className="test-history">
      <h3 className="text-lg font-semibold mb-4">Test History</h3>
      <div className="timeline">
        {history.map((entry, index) => (
          <motion.div
            key={entry.id}
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: index * 0.1 }}
            className="history-entry flex items-center mb-4"
          >
            <div className="w-32 text-sm text-gray-500">
              {format(new Date(entry.timestamp), 'MMM dd, yyyy')}
            </div>
            <div className={`status-dot ${entry.passed ? 'bg-green-500' : 'bg-red-500'}`} />
            <div className="ml-4">
              <div className="font-medium">{entry.result}</div>
              <div className="text-sm text-gray-600">{entry.details}</div>
            </div>
          </motion.div>
        ))}
      </div>
    </div>
  );
}; 