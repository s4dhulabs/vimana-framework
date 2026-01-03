export const a11yProps = {
  testDetails: {
    role: 'region',
    'aria-label': 'Test Details',
  },
  filterPanel: {
    role: 'search',
    'aria-label': 'Filter and Search Tests',
  },
  charts: {
    role: 'img',
    'aria-label': 'Test Results Visualization',
  },
  navigation: {
    role: 'navigation',
    'aria-label': 'Main Navigation',
  }
};

export const keyboardNavigation = {
  handleKeyPress: (e, callback) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      callback();
    }
  }
}; 