import React from 'react';
import { TrendChart } from './TrendChart';
import { MetricsCard } from './MetricsCard';
import { Coverage } from './Coverage';

export const Metrics = ({ data }) => {
  return (
    <div className="metrics-dashboard grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      <MetricsCard
        title="Test Coverage"
        value={`${data.coverage.percentage}%`}
        trend={data.coverage.trend}
        icon="📊"
      />
      
      <MetricsCard
        title="Average Response Time"
        value={`${data.performance.avgResponseTime}ms`}
        trend={data.performance.trend}
        icon="⚡"
      />
      
      <MetricsCard
        title="Error Rate"
        value={`${data.errors.rate}%`}
        trend={data.errors.trend}
        icon="❌"
      />
      
      <div className="col-span-full">
        <TrendChart data={data.trends} />
      </div>
      
      <div className="col-span-full md:col-span-2">
        <Coverage data={data.coverage.details} />
      </div>
    </div>
  );
}; 