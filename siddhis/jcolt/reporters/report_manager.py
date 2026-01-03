from datetime import datetime
import json
import logging

class ReportManager:
    def __init__(self, results, export_format='json', verbose=False, json_output=False, output_file=None):
        self.results = results
        self.export_format = export_format.lower() if export_format else 'json'
        self.verbose = verbose
        self.json_output = json_output
        self.output_file = output_file
        self.timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
    def generate_report(self):
        """Generate report in the specified format"""
        if not self.results:
            logging.warning("No results to generate report")
            return False
            
        # Check if we should generate any report at all
        # Only generate if explicitly requested via --json, --output, or --export-format
        should_generate = (
            self.json_output or 
            self.output_file or 
            self.export_format != 'json'  # Default is 'json', so only generate if explicitly changed
        )
        
        if not should_generate:
            # No explicit request for file output, skip report generation
            return False
            
        handlers = {
            'html': self._generate_html_report,
            'json': self._generate_json_report,
            'csv': self._generate_csv_report,
            'pdf': self._generate_pdf_report
        }
        
        handler = handlers.get(self.export_format)
        if not handler:
            logging.error(f"Unsupported export format: {self.export_format}")
            return False
            
        return handler()
    
    def _generate_html_report(self):
        """Generate HTML report"""
        try:
            from .html_reporter import HTMLReporter
            reporter = HTMLReporter(self.results)
            html_file = reporter.generate_report()
            if self.verbose:
                print(f" → HTML dashboard report saved to {html_file}")
            return html_file
        except Exception as e:
            logging.error(f"Error generating HTML report: {str(e)}")
            if self.verbose:
                print(f" → Error generating HTML report: {e}")
            return False
    
    def _generate_json_report(self):
        """Generate JSON report"""
        try:
            # Use custom output file if provided, otherwise use default with timestamp
            if self.output_file:
                output_file = self.output_file
            else:
            output_file = f"jcolt_pydantic_tests_{self.timestamp}.json"
                
            with open(output_file, 'w') as f:
                json.dump(self.results, f, indent=2)
            if self.verbose:
                print(f" → Results saved to {output_file}")
            return output_file
        except Exception as e:
            logging.error(f"Error generating JSON report: {str(e)}")
            return False
    
    def _generate_csv_report(self):
        """Generate CSV report"""
        try:
            output_file = f"jcolt_pydantic_tests_{self.timestamp}.csv"
            with open(output_file, 'w') as f:
                f.write("Model,Field,Test,Type,Expected,Actual,Status,Pass\n")
                for model_name, model_data in self.results.items():
                    for field_name, field_tests in model_data.get('fields', {}).items():
                        for test in field_tests:
                            f.write(
                                f"{model_name},{field_name},"
                                f"{test.get('name', '').replace(',', ';')},"
                                f"{test.get('test_type', '')},"
                                f"{test.get('expected_result', '')},"
                                f"{test.get('actual_result', '')},"
                                f"{test.get('status_code', '')},"
                                f"{test.get('pass', False)}\n"
                            )
            if self.verbose:
                print(f" → CSV report saved to {output_file}")
            return output_file
        except Exception as e:
            logging.error(f"Error generating CSV report: {str(e)}")
            return False
    
    def _generate_pdf_report(self):
        """Generate PDF report"""
        try:
            from .pdf_reporter import PDFReporter
            output_file = f"jcolt_pydantic_tests_{self.timestamp}.pdf"
            
            summary_data = self._calculate_summary()
            reporter = PDFReporter(summary_data)
            reporter.generate_report(output_file)
            
            if self.verbose:
                print(f" → PDF report saved to {output_file}")
            return output_file
        except Exception as e:
            logging.error(f"Error generating PDF report: {str(e)}")
            if self.verbose:
                print(f" → Error generating PDF report: {e}")
            return False
    
    def _calculate_summary(self):
        """Calculate test summary statistics"""
        total_tests = passed_tests = failed_tests = 0
        
        for model_name, model_results in self.results.items():
            fields = model_results.get('fields', {})
            for field_name, field_data in fields.items():
                tests = (field_data if isinstance(field_data, list) 
                        else field_data.get('tests', []) 
                        if isinstance(field_data, dict) else [])
                
                for test in tests:
                    if not isinstance(test, dict):
                        continue
                    total_tests += 1
                    if test.get('pass', False):
                        passed_tests += 1
                    else:
                        failed_tests += 1
        
        pass_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        return {
            'summary': {
                'total': total_tests,
                'passed': passed_tests,
                'failed': failed_tests,
                'pass_rate': round(pass_rate, 1)
            },
            'test_data': self.results
        } 