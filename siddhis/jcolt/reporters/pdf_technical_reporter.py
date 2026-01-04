from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, 
    PageBreak, Flowable, Image
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from datetime import datetime
import json

class MCLine(Flowable):
    """Custom flowable for drawing a modern line"""
    def __init__(self, width, height=0.25):
        Flowable.__init__(self)
        self.width = width
        self.height = height
        
    def draw(self):
        self.canv.setStrokeColor(colors.HexColor('#2b2b2b'))
        self.canv.setLineWidth(self.height)
        self.canv.line(0, 0, self.width, 0)

class PDFTechnicalReporter:
    def __init__(self, data):
        self.data = data
        self.styles = getSampleStyleSheet()
        
        # Technical color scheme
        self.colors = {
            'primary': colors.HexColor('#2b2b2b'),
            'secondary': colors.HexColor('#404040'),
            'text': colors.HexColor('#1a1a1a'),
            'border': colors.HexColor('#2b2b2b'),
            'code_bg': colors.HexColor('#f5f5f5'),
            'success': colors.HexColor('#006600'),
            'error': colors.HexColor('#cc0000'),
            'header_bg': colors.HexColor('#f0f0f0'),
        }
        
        self._setup_styles()

    def _setup_styles(self):
        """Setup custom styles for the technical report"""
        # Cover page styles
        self.styles.add(ParagraphStyle(
            'CoverTitle',
            fontName='Courier-Bold',
            fontSize=24,
            textColor=self.colors['primary'],
            spaceAfter=30,
            alignment=TA_CENTER
        ))
        
        self.styles.add(ParagraphStyle(
            'CoverInfo',
            fontName='Courier',
            fontSize=12,
            textColor=self.colors['secondary'],
            spaceAfter=12,
            alignment=TA_CENTER
        ))
        
        # Section styles
        self.styles.add(ParagraphStyle(
            'SectionHeader',
            fontName='Courier-Bold',
            fontSize=16,
            textColor=self.colors['primary'],
            spaceBefore=20,
            spaceAfter=10
        ))
        
        # Code block style
        self.styles.add(ParagraphStyle(
            'CodeBlock',
            fontName='Courier',
            fontSize=8,
            textColor=self.colors['text'],
            backColor=self.colors['code_bg'],
            leftIndent=20,
            rightIndent=20,
            spaceAfter=12,
            spaceBefore=12
        ))

    def generate_report(self, output_path):
        doc = SimpleDocTemplate(
            output_path,
            pagesize=A4,
            rightMargin=25*mm,
            leftMargin=25*mm,
            topMargin=20*mm,
            bottomMargin=20*mm
        )
        story = []
        
        # Generate cover page
        self._add_cover_page(story)
        story.append(PageBreak())
        
        # Add table of contents (placeholder for now)
        self._add_toc(story)
        story.append(PageBreak())
        
        # Add test environment details
        self._add_environment_details(story)
        story.append(PageBreak())
        
        # Add detailed test results
        self._add_detailed_results(story)
        
        # Generate PDF
        doc.build(story)

    def _add_cover_page(self, story):
        """Generate the cover page with project and test information"""
        # Title
        story.append(Paragraph("JColt Technical Analysis Report", self.styles['CoverTitle']))
        story.append(Spacer(1, 30))
        
        # Basic information table
        info_data = [
            ['Report Type:', 'Technical Detail Report'],
            ['Generated:', datetime.now().strftime('%Y-%m-%d %H:%M:%S')],
            ['Framework:', 'JColt Pydantic Testing Framework'],
            ['Version:', '1.0.0'],  # You might want to make this dynamic
            ['Total Tests:', str(self.data['summary']['total'])],
            ['Pass Rate:', f"{self.data['summary']['pass_rate']}%"]
        ]
        
        table = Table(info_data, colWidths=[120, 300])
        table.setStyle(TableStyle([
            ('FONT', (0, 0), (-1, -1), 'Courier'),
            ('FONT', (0, 0), (0, -1), 'Courier-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('TEXTCOLOR', (0, 0), (-1, -1), self.colors['text']),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        story.append(table)

    def _add_toc(self, story):
        """Add table of contents"""
        story.append(Paragraph("Table of Contents", self.styles['SectionHeader']))
        # TOC implementation would go here
        # For now, just add placeholder sections
        sections = [
            "1. Test Environment",
            "2. Test Configuration",
            "3. Detailed Test Results",
            "4. Authentication Details",
            "5. Error Analysis"
        ]
        for section in sections:
            story.append(Paragraph(section, self.styles['CodeBlock']))

    def _add_environment_details(self, story):
        """Add detailed environment information"""
        story.append(Paragraph("Test Environment Details", self.styles['SectionHeader']))
        
        # Add environment information
        env_data = [
            ['Operating System:', 'Linux'],  # You might want to make these dynamic
            ['Python Version:', '3.8'],
            ['Dependencies:', 'pydantic, requests, reportlab'],
            ['Test Framework:', 'JColt'],
            ['Configuration File:', 'jcolt.yaml']
        ]
        
        table = Table(env_data, colWidths=[150, 300])
        table.setStyle(TableStyle([
            ('FONT', (0, 0), (-1, -1), 'Courier'),
            ('FONT', (0, 0), (0, -1), 'Courier-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BACKGROUND', (0, 0), (-1, -1), self.colors['code_bg']),
            ('TEXTCOLOR', (0, 0), (-1, -1), self.colors['text']),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('GRID', (0, 0), (-1, -1), 1, self.colors['border']),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        story.append(table)

    def _add_detailed_results(self, story):
        """Add detailed test results including request/response data"""
        story.append(Paragraph("Detailed Test Results", self.styles['SectionHeader']))
        
        for model_name, model_data in self.data.get('test_data', {}).items():
            story.append(Paragraph(f"Model: {model_name}", self.styles['SectionHeader']))
            
            fields = model_data.get('fields', {})
            for field_name, field_tests in fields.items():
                story.append(Paragraph(f"Field: {field_name}", self.styles['CodeBlock']))
                
                for test in field_tests:
                    self._add_test_details(story, test)
                    story.append(MCLine(470))
                    story.append(Spacer(1, 10))

    def _add_test_details(self, story, test):
        """Add detailed information for a single test"""
        # Test header
        test_header = [
            ['Test Name:', test.get('name', 'N/A')],
            ['Test Type:', test.get('test_type', 'N/A')],
            ['Status:', 'Pass' if test.get('pass') else 'Fail'],
            ['Status Code:', str(test.get('status_code', 'N/A'))]
        ]
        
        table = Table(test_header, colWidths=[100, 370])
        table.setStyle(TableStyle([
            ('FONT', (0, 0), (-1, -1), 'Courier'),
            ('FONT', (0, 0), (0, -1), 'Courier-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BACKGROUND', (0, 0), (-1, -1), self.colors['header_bg']),
            ('TEXTCOLOR', (0, 0), (-1, -1), self.colors['text']),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        story.append(table)
        story.append(Spacer(1, 10))
        
        # Request details
        if 'request' in test:
            story.append(Paragraph("Request Details:", self.styles['CodeBlock']))
            request_data = json.dumps(test['request'], indent=2)
            story.append(Paragraph(request_data, self.styles['CodeBlock']))
        
        # Response details
        if 'response' in test:
            story.append(Paragraph("Response Details:", self.styles['CodeBlock']))
            response_data = json.dumps(test['response'], indent=2)
            story.append(Paragraph(response_data, self.styles['CodeBlock']))
        
        # Authentication details if present
        if 'auth' in test:
            story.append(Paragraph("Authentication:", self.styles['CodeBlock']))
            auth_data = json.dumps(test['auth'], indent=2)
            story.append(Paragraph(auth_data, self.styles['CodeBlock']))
        
        # Error details if present
        if not test.get('pass') and 'error' in test:
            story.append(Paragraph("Error Details:", self.styles['CodeBlock']))
            error_data = json.dumps(test['error'], indent=2)
            story.append(Paragraph(error_data, self.styles['CodeBlock'])) 