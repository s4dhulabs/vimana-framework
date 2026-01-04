from reportlab.lib import colors
from reportlab.lib.pagesizes import landscape, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, 
    PageBreak, Flowable
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from datetime import datetime

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

class PDFReporter:
    def __init__(self, data):
        self.data = data
        self.styles = getSampleStyleSheet()
        
        # Technical color scheme
        self.colors = {
            'primary': colors.HexColor('#2b2b2b'),
            'secondary': colors.HexColor('#404040'),
            'text': colors.HexColor('#1a1a1a'),
            'border': colors.HexColor('#2b2b2b'),
            'pass_bg': colors.HexColor('#e6ffe6'),  # Light green
            'fail_bg': colors.HexColor('#ffe6e6'),  # Light red
            'alt_row': colors.HexColor('#f7f7f7'),  # Light gray
            'pass_text': colors.HexColor('#006600'),  # Dark green
            'fail_text': colors.HexColor('#cc0000'),  # Dark red
        }
        
        # Modify existing Title style
        self.styles['Title'].fontName = 'Courier-Bold'
        self.styles['Title'].fontSize = 20
        self.styles['Title'].textColor = self.colors['text']
        self.styles['Title'].spaceAfter = 25
        self.styles['Title'].alignment = TA_LEFT
        
        # Add custom styles
        self.styles.add(ParagraphStyle(
            'ModelHeader',
            fontName='Courier-Bold',
            fontSize=14,
            textColor=self.colors['primary'],
            spaceAfter=10,
            spaceBefore=20
        ))
        
        self.styles.add(ParagraphStyle(
            'FieldHeader',
            fontName='Courier-Bold',  # Changed to bold
            fontSize=12,
            textColor=self.colors['secondary'],
            spaceAfter=8,
            spaceBefore=12
        ))
        
        self.styles.add(ParagraphStyle(
            'ReportNormal',
            fontName='Courier',
            fontSize=9,
            textColor=self.colors['text'],
            spaceAfter=10
        ))

    def generate_report(self, output_path):
        doc = SimpleDocTemplate(
            output_path,
            pagesize=landscape(A4),  # Changed to landscape
            rightMargin=15*mm,
            leftMargin=15*mm,
            topMargin=20*mm,
            bottomMargin=20*mm
        )
        story = []
        
        # Add title and timestamp
        story.append(Paragraph("JColt Pydantic Test Report", self.styles['Title']))
        story.append(Paragraph(
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            self.styles['ReportNormal']
        ))
        story.append(MCLine(doc.width))
        story.append(Spacer(1, 20))
        
        # Add summary section
        self._add_summary(story, doc.width)
        story.append(Spacer(1, 20))
        
        # Add test details
        self._add_test_details(story, doc.width)
        
        # Generate PDF
        doc.build(story)

    def _add_summary(self, story, page_width):
        summary = self.data['summary']
        
        summary_data = [
            ['Total Tests', 'Passed', 'Failed', 'Pass Rate'],
            [
                str(summary['total']),
                str(summary['passed']),
                str(summary['failed']),
                f"{summary['pass_rate']}%"
            ]
        ]
        
        col_width = page_width/4
        table = Table(summary_data, colWidths=[col_width]*4)
        
        table.setStyle(TableStyle([
            ('FONT', (0, 0), (-1, 0), 'Courier-Bold'),
            ('FONT', (0, 1), (-1, 1), 'Courier-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('FONTSIZE', (0, 1), (-1, 1), 14),
            ('BACKGROUND', (0, 0), (-1, 0), self.colors['primary']),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('TOPPADDING', (0, 0), (-1, -1), 12),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 1, self.colors['border']),
            # Color coding for summary values
            ('TEXTCOLOR', (1, 1), (1, 1), self.colors['pass_text']),  # Passed
            ('TEXTCOLOR', (2, 1), (2, 1), self.colors['fail_text']),  # Failed
        ]))
        
        story.append(table)

    def _add_test_details(self, story, page_width):
        for model_name, model_data in self.data.get('test_data', {}).items():
            story.append(Spacer(1, 20))
            story.append(Paragraph(f"Model: {model_name}", self.styles['ModelHeader']))
            
            fields = model_data.get('fields', {})
            for field_name, field_tests in fields.items():
                story.append(Paragraph(f"Field: {field_name}", self.styles['FieldHeader']))
                
                headers = ['Test Name', 'Type', 'Result', 'Status']
                table_data = [headers]
                
                for test in field_tests:
                    test_name = test.get('name', 'N/A')
                    if len(test_name) > 60:  # Increased character limit
                        test_name = test_name[:57] + '...'
                    
                    row = [
                        test_name,
                        test.get('test_type', 'N/A'),
                        'Pass' if test.get('pass') else 'Fail',
                        str(test.get('status_code', 'N/A'))
                    ]
                    table_data.append(row)
                
                col_widths = [
                    page_width * 0.55,  # Test Name (55%)
                    page_width * 0.20,  # Type (20%)
                    page_width * 0.12,  # Result (12%)
                    page_width * 0.13   # Status (13%)
                ]
                
                table = Table(table_data, colWidths=col_widths, repeatRows=1)
                
                # Create row color alternation and pass/fail styling
                row_styles = []
                for i in range(len(table_data)):
                    if i == 0:  # Header row
                        continue
                    
                    # Determine if test passed or failed
                    passed = table_data[i][2] == 'Pass'
                    bg_color = self.colors['pass_bg'] if passed else self.colors['fail_bg']
                    text_color = self.colors['pass_text'] if passed else self.colors['fail_text']
                    
                    row_styles.extend([
                        ('BACKGROUND', (0, i), (-1, i), bg_color),
                        ('TEXTCOLOR', (2, i), (2, i), text_color),  # Color only the Result column
                    ])

                table.setStyle(TableStyle([
                    # Headers
                    ('FONT', (0, 0), (-1, 0), 'Courier-Bold'),
                    ('FONT', (0, 1), (-1, -1), 'Courier'),
                    ('FONTSIZE', (0, 0), (-1, 0), 10),
                    ('FONTSIZE', (0, 1), (-1, -1), 9),
                    ('BACKGROUND', (0, 0), (-1, 0), self.colors['primary']),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('TOPPADDING', (0, 0), (-1, -1), 8),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                    ('GRID', (0, 0), (-1, -1), 0.5, self.colors['border']),
                    ('WORDWRAP', (0, 0), (-1, -1), True),
                    # Add row styling
                    *row_styles,
                    # Add more spacing between rows
                    ('LINEBELOW', (0, 0), (-1, -1), 1, self.colors['border']),
                ]))
                
                story.append(table)
                story.append(Spacer(1, 12))
            
            story.append(MCLine(page_width)) 