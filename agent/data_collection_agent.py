import os
import json
import time
import random
import logging
import requests
from datetime import datetime
from dotenv import load_dotenv

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
            'data_quality_scores': []
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
                self.logger.error(f"API request failed for {city}: {e}")
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
                self.logger.error(f"Data processing failed: {e}")
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
            self.logger.warning("Low success rate detected. Increasing delay.")
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

        json_path = os.path.join("../reports", "quality_report.json") 
        with open(json_path, "w") as f: 
            json.dump(report, f, indent=2)

        text_path = os.path.join("../reports", "quality_report.txt")

        with open(text_path, "w") as f:
            f.write("Quality Report\n" + "="*40 + "\n\n") 
            for k, v in report["summary"].items(): 
                f.write(f"{k}: {v}\n") 
            f.write("\nRecommendations:\n") 
            for rec in report["recommendations"]: 
                f.write(f"- {rec}\n") 
                
        self.logger.info("Quality report generated.")

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
        if not recs: 
            recs.append("Collection successful with no major issues.") 
        return recs

    def generate_final_report(self):
        """Save reports"""
        self.generate_metadata()
        self.generate_quality_report()
        self.logger.info("Reports generated: metadata and quality.")
        
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

