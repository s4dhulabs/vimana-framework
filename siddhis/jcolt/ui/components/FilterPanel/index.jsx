import React, { useState, useEffect } from 'react';
import { SearchBar } from './SearchBar';
import { FilterOptions } from './FilterOptions';
import { useDebounce } from '../../hooks/useDebounce';

export const FilterPanel = ({ onFilterChange }) => {
  const [filters, setFilters] = useState({
    search: '',
    testTypes: [],
    statusCodes: [],
    dateRange: null,
    tags: [],
    passStatus: null
  });
  
  const debouncedFilters = useDebounce(filters, 300);
  
  useEffect(() => {
    onFilterChange(debouncedFilters);
  }, [debouncedFilters]);

  const handleSearchChange = (searchTerm) => {
    setFilters(prev => ({ ...prev, search: searchTerm }));
  };

  const handleTestTypeChange = (selectedTypes) => {
    setFilters(prev => ({ ...prev, testTypes: selectedTypes }));
  };

  const handleStatusCodeChange = (selectedCodes) => {
    setFilters(prev => ({ ...prev, statusCodes: selectedCodes }));
  };

  const handleDateRangeChange = (range) => {
    setFilters(prev => ({ ...prev, dateRange: range }));
  };

  return (
    <div className="filter-panel p-4 bg-white rounded-lg shadow mb-4">
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <SearchBar 
          value={filters.search}
          onChange={handleSearchChange}
          placeholder="Search tests, models, fields..."
        />
        
        <FilterOptions
          testTypes={filters.testTypes}
          statusCodes={filters.statusCodes}
          dateRange={filters.dateRange}
          onTestTypeChange={handleTestTypeChange}
          onStatusCodeChange={handleStatusCodeChange}
          onDateRangeChange={handleDateRangeChange}
        />
      </div>
      
      <div className="selected-filters mt-4 flex flex-wrap gap-2">
        {filters.testTypes.map(type => (
          <span key={type} className="px-2 py-1 bg-blue-100 text-blue-800 rounded">
            {type}
            <button 
              onClick={() => handleTestTypeChange(filters.testTypes.filter(t => t !== type))}
              className="ml-2 text-blue-600 hover:text-blue-800"
            >
              ×
            </button>
          </span>
        ))}
      </div>
    </div>
  );
}; 