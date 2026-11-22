



\# CogniStream Analytics Storage Audit



\## Objective



The Analytics Storage Audit verifies whether daily analytics

records are available in the expected ClickHouse tables.



It helps identify incomplete analytics pipeline runs and

records table-level query failures.



\## Module



`src/database/analytics\_storage\_audit.py`



\## Tables audited



The audit supports five predefined analytics tables:



1\. `developer\_sessions` — filtered using `session\_start`.

2\. `context\_switches` — filtered using `from\_timestamp`.

3\. `flow\_blocks` — filtered using `block\_start`.

4\. `potential\_interruptions` — filtered using `interruption\_timestamp`.

5\. `developer\_daily\_metrics` — filtered using `metric\_date`.



The date expressions must match the ClickHouse schema.



\## Audit process



1\. Validate and normalize the requested metric date.

2\. Select all five tables or a requested subset.

3\. Reject unknown table names.

4\. Execute a parameterized record-count query for each table.

5\. Capture each table's record count or error.

6\. Calculate the total records from successful queries.

7\. Generate the overall audit status.



\## Status definitions



\- `success`: All selected table checks succeeded.

\- `partial`: At least one check succeeded and at least one failed.

\- `failed`: All selected table checks failed.



\## Error handling



Each table is audited independently. A query failure is

recorded in the report and does not stop checks on other tables.



If the ClickHouse client is missing, the report marks all

selected table checks as failed.



Invalid dates and unknown table names raise `ValueError`.



The total record count includes only successful table queries.



\## Example usage



```python

from src.database.clickhouse\_connection import create\_clickhouse\_client

from src.database.analytics\_storage\_audit import audit\_analytics\_storage



client = create\_clickhouse\_client()



report = audit\_analytics\_storage(

&#x20;   client,

&#x20;   "2026-11-22",

)



print(report)



\# Audit only selected tables.

selected\_report = audit\_analytics\_storage(

&#x20;   client,

&#x20;   "2026-11-22",

&#x20;   selected\_tables=\["developer\_sessions", "flow\_blocks"],

)



print(selected\_report)

```



\## Testing



Run the unit tests:



```powershell

python -m unittest discover -s tests -p "test\_analytics\_storage\_audit.py" -v

```



The nine automated tests use a mocked ClickHouse client.

They cover date validation, missing clients, successful and

failed audits, selected tables, unknown table names, and

total record calculation.



A successful mocked test run does not replace live

ClickHouse validation.



