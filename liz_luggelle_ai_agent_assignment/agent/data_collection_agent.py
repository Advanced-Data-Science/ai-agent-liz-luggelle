import os
import json
import time
import random
import logging
import requests
from datetime import datetime
from dotenv import load_dotenv
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.enums import TA_CENTER, TA_LEFT

class DataCollectionAgent:
    def __init__(self, config_file):
        """Initialize agent with configuration"""
        load_dotenv()  # Load environment variables from .env
        self.config = self.load_config(config_file)
        self.data_store = []
        self.collection_stats = {
            'start_time': datetime.now(),
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'data_quality_scores': [],
            'issues_encountered': []  # Track issues for PDF report
        }
        # delay because i'm feeling nice
        self.delay_multiplier = 1.0
        # create subdirectories for logs & data
        self.setup_directories()
        self.setup_logging()

    def setup_directories(self):
        """Ensure required directories exist"""
        os.makedirs("../data/raw", exist_ok=True)
        os.makedirs("../data/processed", exist_ok=True)
        os.makedirs("../data/metadata", exist_ok=True)
        os.makedirs("../logs", exist_ok=True)
        os.makedirs("../reports", exist_ok=True)

    def setup_logging(self):
        """Setup logging for the agent"""
        log_file = self.config.get("logging", {}).get("log_file", "../logs/collection.log")
        log_level = self.config.get("logging", {}).get("level", "INFO").upper()
        logging.basicConfig(
            level=getattr(logging, log_level, logging.INFO),
            format="%(asctime)s - %(levelname)s - %(message)s",
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

    def load_config(self, config_file):
        """Load collection parameters from JSON config and resolve env keys"""
        try:
            with open(config_file, "r") as f:
                cfg = json.load(f)

            # If API key is specified as env var name, load it
            api_cfg = cfg.get("api", {})
            env_var_name = api_cfg.get("api_key_env_var")
            # configure api
            if env_var_name:
                api_key_value = os.getenv(env_var_name)
                if not api_key_value:
                    raise RuntimeError(f"Missing environment variable: {env_var_name}")
                api_cfg["api_key"] = api_key_value
                cfg["api"] = api_cfg

            return cfg
        # error if config not working :(
        except Exception as e:
            raise RuntimeError(f"Failed to load config: {e}")

    def make_api_request(self):
        """Call the API with error handling"""
        self.collection_stats["total_requests"] += 1
        api_cfg = self.config.get("api", {})
        cities = api_cfg.get("cities", []) #load in cities list from config.json

        results = [] # list of city data
        for city in cities:
            try:
                params = {
                    "q": city,
                    "appid": api_cfg.get("api_key"),
                    "units": "metric"
                }
                # make request for each city individually
                response = requests.get(api_cfg["api_url"], params=params, timeout=10)
                response.raise_for_status()
                # append to list (assuming successful)
                results.append(response.json())
                self.collection_stats["successful_requests"] += 1
            # in case the request fails
            except Exception as e:
                self.collection_stats["failed_requests"] += 1
                error_msg = f"API request failed for {city}: {str(e)}"
                self.logger.error(error_msg)
                self.collection_stats['issues_encountered'].append({
                    'timestamp': datetime.now().isoformat(),
                    'type': 'API Request Failure',
                    'city': city,
                    'error': str(e)
                })
        return results if results else None

    def process_data(self, data_list):
        """Extract and clean fields for each city"""
        # array for processed data
        processed = []
        for data in data_list:
            try:
                # distinguish data by city
                city_name = data["name"]
                # create record of weather data
                record = {
                    "time": datetime.now().isoformat(),
                    "city": city_name,
                    "temperature": data["main"]["temp"],
                    "humidity": data["main"]["humidity"],
                    "weather": data["weather"][0]["description"]
                }
                # append record to the list
                processed.append(record)
            # in case processing fails
            except Exception as e:
                error_msg = f"Data processing failed: {str(e)}"
                self.logger.error(error_msg)
                self.collection_stats['issues_encountered'].append({
                    'timestamp': datetime.now().isoformat(),
                    'type': 'Data Processing Error',
                    'error': str(e)
                })
        return processed

    def validate_data(self, records):
        """Check completeness"""
        # incomplete if records blank
        if not records:
            return False
        # incomplete if missing fields
        for rec in records:
            if rec.get("temperature") is None or rec.get("humidity") is None:
                return False
        # otherwise complete
        return True

    def store_data(self, records):
        """Store validated data in raw folder"""
        self.data_store.extend(records)
        raw_path = os.path.join("../data/raw", "collected_data.json")
        with open(raw_path, "w") as f:
            json.dump(self.data_store, f, indent=2)

    def assess_data_quality(self):
        """Evaluate the quality of collected data"""
        if not self.data_store:
            return 0
        # check for data completeness, consistency, accuracy, timeliness - each weighted 1/4
        completeness = 1.0 if all("temperature" in rec for rec in self.data_store) else 0.5
        consistency = 1.0
        accuracy = 1.0
        timeliness = 1.0
        score = (completeness + consistency + accuracy + timeliness) / 4
        # record data quality
        self.collection_stats["data_quality_scores"].append(score)
        return score

    def get_success_rate(self):
        """Check how frequently requests succeed"""
        total = self.collection_stats["total_requests"]
        if total == 0:
            return 1.0
        return self.collection_stats["successful_requests"] / total

    def adjust_strategy(self):
        """Modify collection approach"""
        success_rate = self.get_success_rate()
        # if success rate is poor, increases delay
        if success_rate < 0.5:
            self.delay_multiplier *= 2
            warning_msg = "Low success rate detected. Increasing delay."
            self.logger.warning(warning_msg)
            self.collection_stats['issues_encountered'].append({
                'timestamp': datetime.now().isoformat(),
                'type': 'Strategy Adjustment',
                'action': 'Increased delay multiplier',
                'reason': f'Success rate below 50% ({success_rate:.2%})'
            })
        # if success rate is high, decreases delay
        elif success_rate > 0.9:
            self.delay_multiplier *= 0.8
            self.logger.info("High success rate detected. Decreasing delay.")

    def respectful_delay(self):
        """Wait between API calls"""
        # grab base delay from config
        base_delay = self.config.get("collection", {}).get("base_delay", 1.0)
        # make adjustment (if necessary)
        delay = base_delay * self.delay_multiplier
        jitter = random.uniform(0.5, 1.5)
        time.sleep(delay * jitter)

    def collection_complete(self):
        """Stop after max_requests"""
        max_requests = self.config.get("collection", {}).get("max_requests", 10)
        return self.collection_stats["total_requests"] >= max_requests
    

    def generate_metadata(self): 
        metadata = { 
            "collection_info": { 
                "collection_date": datetime.now().isoformat(), 
                "agent_version": "1.0",
                "collector": "Liz Luggelle",
                "total_records": len(self.data_store) 
            }, 
            "data_sources": [self.config["api"].get("api_url")], 
            "quality_metrics": self.calculate_final_quality_metrics(), 
            "processing_history": ["collected data", "validated data", "stored raw JSON"],
            "variables": { 
                    "time": "ISO timestamp when data was collected", 
                    "city": "Name of the city", 
                    "temperature": "Air temperature in Celsius", 
                    "humidity": "Relative humidity (%)", 
                    "weather": "Short description of weather conditions" 
                } 
        }
        meta_path = os.path.join("../data/metadata", "dataset_metadata.json") 
        with open(meta_path, "w") as f: 
            json.dump(metadata, f, indent=2) 
        self.logger.info(f"Metadata saved: {meta_path}")

    def calculate_final_quality_metrics(self): 
        scores = self.collection_stats.get("data_quality_scores", []) 
        return {"average_score": sum(scores) / max(1, len(scores)), "num_checks": len(scores)}
    
    def generate_quality_report(self): 
        report = { 
            "summary": { 
                "total_records": len(self.data_store), 
                "collection_success_rate": self.get_success_rate(), 
                "overall_quality_score": self.get_overall_quality_score() 
                }, 
            "completeness_analysis": self.analyze_completeness(), 
            "data_distribution": self.analyze_distribution(), 
            "anomaly_detection": self.detect_anomalies(), 
            "recommendations": self.generate_recommendations() 
        }
        # generate JSON report
        json_path = os.path.join("../reports", "quality_report.json") 
        with open(json_path, "w") as f: 
            json.dump(report, f, indent=2)

        text_path = os.path.join("../reports", "quality_report.txt")

        # Generate HTML report
        html_path = os.path.join("../reports", "quality_report.html")
        
        self.generate_html_report(report, html_path)
                
        self.logger.info("Quality reports generated.")
    
    def generate_html_report(self, report, html_path):
        """Generate a visual HTML quality report"""
        success_rate = report["summary"]["collection_success_rate"]
        quality_score = report["summary"]["overall_quality_score"]
        
        # Determine status color
        if quality_score >= 0.8:
            quality_color = "#10b981"
            quality_status = "Excellent"
        elif quality_score >= 0.6:
            quality_color = "#f59e0b"
            quality_status = "Good"
        else:
            quality_color = "#ef4444"
            quality_status = "Needs Improvement"
        
        html_content = f"""<!DOCTYPE html>
<html>
<head>
    <title>Data Collection Quality Report</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            max-width: 1000px;
            margin: 40px auto;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 30px;
        }}
        .metric-card {{
            background: white;
            padding: 20px;
            margin: 15px 0;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .metric-value {{
            font-size: 32px;
            font-weight: bold;
            color: {quality_color};
        }}
        .metric-label {{
            color: #666;
            font-size: 14px;
            text-transform: uppercase;
        }}
        .section {{
            background: white;
            padding: 25px;
            margin: 20px 0;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .section-title {{
            font-size: 20px;
            font-weight: bold;
            margin-bottom: 15px;
            color: #333;
            border-bottom: 2px solid #667eea;
            padding-bottom: 10px;
        }}
        .recommendation {{
            padding: 10px 15px;
            margin: 10px 0;
            background: #f0f9ff;
            border-left: 4px solid #0ea5e9;
            border-radius: 4px;
        }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin: 20px 0;
        }}
        .stat-box {{
            padding: 15px;
            background: #f9fafb;
            border-radius: 6px;
            border: 1px solid #e5e7eb;
        }}
        .anomaly {{
            background: #fef2f2;
            border-left: 4px solid #ef4444;
            padding: 10px;
            margin: 5px 0;
            border-radius: 4px;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Data Collection Quality Report</h1>
        <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <p>Collector: Liz Luggelle</p>
    </div>

    <div class="stats-grid">
        <div class="metric-card">
            <div class="metric-label">Overall Quality Score</div>
            <div class="metric-value">{quality_score:.2%}</div>
            <div style="color: {quality_color}; font-weight: bold; margin-top: 5px;">{quality_status}</div>
        </div>
        <div class="metric-card">
            <div class="metric-label">Collection Success Rate</div>
            <div class="metric-value">{success_rate:.2%}</div>
        </div>
        <div class="metric-card">
            <div class="metric-label">Total Records</div>
            <div class="metric-value">{report["summary"]["total_records"]}</div>
        </div>
    </div>

    <div class="section">
        <div class="section-title">Completeness Analysis</div>
        <div class="stat-box">
            <strong>Missing Values:</strong> {report["completeness_analysis"].get("missing_values", 0)}<br>
            <strong>Completeness Rate:</strong> {report["completeness_analysis"].get("completeness_rate", 0):.2%}
        </div>
    </div>

    <div class="section">
        <div class="section-title">Data Distribution</div>
        {self._format_distribution_html(report["data_distribution"])}
    </div>

    <div class="section">
        <div class="section-title">Anomaly Detection</div>
        {self._format_anomalies_html(report["anomaly_detection"])}
    </div>

    <div class="section">
        <div class="section-title">Recommendations</div>
        {''.join(f'<div class="recommendation">• {rec}</div>' for rec in report["recommendations"])}
    </div>
</body>
</html>"""

        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html_content)

    def _format_distribution_html(self, distribution):
        """Helper to format distribution data for HTML"""
        if not distribution:
            return "<p>No distribution data available.</p>"
        
        return f"""
        <div class="stats-grid">
            <div class="stat-box">
                <strong>Min Temperature:</strong> {distribution.get('min_temp', 'N/A'):.1f}°C
            </div>
            <div class="stat-box">
                <strong>Max Temperature:</strong> {distribution.get('max_temp', 'N/A'):.1f}°C
            </div>
            <div class="stat-box">
                <strong>Average Temperature:</strong> {distribution.get('avg_temp', 'N/A'):.1f}°C
            </div>
        </div>
        """
    
    def _format_anomalies_html(self, anomalies):
        """Helper to format anomalies for HTML"""
        if not anomalies:
            return "<p style='color: #10b981;'>✓ No anomalies detected.</p>"
        
        anomaly_html = f"<p style='color: #ef4444;'>⚠ {len(anomalies)} anomalies detected:</p>"
        for anomaly in anomalies:
            anomaly_html += f"""
            <div class="anomaly">
                <strong>{anomaly.get('city', 'Unknown')}:</strong> 
                Temperature {anomaly.get('temperature', 'N/A')}°C 
                (recorded at {anomaly.get('time', 'N/A')})
            </div>
            """
        return anomaly_html
    
    def generate_pdf_summary(self):
        """Generate a comprehensive PDF summary report"""
        pdf_path = os.path.join("../reports", "collection_summary.pdf")
        doc = SimpleDocTemplate(pdf_path, pagesize=letter)
        styles = getSampleStyleSheet()
        story = []
        
        # Custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#667eea'),
            spaceAfter=30,
            alignment=TA_CENTER
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#764ba2'),
            spaceAfter=12,
            spaceBefore=12
        )
        
        # Title
        story.append(Paragraph("Data Collection Summary Report", title_style))
        story.append(Spacer(1, 0.2*inch))
        
        # Collection Info
        end_time = datetime.now()
        duration = end_time - self.collection_stats['start_time']
        
        info_data = [
            ['Collector:', 'Liz Luggelle'],
            ['Generated:', end_time.strftime('%Y-%m-%d %H:%M:%S')],
            ['Collection Start:', self.collection_stats['start_time'].strftime('%Y-%m-%d %H:%M:%S')],
            ['Collection Duration:', str(duration).split('.')[0]],
            ['API Source:', self.config["api"].get("api_url", "N/A")]
        ]
        
        info_table = Table(info_data, colWidths=[2*inch, 4*inch])
        info_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f3f4f6')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey)
        ]))
        story.append(info_table)
        story.append(Spacer(1, 0.3*inch))
        
        # Total Data Points Section
        story.append(Paragraph("1. Total Data Points Collected", heading_style))
        total_points = len(self.data_store)
        cities_data = {}
        for record in self.data_store:
            city = record.get('city', 'Unknown')
            cities_data[city] = cities_data.get(city, 0) + 1
        
        data_points_info = [
            ['Total Data Points:', str(total_points)],
            ['Unique Cities:', str(len(cities_data))],
            ['Cities Monitored:', ', '.join(cities_data.keys())]
        ]
        
        dp_table = Table(data_points_info, colWidths=[2*inch, 4*inch])
        dp_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#e0e7ff')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey)
        ]))
        story.append(dp_table)
        story.append(Spacer(1, 0.3*inch))
        
        # Success/Failure Rates Section
        story.append(Paragraph("2. Success & Failure Rates", heading_style))
        success_rate = self.get_success_rate()
        failure_rate = 1 - success_rate
        
        rates_data = [
            ['Metric', 'Count', 'Percentage'],
            ['Total API Requests', str(self.collection_stats['total_requests']), '100%'],
            ['Successful Requests', str(self.collection_stats['successful_requests']), f"{success_rate:.1%}"],
            ['Failed Requests', str(self.collection_stats['failed_requests']), f"{failure_rate:.1%}"]
        ]
        
        rates_table = Table(rates_data, colWidths=[2.5*inch, 1.5*inch, 1.5*inch])
        rates_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#667eea')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9fafb')])
        ]))
        story.append(rates_table)
        story.append(Spacer(1, 0.3*inch))
        
        # Quality Metrics Section
        story.append(Paragraph("3. Quality Metrics & Trends", heading_style))
        quality_score = self.get_overall_quality_score()
        completeness = self.analyze_completeness()
        distribution = self.analyze_distribution()
        
        quality_status = "Excellent" if quality_score >= 0.8 else "Good" if quality_score >= 0.6 else "Needs Improvement"
        
        quality_data = [
            ['Overall Quality Score:', f"{quality_score:.2%}", quality_status],
            ['Completeness Rate:', f"{completeness.get('completeness_rate', 0):.2%}", ''],
            ['Missing Values:', str(completeness.get('missing_values', 0)), ''],
        ]
        
        if distribution:
            quality_data.extend([
                ['Temperature Range:', f"{distribution.get('min_temp', 0):.1f}°C - {distribution.get('max_temp', 0):.1f}°C", ''],
                ['Average Temperature:', f"{distribution.get('avg_temp', 0):.1f}°C", '']
            ])
        
        quality_table = Table(quality_data, colWidths=[2.5*inch, 2*inch, 1.5*inch])
        quality_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#dbeafe')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey)
        ]))
        story.append(quality_table)
        story.append(Spacer(1, 0.3*inch))
        
        # Issues Encountered Section
        story.append(Paragraph("4. Issues Encountered", heading_style))
        issues = self.collection_stats.get('issues_encountered', [])
        
        if issues:
            story.append(Paragraph(f"Total Issues: {len(issues)}", styles['Normal']))
            story.append(Spacer(1, 0.1*inch))
            
            issue_types = {}
            for issue in issues:
                issue_type = issue.get('type', 'Unknown')
                issue_types[issue_type] = issue_types.get(issue_type, 0) + 1
            
            issue_summary = [[issue_type, str(count)] for issue_type, count in issue_types.items()]
            issue_summary.insert(0, ['Issue Type', 'Count'])
            
            issue_table = Table(issue_summary, colWidths=[4*inch, 2*inch])
            issue_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#fee2e2')),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey)
            ]))
            story.append(issue_table)
        else:
            story.append(Paragraph("✓ No issues encountered during collection.", styles['Normal']))
        
        story.append(Spacer(1, 0.3*inch))
        
        # Recommendations Section
        story.append(Paragraph("5. Recommendations for Future Collection", heading_style))
        recommendations = self.generate_recommendations()
        
        for i, rec in enumerate(recommendations, 1):
            story.append(Paragraph(f"{i}. {rec}", styles['Normal']))
            story.append(Spacer(1, 0.1*inch))
        
        # Anomalies if any
        anomalies = self.detect_anomalies()
        if anomalies:
            story.append(Spacer(1, 0.2*inch))
            story.append(Paragraph("⚠ Anomalies Detected", heading_style))
            story.append(Paragraph(f"Found {len(anomalies)} temperature anomalies (outside -40°C to 50°C range):", styles['Normal']))
            story.append(Spacer(1, 0.1*inch))
            
            for anomaly in anomalies[:5]:  # Limit to first 5
                story.append(Paragraph(
                    f"• {anomaly.get('city', 'Unknown')}: {anomaly.get('temperature', 'N/A')}°C at {anomaly.get('time', 'N/A')}",
                    styles['Normal']
                ))
        
        # Build PDF
        doc.build(story)
        self.logger.info(f"PDF summary report generated: {pdf_path}")
    
    def get_overall_quality_score(self): 
        scores = self.collection_stats.get("data_quality_scores", []) 
        return sum(scores) / max(1, len(scores))

    def analyze_completeness(self): 
        if not self.data_store: 
            return {"status": "no data"} 
        missing = sum(1 for rec in self.data_store if "temperature" not in rec) 
        return {"missing_values": missing, "completeness_rate": 1 - missing/len(self.data_store)}
    
    def analyze_distribution(self): 
        temps = [rec.get("temperature") for rec in self.data_store if "temperature" in rec] 
        if not temps: 
                return {} 
        return {"min_temp": min(temps), "max_temp": max(temps), "avg_temp": sum(temps)/len(temps)}
    
    def detect_anomalies(self): 
        anomalies = [] 
        for rec in self.data_store: 
            t = rec.get("temperature") 
            if t is not None and (t < -40 or t > 50): 
                anomalies.append(rec) 
        return anomalies
    
    def generate_recommendations(self): 
        recs = [] 
        if self.get_success_rate() < 0.8: 
            recs.append("Increase delay between requests or check API quota.") 
        if len(self.data_store) < 10: 
            recs.append("Extend collection time to gather more data.") 
        
        # Additional recommendations based on issues
        issues = self.collection_stats.get('issues_encountered', [])
        if issues:
            api_failures = sum(1 for i in issues if i.get('type') == 'API Request Failure')
            if api_failures > 5:
                recs.append(f"High number of API failures ({api_failures}). Verify API key and network connectivity.")
        
        anomalies = self.detect_anomalies()
        if anomalies:
            recs.append(f"Review {len(anomalies)} temperature anomalies for data quality issues.")
        
        if not recs: 
            recs.append("Collection successful with no major issues.") 
        return recs

    def generate_final_report(self):
        """Save reports"""
        self.generate_metadata()
        self.generate_quality_report()
        self.generate_pdf_summary()  # Add PDF generation
        self.logger.info("Reports generated: metadata, quality, and PDF summary.")
        
    def collect_data(self):
        """Main collection loop"""
        self.logger.info("Starting collection loop...")
        # while data isn't complete...
        while not self.collection_complete():
            # ...check quality score and success rate...
            self.assess_data_quality()
            if self.get_success_rate() < 0.8:
                # ...make adjustments if necessary...
                self.adjust_strategy()
            # make request
            data = self.make_api_request()
            # if successful...
            if data:
                # process data accordingly
                processed = self.process_data(data)
                # store data if declared valid
                if self.validate_data(processed):
                    self.store_data(processed)
            # delay as neeeded
            self.respectful_delay()
        # and auto-generate report
        self.generate_final_report()

# run
if __name__ == "__main__":
    # join paths to access json
    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(script_dir, "config.json")
    # and go
    agent = DataCollectionAgent(config_path)
    agent.collect_data()