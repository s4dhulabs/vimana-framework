class MarkdownReporter:
    def __init__(self, data):
        self.data = data
        
    def generate_report(self):
        md_content = []
        
        # Add header
        md_content.append("# JColt Test Report\n")
        
        # Add summary
        md_content.append("## Summary\n")
        md_content.append("| Metric | Value |")
        md_content.append("|--------|-------|")
        md_content.append(f"| Total Tests | {self.data['summary']['total']} |")
        md_content.append(f"| Passed | {self.data['summary']['passed']} |")
        md_content.append(f"| Failed | {self.data['summary']['failed']} |")
        md_content.append(f"| Pass Rate | {self.data['summary']['pass_rate']}% |\n")
        
        # Add test details
        md_content.append("## Test Details\n")
        for model, tests in self.data['tests'].items():
            md_content.append(f"### {model}\n")
            md_content.append("| Test | Result | Description |")
            md_content.append("|------|--------|-------------|")
            for test in tests:
                result = "✅" if test['pass'] else "❌"
                md_content.append(f"| {test['name']} | {result} | {test['description']} |")
            md_content.append("\n")
            
        return "\n".join(md_content) 