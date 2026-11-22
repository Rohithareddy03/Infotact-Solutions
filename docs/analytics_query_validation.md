\# CogniStream – Analytics Query Optimization and Validation



\## 1. Objective



The analytics query module provides reusable functions for retrieving developer activity analytics from ClickHouse.



It supports date-range filtering, optional developer filtering, parameterized SQL execution, structured results, and database error handling.



\## 2. Database Tables



The queries use the existing CogniStream ClickHouse tables:



\- `developer\_daily\_metrics`

\- `developer\_sessions`

\- `flow\_blocks`

\- `context\_switches`

\- `potential\_interruptions`



\## 3. Supported Analytics



| Function | Description | Source table |

|---|---|---|

| `get\_total\_developer\_commits()` | Total commits per developer | developer\_daily\_metrics |

| `get\_activity\_duration()` | Estimated activity duration in minutes | developer\_daily\_metrics |

| `get\_average\_session\_duration()` | Average session duration | developer\_sessions |

| `get\_uninterrupted\_activity\_blocks()` | Qualifying uninterrupted blocks and duration | flow\_blocks |

| `get\_context\_switch\_frequency()` | Context-switch count | context\_switches |

| `get\_interruption\_count()` | Potential interruption count | potential\_interruptions |

| `get\_daily\_activity\_summary()` | Daily developer activity metrics | developer\_daily\_metrics |



\*\*Activity duration note:\*\* The current database schema contains `estimated\_activity\_minutes`. It does not contain a separate IDE-only duration field. The activity-duration function therefore returns the estimated activity metric.



\## 4. Query Optimization and Filtering



All new analytics functions use parameterized ClickHouse queries.



Supported filters:



\- `start\_date`

\- `end\_date`

\- Optional `developer\_id`



Date ranges are inclusive. Developer IDs are passed as bound query parameters rather than inserted directly into SQL strings.



Example:



```python

from src.database.analytics\_queries import (

&#x20;   get\_total\_developer\_commits,

)



result = get\_total\_developer\_commits(

&#x20;   start\_date="2026-11-01",

&#x20;   end\_date="2026-11-22",

&#x20;   developer\_id="DEV01",

)

{

&#x20;   "status": "success",

&#x20;   "data": \[

&#x20;       {

&#x20;           "developer\_id": "DEV01",

&#x20;           "total\_commits": 10

&#x20;       }

&#x20;   ],

&#x20;   "error": None

}

{

&#x20;   "status": "error",

&#x20;   "data": \[],

&#x20;   "error": "Connection failed"

}



