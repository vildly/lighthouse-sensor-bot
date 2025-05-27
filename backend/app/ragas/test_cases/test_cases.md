# Test Cases Classification Summary

## Categories Overview

### Query Complexity
- **Simple**: Direct retrieval of single values or basic calculations that can be answered with simple SQL queries
- **Moderate**: Requires aggregation, comparison, or multiple data points that can be handled with SQL
- **Complex**: Requires custom code generation, complex data transformations, or advanced analytics that cannot be easily expressed in SQL

### Maritime Domain Categories
1. **Fuel Efficiency**
   - Fuel consumption metrics
   - Cost calculations
   - Efficiency comparisons

2. **Route Optimization/Operations**
   - PCE (Passenger Car Equivalent) analysis
   - Vehicle throughput
   - Trip durations
   - Terminal operations
   - Route utilization

3. **Environmental Impact**
   - CO2 emissions
   - Environmental metrics

### Data Interaction Types
1. **Retrieval**
   - Simple data lookups
   - Direct value extraction

2. **Aggregation**
   - Average calculations
   - Sum totals
   - Combined metrics

3. **Comparison**
   - Ratio analysis
   - Percentage differences
   - Comparative metrics

## Test Cases Distribution

### By Complexity
- Simple: 4 test cases (20%)
- Moderate: 12 test cases (60%)
- Complex: 4 test cases (20%)

### By Domain Category
- Fuel Efficiency: 3 test cases (15%)
- Route Optimization/Operations: 15 test cases (75%)
- Environmental Impact: 2 test cases (10%)

### By Interaction Type
- Retrieval: 5 test cases (25%)
- Aggregation: 13 test cases (65%)
- Comparison: 2 test cases (10%)

## Detailed Test Cases

1. **Fuel Cost Calculation** (Simple, Fuel Efficiency, Retrieval)
   - Calculates total fuel cost for a specific ferry and time period
   - Can be done with simple SQL aggregation

2. **Average Speed** (Simple, Route Optimization, Retrieval)
   - Retrieves average speed of a specific ferry
   - Basic SQL calculation

3. **Terminal Vehicle Analysis** (Moderate, Route Optimization, Aggregation)
   - Analyzes vehicles left at terminal for inbound trips
   - Requires SQL aggregation and filtering

4. **Summer Operations Analysis** (Complex, Route Optimization, Aggregation)
   - Calculates average vehicles unable to board during summer months
   - Requires date handling and complex aggregations

5. **Daily PCE Analysis** (Complex, Route Optimization, Aggregation)
   - Determines highest average daily PCE value for a route
   - Requires grouping by day and complex aggregations

6. **Route Distance** (Simple, Route Optimization, Retrieval)
   - Retrieves average distance for a specific route
   - Simple SQL calculation

7. **Peak Hour Analysis** (Complex, Route Optimization, Aggregation)
   - Calculates total PCE during peak hours
   - Requires time-based grouping and complex aggregations

8. **Fuel Consumption Analysis** (Moderate, Fuel Efficiency, Aggregation)
   - Analyzes average fuel consumption for a route
   - Basic SQL aggregation

9. **Trip Duration** (Moderate, Route Optimization, Retrieval)
   - Calculates average trip duration
   - Requires time difference calculations

10. **Fuel Efficiency Comparison** (Simple, Fuel Efficiency, Retrieval)
    - Compares fuel consumption rates across ferries
    - Simple SQL comparison

11. **Route Utilization** (Complex, Route Optimization, Aggregation)
    - Analyzes utilization percentage based on PCE
    - Requires complex calculations and capacity comparisons

12. **Terminal Capacity Analysis** (Moderate, Route Optimization, Aggregation)
    - Calculates average vehicles left at terminals
    - Basic SQL aggregation

13. **Daily Throughput** (Moderate, Route Optimization, Aggregation)
    - Analyzes average daily vehicle throughput
    - Requires date-based grouping

14. **Day-Specific Analysis** (Moderate, Route Optimization, Aggregation)
    - Calculates average PCE for specific days
    - Requires day-of-week filtering

15. **Peak Hour Identification** (Moderate, Route Optimization, Aggregation)
    - Identifies hours with highest PCE
    - Requires time-based grouping

16. **Seasonal Analysis** (Moderate, Route Optimization, Aggregation)
    - Analyzes PCE during specific months
    - Requires month-based grouping

17. **Weekday/Weekend Comparison** (Moderate, Route Optimization, Comparison)
    - Compares pedestrian to vehicle ratios
    - Requires day type classification

18. **Hourly PCE Analysis** (Moderate, Route Optimization, Aggregation)
    - Identifies peak PCE hours
    - Requires time-based grouping

19. **Ratio Analysis** (Moderate, Route Optimization, Aggregation)
    - Calculates pedestrian to vehicle ratios
    - Basic ratio calculation

20. **Environmental Impact** (Moderate, Environmental Impact, Aggregation)
    - Calculates CO2 emissions based on fuel consumption
    - Requires conversion calculations