import React from 'react';
import { Line } from 'react-chartjs-2';

export const TrendGraph = ({ data }) => {
  const chartData = {
    labels: data.dates,
    datasets: [
      {
        label: 'Pass Rate',
        data: data.passRates,
        borderColor: 'rgb(75, 192, 192)',
        tension: 0.1
      },
      {
        label: 'Failed Tests',
        data: data.failedCounts,
        borderColor: 'rgb(255, 99, 132)',
        tension: 0.1
      }
    ]
  };

  const options = {
    responsive: true,
    plugins: {
      legend: {
        position: 'top',
      },
      title: {
        display: true,
        text: 'Test Results Trend'
      }
    },
    scales: {
      y: {
        beginAtZero: true
      }
    }
  };

  return (
    <div className="trend-graph p-4 bg-white rounded-lg shadow">
      <Line data={chartData} options={options} />
    </div>
  );
}; 