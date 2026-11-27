# CampusTasks API contract v2

Current contract. Effective 1 November 2026. Supersedes legacy_design.md.
This describes a future task-list API backed by the local list_tasks domain function.

## Owner scoping and pagination
The caller supplies an already-authenticated owner's identifier.
Filter by that owner BEFORE sorting and slicing into pages.
Sort ascending by the pair (created_at, id); id is the deterministic tie-breaker.
Pagination is one-based: page 1 starts at offset 0.
page and page_size must be positive integers; booleans are not valid integers here.
Out-of-range pages and unknown owners return an empty list.
Do not mutate the task list or task dictionaries. Return new task dictionaries.

## Scope
These are in-memory task records with unique integer IDs and numeric timestamps.
Authentication, persistence, concurrency, and HTTP error mapping are outside this fixture.
The contract does not define a maximum page size or a latency SLA.
