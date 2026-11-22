# API Requirements

## Functional Requirements

1. Provide a health-check endpoint.
2. Retrieve overall developer analytics.
3. Retrieve analytics for an individual developer.
4. Support date-range filtering.
5. Return activity summaries.
6. Return structured JSON responses.
7. Handle empty datasets.
8. Handle database failures.

## Non-Functional Requirements

1. Maintain readable and modular code.
2. Validate incoming requests.
3. Provide meaningful HTTP status codes.
4. Protect database credentials.
5. Support frontend integration.
6. Include automated tests.

## Expected Analytics

- Total commits.
- IDE activity duration.
- Average session duration.
- Uninterrupted coding blocks.
- Context switches.
- Interruption counts.

Note: These are activity-based indicators and
should not be presented as direct measurements
of a person's cognitive state.