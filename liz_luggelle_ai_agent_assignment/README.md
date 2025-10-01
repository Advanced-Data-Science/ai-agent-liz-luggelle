Author: Liz Luggelle
Updated: September 30, 2025

## Assignment Overview
This assignment entailed creating an AI agent to automate weather data collection. It utilizes the free OpenWeatherMap API to collect data on temperature and humidity for 5 cities in the northeast region of the US: Burlington VT, Boston MA, Portland ME, Albany NY, and New York NY.

## Setup Steps - class initialization
- Loads the API key from environment variables and reads the configuration.
- Initializes record and collection statistics storage -> where success rates and data quality information are stored.
- Creates directories in setup_directories -> where data subdirectories, logs, reports are stored
- Configures logging system
- Loads configuration file -> reads in collection parameters and passes API key, error handling

## Data Collection - main loop
- Data collection commences until data is sufficient
- Records quality score based on completeness, consistency, accuracy, timeliness
- Adjusts latency (delay between requests) as needed -> performance based
- Makes API requests for each city defined in the configuration -> success and failures are recorded
- Processes data by extracting relevant fields and creating structured records*
- Validates data to check that records are complete -> stores under raw data if valid

## Data Processing - recording & validation details
Records for each city are made containing:
- current timestamp (time of call)
- name of the city
- temperature data (in C)
- humidity percentage
- written description of the weather
The validation step checks that the records list is not empty and verifies temperature and humidity data. It raises issues if any found, and stores valid data to a json file.

Success rates are calculated to check performance, and if they are deemed low (<50%>) the delay increases. If performance is high (success rates >90%), the delay decreases.

A distribution analysis is performed to find the min, max, and average temperature, as well as an anomaly detection to flag outlying temperature records.

## Report Generation - metadata, quality, summary
After running, the agent auto-generates and saves reports for metadata, a quality report in json and html, and a collection summary as follows:

Metadata Contents
- collection date
- agent version
- data sources
- quality metrics summary
- variable descriptions

Quality Report Contents (as reported during data processing) - saved in json and made available in styled HTML
- summary statistics
- completeness analysis
- data distribution
- anomaly detection
- recommendations (self-generated)

Collection Summary Contents (pdf auto-generated)
- total data points
- success and failure rates
- quality metrics
- issues encountered 
- recommendations (as found in quality report)

## Recommendations
Recommendations are issued based on success rate, data volume, API failures, and detected anomalies

## Setup Instructions
Requirements:
- Python 3.7 or higher
- OpenWeatherMap API key (in env file)

Dependencies:
- requests (for API requests)
- python-dotenv (to load env)
- reportlab (to generate summary pdf)

Configuration:
- config.json file may be configured in the agent directory for any cities following the appropriate format
- US City Format: "{CityName},{STATE_ABBREVIATION},US"
- International City Format: "{CityName}, {TERRITORY_ABBREVIATION}"

## Useage Guide
Must be run from the "agent" directory to ensure proper storage of logs, data, and reports.

Feedback is provided as collection begins, and when reports and summaries are saved. Directory location of said data is reported in terminal along with a date/time of creation.

Cities may be added or deleted by altering the config found in the agent directory.