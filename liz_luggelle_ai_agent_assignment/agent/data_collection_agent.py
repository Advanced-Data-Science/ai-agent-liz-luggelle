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
                    "time": datetime.utcnow().isoformat(),
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

    def generate_final_report(self):
        """Save reports"""
        # JSON metadata
        metadata_path = os.path.join("../data/metadata", "final_report.json")
        with open(metadata_path, "w") as f:
            json.dump(self.collection_stats, f, indent=2, default=str)

        # HTML report
        html_path = os.path.join("../reports", "quality_report.html")
        avg_quality = sum(self.collection_stats["data_quality_scores"]) / max(
            1, len(self.collection_stats["data_quality_scores"])
        )
        with open(html_path, "w") as f:
            f.write(f"<h1>Data Quality Report</h1>\n")
            f.write(f"<p>Average Quality Score: {avg_quality:.2f}</p>\n")

        # PDF summary placeholder
        pdf_path = os.path.join("../reports", "collection_summary.pdf")
        with open(pdf_path, "w") as f:
            f.write("PDF report generation placeholder")

        self.logger.info("Reports generated in ../reports and ../data/metadata")

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
    agent = DataCollectionAgent("config.json")
    agent.collect_data()

