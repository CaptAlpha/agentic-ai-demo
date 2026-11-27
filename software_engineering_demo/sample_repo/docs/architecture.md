# CampusTasks architecture

This teaching repository contains one Python domain module and unittest regressions.
task_service.py owns owner filtering, deterministic ordering, pagination and output copies.
tests/test_task_service.py exercises acceptance criteria and defensive input handling.

The intended data flow is owner filter -> stable key sort -> page slice -> copy records.
The baseline implementation contains defects intentionally for an agentic debugging exercise.
No database migration, package installation, network access, or deployment is necessary.
The bundled test runner executes only this fixture in a disposable temporary directory.
