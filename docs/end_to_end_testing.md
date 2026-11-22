

\# CogniStream End-to-End Analytics Testing



\## Objective



Validate the integration of developer event processing modules and confirm that the unified analytics pipeline produces the expected outputs.



\## Test Input



The tests use sample developer activity events from ActivityWatch and Slack.



Each event contains:

\- Event ID

\- Developer ID

\- Source

\- Event type

\- Timestamp

\- Metadata



\## Pipeline Stages Tested



1\. Event cleaning and validation

2\. Developer session detection

3\. Context-switch analysis

4\. Flow-block analysis

5\. Potential interruption detection

6\. Developer baseline metrics



\## Validation



The tests verify:



\- All expected analytics outputs are returned.

\- Processing outputs are Polars DataFrames.

\- The original input DataFrame is not modified.

\- Empty input is handled.

\- Quality reports contain expected counts.

\- Invalid inputs and thresholds are rejected.



\## Execution



Run from the project root:



```powershell

python -m unittest discover -s tests -p "test\_end\_to\_end\_analytics.py" -v

```



\## Scope and Limitations



These are automated processing integration tests using sample data.



They do not prove that a live ClickHouse server or Airflow scheduler is operational.



Live database insertion, Airflow execution, and dashboard integration require separate environment-level validation.



