import re
import json
import tempfile
from typing import List, Dict, Any, Optional
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from app.models import TimingPath
from io import BytesIO

class STAParser:
    def __init__(self, sta_report: str):
        self.report = sta_report

    def parse(self) -> List[TimingPath]:
        paths = []
        blocks = self.report.strip().split("Startpoint:")

        for block in blocks[1:]:
            path_data = self._parse_block(block)
            if path_data:
                try:
                    paths.append(TimingPath(**path_data))
                except Exception as e:
                    print(f"Error parsing block: {e}")
                    continue

        return paths

    def _parse_block(self, block: str) -> Optional[Dict[str, Any]]:
        lines = block.strip().splitlines()
        if not lines:
            return None

        startpoint = lines[0].strip()
        endpoint = ""
        clock = ""
        path_type = ""
        data_arrival = None
        data_required = None
        slack = None
        status = "MET"
        logic_chain = []

        for line in lines:
            line = line.strip()
            if line.startswith("Endpoint:"):
                endpoint = line.replace("Endpoint:", "").strip()
            elif line.startswith("Path Group:"):
                clock = line.replace("Path Group:", "").strip()
            elif line.startswith("Path Type:"):
                path_type = line.replace("Path Type:", "").strip()
            elif "data arrival time" in line and data_arrival is None:
                try:
                    data_arrival = float(line.split()[0])
                except (ValueError, IndexError):
                    pass
            elif "data required time" in line and data_required is None:
                try:
                    data_required = float(line.split()[0])
                except (ValueError, IndexError):
                    pass
            elif "slack" in line.lower():
                parts = line.split()
                try:
                    slack = float(parts[0])
                    if "violated" in line.lower():
                        status = "VIOLATED"
                except (ValueError, IndexError):
                    pass
            elif re.search(r"\s+[0-9]", line) and ("v " in line or "^ " in line):
                parts = line.split()
                if len(parts) >= 3:
                    try:
                        delay = float(parts[0])
                    except ValueError:
                        delay = 0.0
                    description = " ".join(parts[2:])
                    logic_chain.append({"cell": description, "delay": delay})

        return {
            "startpoint": startpoint,
            "endpoint": endpoint,
            "clock": clock,
            "path_type": path_type,
            "data_arrival_time": data_arrival,
            "data_required_time": data_required,
            "slack": slack,
            "status": status,
            "logic_chain": logic_chain
        }


def generate_pdf_report(analyses: List[Dict], output_path: str):
    """Generate PDF report from analysis results"""
    doc = SimpleDocTemplate(output_path, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []

    # Title
    title_style = ParagraphStyle(
        'Title',
        parent=styles['Heading1'],
        fontSize=16,
        spaceAfter=30
    )
    story.append(Paragraph("Timing Violation Analysis Report", title_style))
    story.append(Spacer(1, 12))

    # Summary
    violated = sum(1 for a in analyses if a.get('status') == 'VIOLATED')
    story.append(Paragraph(f"Total Paths Analyzed: {len(analyses)}", styles['Normal']))
    story.append(Paragraph(f"Violated Paths: {violated}", styles['Normal']))
    story.append(Spacer(1, 20))

    # Detailed analysis
    for i, analysis in enumerate(analyses, 1):
        if analysis.get('status') == 'VIOLATED':
            story.append(Paragraph(f"Violation {i}: {analysis.get('startpoint')} → {analysis.get('endpoint')}",
                                   styles['Heading2']))

            data = [
                ["Slack", f"{analysis.get('slack', 'N/A')} ns"],
                ["Path Type", analysis.get('path_type', 'N/A')],
                ["Severity", analysis.get('severity', 'N/A')],
                ["Root Cause", analysis.get('root_cause', 'N/A')]
            ]

            table = Table(data, colWidths=[100, 400])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))

            story.append(table)
            story.append(Spacer(1, 12))

            # Suggestions
            story.append(Paragraph("Recommended Fixes:", styles['Heading3']))
            for suggestion in analysis.get('suggestions', []):
                story.append(
                    Paragraph(f"• {suggestion.get('fix')} ({suggestion.get('priority')} priority)", styles['Normal']))
                story.append(Paragraph(f"  Explanation: {suggestion.get('explanation')}", styles['Italic']))

            story.append(Spacer(1, 20))

    doc.build(story)
    return output_path

def generate_pdf_bytes(analyses: List[Dict]) -> bytes:
    """Generate PDF report and return as bytes (for Streamlit compatibility)"""
    buffer = BytesIO()

    # Reuse your existing PDF generation logic but write to buffer
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []

    # Title
    title_style = ParagraphStyle(
        'Title',
        parent=styles['Heading1'],
        fontSize=16,
        spaceAfter=30
    )
    story.append(Paragraph("Timing Violation Analysis Report", title_style))
    story.append(Spacer(1, 12))

    # Summary
    violated = sum(1 for a in analyses if a.get('status') == 'VIOLATED')
    total = len(analyses)

    story.append(Paragraph(f"Report Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}", styles['Normal']))
    story.append(Paragraph(f"Total Paths Analyzed: {total}", styles['Normal']))
    story.append(Paragraph(f"Violated Paths: {violated}", styles['Normal']))
    story.append(Spacer(1, 20))

    # Detailed analysis for violations
    if violated > 0:
        story.append(Paragraph("Timing Violations Analysis", styles['Heading2']))
        story.append(Spacer(1, 12))

        for i, analysis in enumerate(analyses, 1):
            if analysis.get('status') == 'VIOLATED':
                story.append(Paragraph(f"Violation {i}: {analysis.get('startpoint')} → {analysis.get('endpoint')}",
                                       styles['Heading3']))

                # Violation details table
                data = [
                    ["Parameter", "Value"],
                    ["Slack", f"{analysis.get('slack', 'N/A')} ns"],
                    ["Path Type", analysis.get('path_type', 'N/A')],
                    ["Severity", analysis.get('severity', 'N/A').upper()],
                    ["Estimated Effort", analysis.get('estimated_effort', 'N/A').upper()]
                ]

                table = Table(data, colWidths=[120, 380])
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))

                story.append(table)
                story.append(Spacer(1, 12))

                # Root cause
                story.append(Paragraph("Root Cause:", styles['Heading4']))
                story.append(Paragraph(analysis.get('root_cause', 'N/A'), styles['Normal']))
                story.append(Spacer(1, 8))

                # Suggestions
                story.append(Paragraph("Recommended Fixes:", styles['Heading4']))
                suggestions = analysis.get('suggestions', [])
                for suggestion in suggestions:
                    priority = suggestion.get('priority', '').upper()
                    story.append(Paragraph(f"• {suggestion.get('fix')} ({priority} priority)", styles['Normal']))
                    story.append(Paragraph(f"  Explanation: {suggestion.get('explanation')}", styles['Italic']))
                    story.append(Spacer(1, 4))

                story.append(Spacer(1, 20))

    # Build the PDF
    doc.build(story)

    # Get the bytes and reset buffer
    pdf_bytes = buffer.getvalue()
    buffer.close()

    return pdf_bytes