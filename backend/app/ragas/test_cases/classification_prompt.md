For this syntethic test cases json file. 

Act as a classification assistant to categorize  maritime sensor data queries.

For each query object, add the following classifications:

query_complexity:
Simple: Direct lookup or single-step calculation that can be done with sql 
Moderate: Involves aggregation, basic comparison, or multi-step logic, can be done with sql 
Complex: Requires multiple aggregations, temporal analysis, correlation, inference, or generating code 
Predictive: Involves forecasting or recommending based on patterns (e.g., "predictive maintenance").
Edge Case: Ambiguous, incomplete data, or designed to test robustness under challenging conditions.

maritime_domain_category:
Fuel Efficiency: Questions about fuel consumption, optimization, cost.
Engine Health/Maintenance: Questions about engine performance, anomalies, predictive maintenance.
Route Optimization/Operations: Questions about scheduling, speed, trip frequency, capacity.
Environmental Impact: Emissions, compliance, environmental conditions affecting operations.
Safety/Risk: Questions related to operational safety or risk assessment.
General Data Access/Reporting: Basic data retrieval, summarizing operations.
Other .

data_interaction_type:
Retrieval: Direct extraction of information.
Aggregation: Sums, averages, counts, etc.
Comparison: Comparing values across different entities or time periods.
Trend Analysis: Identifying patterns over time.
Anomaly Detection: Identifying unusual sensor readings or operational patterns.
Recommendation/Actionable Insight: Questions leading to suggestions or actions.

Add classification to the json file as additional fields for each query. 