

\# CogniStream Analytics Storage Audit



\## Objective



Verify that daily analytics records are available in the

expected ClickHouse analytics tables.



\## Module



`src/database/analytics\_storage\_audit.py`



\## Tables audited



1\. developer\_sessions

2\. context\_switches

3\. flow\_blocks

4\. potential\_interruptions

5\. developer\_daily\_metrics



\## Audit process



1\. Validate the requested metric date.

2\. Execute a parameterized record-count query for each table.

3\. Capture the record count or the error.

4\. Calculate successful and failed checks.

5\. Generate an overall audit status.



\## Status definitions



\- success: All requested table checks succeeded.

\- partial: At least one check succeeded and at least one failed.

\- failed: All requested table checks failed.



A successful audit means the table queries completed.

It does not guarantee that the record counts are complete

or that every expected event was inserted.



\## Example usage



```python

from src.database.clickhouse\_connection import create\_clickhouse\_client

from src.database.analytics\_storage\_audit import audit\_analytics\_storage



client = create\_clickhouse\_client()



report = audit\_analytics\_storage(

&#x20;   client,

&#x20;   "2026-11-05",

)



print(report)

```



\## Testing



Run:



```powershell

python -m unittest discover -s tests -p "test\_analytics\_storage\_audit.py" -v

```



The automated tests use a mocked ClickHouse client.

Live database validation must be performed separately.



