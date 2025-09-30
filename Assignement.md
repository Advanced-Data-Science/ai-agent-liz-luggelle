**Points:** 100 points  

---
Name: 

---

## Part 1: Create Your Data Collection Scenario (20 points)

Select ONE of the datasets in the Data Management Plan submitted for T2 and create a mini scenario by identifying the following aims:

### Scenario
**Main Objective:** 
- **Data Sources:** resources with and API
- **Data Types:** data variables needed from the API
- **Geographic Scope:** queries needed from API
- **Time Range:**

### Example Scenario: Weather Pattern Analysis
**Objective:** Collect weather data to analyze climate patterns across different cities
- **Data Sources:** OpenWeatherMap API (free tier), WeatherAPI (free tier)
- **Data Types:** Temperature, humidity, precipitation, wind speed
- **Geographic Scope:** 5-10 cities of your choice
- **Time Range:** Current conditions + 5-day forecast

*If your DMP does not include an API, use one of the DMP scenarios in scenarios.md

---

## Part 2: API Fundamentals - Your First API Call (15 points)

### Exercise 2.2: Your First API Call

**Your Task:**
1. Run the code and understand each part so you can easily reproduce it
2. Modify it to get 5 different cat facts
3. Add proper error handling and logging
4. Save the facts to a JSON file

### Exercise 2.3: API with Parameters

**Your Task:**
1. Test this function with 3 different countries
2. Extract and print just the holiday names and dates
3. Create a summary comparing holiday counts by country

**Deliverable 2:**  
on github repo:
- Working code files for both exercises
on brightspace:
- Brief reflection (1 paragraph) on what you learned about APIs

---

## Part 3: Setting Up Free API Access (10 points)

### API Key Security Best Practices:

**Deliverable 3:**
on brightspace:
- Screenshot showing successful API key creation
on github repo:
- Test script that successfully calls your chosen API
- Config file template (with fake keys as examples)

---

## Part 4: Build Your AI Data Collection Agent (35 points)

### Agent Requirements:

Your agent must include these components:  
 1. Configuration Management
 2. Intelligent Collection Strategy
 3. Data Quality Assessment
 4. Adaptive Strategy
 5. Respectful Collection

**Deliverable 4:**
on github repo:
- Complete Python agent class (well-commented)
- Configuration file based on your DMP
- Test results showing the agent successfully collecting data
- Log file showing respectful collection practices

---

## Part 5: Documentation (20 pts)


Required Documentation Features:
1. Automated Metadata Generation
2. Quality Report Generation
3. Collection Summary

Quality Report should contain:
- total number of records
- collection success rate
- quality score (metrics such as accuracy, completeness, consistency, and/or validity which you choose will depend on your data plan)
        
Your agent should produce a final summary including:
- Total data points collected
- Success/failure rates by API
- Quality metrics and trends
- Any issues encountered
- Recommendations for future collection

**Deliverable 5:**
on github:
- Automated metadata file
- Collection summary document  
on brightspace:
- Quality assessment report  
- Screenshots of your agent running

---

## Submission Requirements

Submit a report to Brightspace with a titled section for each component and the code to the github repo for this assignement with the file structure defined in 
### File Structure:
```
your_name_ai_agent_assignment/
├── README.md                    # Project overview and instructions
├── data_management_plan.pdf     # Your mini-DMP from Part 1
├── agent/
│   ├── data_collection_agent.py # Your main agent class
│   ├── config.json             # Configuration file
│   ├── requirements.txt        # Python dependencies
│   └── tests/
│       └── test_agent.py       # Basic tests
├── data/
│   ├── raw/                    # Raw collected data
│   ├── processed/              # Cleaned data
│   └── metadata/               # Generated documentation
├── logs/
│   └── collection.log          # Agent execution logs
├── reports/
│   ├── quality_report.html     # Human-readable quality report
│   └── collection_summary.pdf  # Final summary
└── demo/
    ├── api_exercises.py        # Your Part 2 exercises
    └── demo_screenshots/       # Screenshots of agent running
```

### Code Quality Requirements:
- **Documentation**: Every function must have docstrings
- **Error Handling**: Proper try/catch blocks and logging
- **Rate Limiting**: Respectful delays and API limit monitoring
- **Configuration**: No hardcoded values, use config files
- **Testing**: Basic unit tests for key functions

### Written Components:
1. **README.md** (2-3 pages): Project overview, setup instructions, usage guide
2. **Mini Data Management Plan** (1-2 pages): From Part 1
3. **Quality Report** (auto-generated): Data quality analysis
4. **Collection Summary** (1 page): Results and lessons learned

---

## Grading Rubric

| Component | Excellent (A) | Good (B) | Satisfactory (C) | Needs Improvement (D/F) |
|-----------|---------------|----------|------------------|-------------------------|
| **Mini DMP (20 pts)** | Comprehensive, specific, well-researched | Good coverage, minor gaps | Basic requirements met | Incomplete or generic |
| **API Fundamentals (15 pts)** | Perfect execution, creative extensions | All exercises working | Basic requirements met | Some exercises not working |
| **API Setup (10 pts)** | All keys working, excellent security | Keys working, good security | Keys working, basic security | Keys not working |
| **AI Agent (35 pts)** | Sophisticated, adaptive, well-designed | Good functionality, some AI features | Basic collection working | Agent not functional |
| **Documentation (20 pts)** | Comprehensive, auto-generated, professional | Good documentation, mostly complete | Basic documentation | Poor or missing documentation |

---

## Resources and Help

### Getting Started Resources:
- **Python Requests Tutorial**: [Real Python Requests Guide](https://realpython.com/python-requests/)
- **API Testing**: Use [Postman](https://www.postman.com/) or [HTTPie](https://httpie.io/) to test APIs
- **JSON Handling**: [Working with JSON in Python](https://realpython.com/python-json/)

### Free APIs for Practice:
- [JSONPlaceholder](https://jsonplaceholder.typicode.com/) - Fake REST API for testing
- [Dog CEO API](https://dog.ceo/dog-api/) - Dog images API
- [Rest Countries](https://restcountries.com/) - Country information
- [Public APIs List](https://github.com/public-apis/public-apis) - Huge list of free APIs

### Common Challenges and Solutions:

**Challenge**: "My API calls are failing"
**Solution**: Check your API key, read the documentation, verify the endpoint URL

**Challenge**: "I'm getting rate limited"  
**Solution**: Add longer delays, respect the API's rate limits, consider using multiple APIs

**Challenge**: "My agent is too slow"
**Solution**: Implement concurrent requests (carefully!), cache results, optimize your processing

**Challenge**: "Data quality is poor"
**Solution**: Add validation checks, implement retry logic, use multiple data sources

---

## Extension Ideas (Optional)

If you finish early or want to go beyond the requirements:

### Advanced Features:
- **Multi-threading**: Collect from multiple sources simultaneously
- **Machine Learning**: Use ML to predict optimal collection times
- **Real-time Monitoring**: Create a dashboard showing collection progress  
- **Data Visualization**: Generate charts showing data quality trends
- **Alerting System**: Send notifications when collection issues occur

### Integration Opportunities:
- **Database Storage**: Store data in SQLite or PostgreSQL
- **Cloud Deployment**: Deploy your agent to run automatically
- **API Creation**: Turn your agent into an API that others can use
- **Containerization**: Package your agent with Docker

---

**Good luck building your AI data collection agent! Remember, the goal is not just to collect data, but to do so responsibly, efficiently, and with proper documentation. Your future self (and your research collaborators) will thank you for the time invested in good practices.**

---

*If you have any questions about this assignment, please don't hesitate to ask during office hours. We're here to help you succeed!*
