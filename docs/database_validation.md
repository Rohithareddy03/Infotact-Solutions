

\# CogniStream Database Validation



\## Objective



Validate the ClickHouse database structure and identify

basic data-quality issues in the developer analytics tables.



\## Tables checked



1\. developer\_events

2\. developer\_sessions

3\. context\_switches

4\. flow\_blocks

5\. potential\_interruptions

6\. developer\_daily\_metrics



\## Validation checks



\### 1. Table existence



Checks whether all required analytical tables exist

in the cognistream database.



\### 2. Column validation



Checks whether each table contains its required columns.



\### 3. Record counts



Retrieves the number of records stored in each table.



\### 4. Duplicate event detection



Identifies event IDs that occur more than once in

developer\_events.



\### 5. Duration validation



Identifies sessions and activity blocks with negative

duration values.



\### 6. Connection validation



Executes SELECT 1 to verify basic ClickHouse connectivity.



\### 7. Query performance



Measures the execution time of a basic SELECT 1 query.



\## Expected outcome



The validation report contains:



\- Database name

\- Table existence status

\- Column validation status

\- Record counts

\- Missing tables and columns

\- Duplicate event details

\- Negative duration counts

\- Query execution time

\- Overall validation status



\## Important limitations



A successful structural validation does not prove that

all analytical calculations are correct.



Duplicate IDs should be investigated before removal.

MergeTree tables do not automatically enforce unique IDs.



The duplicate check returns at most 100 duplicate event IDs.



Potential interruptions are activity-based estimates,

not confirmed measurements of cognitive state.



The basic SELECT 1 performance check is not a benchmark

of complex analytical queries.



The validation module does not automatically modify

or delete database records.



