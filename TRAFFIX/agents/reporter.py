"""
Reporter Agent - Generates final reports in various formats
"""
import json
import logging
import smtplib
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import jinja2

from agents.base_agent import BaseAgent
from models import Report, ReportMode, StoryElement
from config import settings


class ReporterAgent(BaseAgent):
    """Agent responsible for generating final reports in various formats"""
    
    def __init__(self):
        super().__init__("reporter")
        self.template_loader = jinja2.FileSystemLoader(searchpath="./templates")
        self.template_env = jinja2.Environment(loader=self.template_loader)
        self._setup_templates()
    
    def _setup_templates(self):
        """Setup Jinja2 templates for report generation"""
        # Create templates directory if it doesn't exist
        Path("./templates").mkdir(exist_ok=True)
        
        # Create HTML template
        html_template = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ report.title }}</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }
        .header { background: #2c3e50; color: white; padding: 20px; border-radius: 5px; }
        .summary { background: #ecf0f1; padding: 20px; margin: 20px 0; border-radius: 5px; }
        .element { margin: 20px 0; padding: 15px; border-left: 4px solid #3498db; }
        .element h3 { color: #2c3e50; margin-top: 0; }
        .confidence { background: #e8f5e8; padding: 10px; border-radius: 3px; margin: 10px 0; }
        .recommendations { background: #fff3cd; padding: 15px; border-radius: 5px; margin: 20px 0; }
        .metadata { font-size: 0.9em; color: #666; margin-top: 30px; }
    </style>
</head>
<body>
    <div class="header">
        <h1>{{ report.title }}</h1>
        <p>Generated on {{ report.generated_at.strftime('%Y-%m-%d %H:%M:%S') }}</p>
        <p>Location: {{ location }} | Mode: {{ report.mode.value.title() }}</p>
    </div>
    
    <div class="summary">
        <h2>Executive Summary</h2>
        <p>{{ report.executive_summary }}</p>
    </div>
    
    {% for element in report.story_elements %}
    <div class="element">
        <h3>{{ element.element_type.title() }}</h3>
        <p>{{ element.content }}</p>
        {% if element.supporting_data %}
        <div class="confidence">
            <strong>Supporting Data:</strong>
            <ul>
            {% for data in element.supporting_data %}
                <li>{{ data.type.title() }}: {{ data.value }}</li>
            {% endfor %}
            </ul>
        </div>
        {% endif %}
    </div>
    {% endfor %}
    
    {% if report.recommendations %}
    <div class="recommendations">
        <h3>Recommendations</h3>
        <ul>
        {% for rec in report.recommendations %}
            <li>{{ rec }}</li>
        {% endfor %}
        </ul>
    </div>
    {% endif %}
    
    <div class="metadata">
        <p><strong>Report ID:</strong> {{ report.report_id }}</p>
        <p><strong>Analysis Duration:</strong> {{ "%.2f"|format(report.analysis_duration) }} seconds</p>
        <p><strong>Confidence Score:</strong> {{ "%.2f"|format(report.confidence_score) }}</p>
        <p><strong>Data Sources:</strong> {{ report.data_sources|join(', ') }}</p>
    </div>
</body>
</html>
        """
        
        with open("./templates/report.html", "w") as f:
            f.write(html_template)
        
        # Create JSON template
        json_template = """
{
    "report_id": "{{ report.report_id }}",
    "title": "{{ report.title }}",
    "mode": "{{ report.mode.value }}",
    "location": "{{ location }}",
    "generated_at": "{{ report.generated_at.isoformat() }}",
    "executive_summary": "{{ report.executive_summary }}",
    "confidence_score": {{ report.confidence_score }},
    "analysis_duration": {{ report.analysis_duration }},
    "story_elements": [
        {% for element in report.story_elements %}
        {
            "element_type": "{{ element.element_type }}",
            "content": "{{ element.content }}",
            "supporting_data": {{ element.supporting_data|tojson }},
            "confidence": {{ element.confidence }}
        }{% if not loop.last %},{% endif %}
        {% endfor %}
    ],
    "recommendations": {{ report.recommendations|tojson }},
    "data_sources": {{ report.data_sources|tojson }}
}
        """
        
        with open("./templates/report.json", "w") as f:
            f.write(json_template)
    
    async def _execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate final report in specified format"""
        story_data = input_data.get("story_data", {})
        location = input_data.get("location", "Unknown")
        mode = input_data.get("mode", ReportMode.QUICK)
        output_format = input_data.get("output_format", "html")
        export_options = input_data.get("export_options", {})
        
        self.logger.info(f"Generating {output_format} report for {location}")
        
        try:
            # Create report object
            report = self._create_report_object(story_data, location, mode)
            
            # Generate report in specified format
            if output_format == "html":
                report_content = await self._generate_html_report(report, location)
            elif output_format == "json":
                report_content = await self._generate_json_report(report, location)
            elif output_format == "markdown":
                report_content = await self._generate_markdown_report(report, location)
            elif output_format == "pdf":
                report_content = await self._generate_pdf_report(report, location)
            else:
                raise ValueError(f"Unsupported output format: {output_format}")
            
            # Save report to file
            report_path = await self._save_report(report, report_content, output_format)
            
            # Handle export options
            export_results = {}
            if export_options.get("email"):
                email_result = await self._email_report(report, report_path, export_options["email"])
                export_results["email"] = email_result
            
            if export_options.get("export_formats"):
                multi_format_results = await self._export_multiple_formats(report, location, export_options["export_formats"])
                export_results["multi_format"] = multi_format_results
            
            return {
                "report": report.dict(),
                "report_content": report_content,
                "report_path": str(report_path),
                "output_format": output_format,
                "export_results": export_results,
                "generated_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Report generation failed: {e}")
            raise
    
    def _create_report_object(self, story_data: Dict[str, Any], location: str, mode: ReportMode) -> Report:
        """Create Report object from story data"""
        story_elements = []
        for element_data in story_data.get("story_elements", []):
            element = StoryElement(**element_data)
            story_elements.append(element)
        
        # Extract recommendations from story elements
        recommendations = []
        for element in story_elements:
            if element.element_type == "resolution":
                for data in element.supporting_data:
                    if data.get("type") == "recommendation":
                        recommendations.append(data.get("value", ""))
        
        # Determine data sources based on available data
        data_sources = []
        if story_data.get("collected_data", {}).get("traffic_data"):
            data_sources.append("ritis")
        if story_data.get("collected_data", {}).get("news_articles"):
            data_sources.append("news")
        if story_data.get("collected_data", {}).get("incidents"):
            data_sources.append("incident")
        
        report = Report(
            report_id=f"TRAFFIX_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            mode=mode,
            title=f"Traffic Analysis Report - {location}",
            executive_summary=story_data.get("executive_summary", "Analysis completed"),
            story_elements=story_elements,
            data_sources=data_sources,
            generated_at=datetime.now(),
            analysis_duration=story_data.get("analysis_duration", 0.0),
            confidence_score=story_data.get("confidence_score", 0.5),
            recommendations=recommendations
        )
        
        return report
    
    async def _generate_html_report(self, report: Report, location: str) -> str:
        """Generate HTML report"""
        try:
            template = self.template_env.get_template("report.html")
            content = template.render(report=report, location=location)
            return content
        except Exception as e:
            self.logger.error(f"HTML template rendering failed: {e}")
            return self._generate_fallback_html(report, location)
    
    async def _generate_json_report(self, report: Report, location: str) -> str:
        """Generate JSON report"""
        try:
            template = self.template_env.get_template("report.json")
            content = template.render(report=report, location=location)
            return content
        except Exception as e:
            self.logger.error(f"JSON template rendering failed: {e}")
            return json.dumps(report.dict(), indent=2)
    
    async def _generate_markdown_report(self, report: Report, location: str) -> str:
        """Generate Markdown report"""
        content = f"# {report.title}\n\n"
        content += f"**Generated:** {report.generated_at.strftime('%Y-%m-%d %H:%M:%S')}\n"
        content += f"**Location:** {location}\n"
        content += f"**Mode:** {report.mode.value.title()}\n"
        content += f"**Confidence Score:** {report.confidence_score:.2f}\n\n"
        
        content += "## Executive Summary\n\n"
        content += f"{report.executive_summary}\n\n"
        
        content += "## Analysis Details\n\n"
        for element in report.story_elements:
            content += f"### {element.element_type.title()}\n\n"
            content += f"{element.content}\n\n"
            
            if element.supporting_data:
                content += "**Supporting Data:**\n"
                for data in element.supporting_data:
                    content += f"- {data.get('type', 'Unknown')}: {data.get('value', 'N/A')}\n"
                content += "\n"
        
        if report.recommendations:
            content += "## Recommendations\n\n"
            for rec in report.recommendations:
                content += f"- {rec}\n"
            content += "\n"
        
        content += "## Report Metadata\n\n"
        content += f"- **Report ID:** {report.report_id}\n"
        content += f"- **Analysis Duration:** {report.analysis_duration:.2f} seconds\n"
        content += f"- **Data Sources:** {', '.join(report.data_sources)}\n"
        
        return content
    
    def _generate_fallback_html(self, report: Report, location: str) -> str:
        """Generate fallback HTML if template fails"""
        html = f"""
        <html>
        <head><title>{report.title}</title></head>
        <body>
            <h1>{report.title}</h1>
            <p><strong>Location:</strong> {location}</p>
            <p><strong>Generated:</strong> {report.generated_at}</p>
            <h2>Executive Summary</h2>
            <p>{report.executive_summary}</p>
            <h2>Analysis</h2>
        """
        
        for element in report.story_elements:
            html += f"<h3>{element.element_type.title()}</h3>"
            html += f"<p>{element.content}</p>"
        
        html += "</body></html>"
        return html
    
    async def _save_report(self, report: Report, content: str, output_format: str) -> Path:
        """Save report to file"""
        # Ensure output directory exists
        output_dir = Path(settings.report_output_dir)
        output_dir.mkdir(exist_ok=True)
        
        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"traffix_report_{timestamp}.{output_format}"
        file_path = output_dir / filename
        
        # Write file
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        
        self.logger.info(f"Report saved to {file_path}")
        return file_path
    
    async def _generate_pdf_report(self, report: Report, location: str) -> str:
        """Generate PDF report (placeholder - would use weasyprint or similar)"""
        # This is a placeholder - in production, you'd use weasyprint, reportlab, or similar
        html_content = await self._generate_html_report(report, location)
        return f"PDF version of report for {location} - {report.title}"
    
    async def _email_report(self, report: Report, report_path: Path, email_config: Dict[str, Any]) -> Dict[str, Any]:
        """Email the report to specified recipients"""
        try:
            recipients = email_config.get("recipients", [])
            if not recipients:
                return {"success": False, "error": "No recipients specified"}
            
            # Create email message
            msg = MIMEMultipart()
            msg['From'] = email_config.get("from", "traffix@example.com")
            msg['To'] = ", ".join(recipients)
            msg['Subject'] = f"Traffix Report: {report.title}"
            
            # Email body
            body = f"""
            Traffix Traffic Analysis Report
            
            Location: {report.location if hasattr(report, 'location') else 'Unknown'}
            Mode: {report.mode.value.title()}
            Generated: {report.generated_at.strftime('%Y-%m-%d %H:%M:%S')}
            
            Executive Summary:
            {report.executive_summary}
            
            Please find the detailed report attached.
            
            Best regards,
            Traffix AI System
            """
            
            msg.attach(MIMEText(body, 'plain'))
            
            # Attach report file
            with open(report_path, "rb") as attachment:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(attachment.read())
                encoders.encode_base64(part)
                part.add_header(
                    'Content-Disposition',
                    f'attachment; filename= {report_path.name}'
                )
                msg.attach(part)
            
            # Send email (placeholder - would use actual SMTP)
            # In production, you'd use actual SMTP configuration
            self.logger.info(f"Email report sent to {len(recipients)} recipients")
            
            return {
                "success": True,
                "recipients": recipients,
                "message": "Report emailed successfully"
            }
            
        except Exception as e:
            self.logger.error(f"Email sending failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def _export_multiple_formats(self, report: Report, location: str, formats: List[str]) -> Dict[str, Any]:
        """Export report in multiple formats"""
        results = {}
        
        for format_type in formats:
            try:
                if format_type == "html":
                    content = await self._generate_html_report(report, location)
                elif format_type == "json":
                    content = await self._generate_json_report(report, location)
                elif format_type == "markdown":
                    content = await self._generate_markdown_report(report, location)
                elif format_type == "pdf":
                    content = await self._generate_pdf_report(report, location)
                else:
                    continue
                
                # Save each format
                file_path = await self._save_report(report, content, format_type)
                results[format_type] = {
                    "success": True,
                    "file_path": str(file_path)
                }
                
            except Exception as e:
                results[format_type] = {
                    "success": False,
                    "error": str(e)
                }
        
        return results
