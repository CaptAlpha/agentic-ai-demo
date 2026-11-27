# Issue 42: incomplete task pages and unstable ordering

Fictional student project: CampusTasks.
Reporter: a student testing the task dashboard.

Alice and Bob have interleaved tasks. Bob sees only one task on page 1 even though he owns two.
Alice's second page does not contain the expected remaining tasks.
When two tasks share a creation timestamp, changing input order changes the displayed order.

Acceptance criteria: follow the current API contract, fix owner-scoped pagination,
use deterministic ordering, preserve input data, and pass the regression suite.
No authentication bypass or cross-user data exposure has been demonstrated by this report.
The sample has no HTTP server, authentication middleware, database, or production logs.
