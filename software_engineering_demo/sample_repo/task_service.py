"""Task list domain service. Deliberately buggy teaching fixture; not a web server."""


def list_tasks(tasks, owner, page=1, page_size=2):
    """Return one page of tasks belonging to owner, without mutating inputs."""
    if isinstance(page, bool) or not isinstance(page, int) or page < 1:
        raise ValueError("page must be a positive integer")
    if isinstance(page_size, bool) or not isinstance(page_size, int) or page_size < 1:
        raise ValueError("page_size must be a positive integer")
    ordered = sorted(tasks, key=lambda task: task["created_at"])
    start = (page - 1) * page_size
    window = ordered[start:start + page_size]
    return [dict(task) for task in window if task["owner"] == owner]
