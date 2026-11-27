"""Trusted regression suite for the task-list teaching fixture."""

import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location("task_service", Path(__file__).resolve().parents[1] / "task_service.py")
service = importlib.util.module_from_spec(spec)
spec.loader.exec_module(service)


def sample_tasks():
    return [
        {"id": 3, "owner": "bob", "created_at": 1},
        {"id": 2, "owner": "alice", "created_at": 2},
        {"id": 1, "owner": "alice", "created_at": 2},
        {"id": 4, "owner": "bob", "created_at": 3},
        {"id": 5, "owner": "alice", "created_at": 4},
        {"id": 6, "owner": "alice", "created_at": 5},
    ]


class TaskServiceTests(unittest.TestCase):
    def test_owner_filter_precedes_pagination(self):
        actual = service.list_tasks(sample_tasks(), "bob", page_size=2)
        self.assertEqual([task["id"] for task in actual], [3, 4])

    def test_first_page_ties_use_id(self):
        actual = service.list_tasks(sample_tasks(), "alice", page_size=2)
        self.assertEqual([task["id"] for task in actual], [1, 2])

    def test_second_page_has_remaining_owner_tasks(self):
        actual = service.list_tasks(sample_tasks(), "alice", page=2, page_size=2)
        self.assertEqual([task["id"] for task in actual], [5, 6])

    def test_order_is_independent_of_input(self):
        tasks = [task for task in sample_tasks() if task["owner"] == "alice"]
        forward = service.list_tasks(tasks, "alice", page_size=10)
        backward = service.list_tasks(list(reversed(tasks)), "alice", page_size=10)
        self.assertEqual([task["id"] for task in forward], [task["id"] for task in backward])

    def test_no_cross_owner_results(self):
        for page in (1, 2, 3):
            self.assertTrue(all(task["owner"] == "alice" for task in service.list_tasks(sample_tasks(), "alice", page=page)))

    def test_empty_and_out_of_range(self):
        self.assertEqual(service.list_tasks([], "alice"), [])
        self.assertEqual(service.list_tasks(sample_tasks(), "nobody"), [])
        self.assertEqual(service.list_tasks(sample_tasks(), "alice", page=99), [])

    def test_invalid_pagination(self):
        for value in (0, -1, True, 1.5):
            with self.assertRaises(ValueError):
                service.list_tasks([], "alice", page=value)
            with self.assertRaises(ValueError):
                service.list_tasks([], "alice", page_size=value)

    def test_does_not_mutate_input(self):
        tasks = sample_tasks()
        original = [dict(task) for task in tasks]
        result = service.list_tasks(tasks, "alice", page_size=10)
        result[0]["owner"] = "changed"
        self.assertEqual(tasks, original)


if __name__ == "__main__":
    unittest.main()
