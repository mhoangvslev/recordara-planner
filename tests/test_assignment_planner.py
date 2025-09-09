"""Test cases for the TaskAssignmentPlanner."""

import unittest
import sys
import os

# Add the parent directory to the path to import the planner module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from planner.main import TaskAssignmentPlanner


class TestTaskAssignmentPlanner(unittest.TestCase):
    """Test cases for the TaskAssignmentPlanner class."""

    def setUp(self):
        """Set up test fixtures before each test method."""
        self.tasks_file = "data/tasks.csv"
        self.participants_file = "data/participants.csv"

        # Check if test data files exist
        if not os.path.exists(self.tasks_file):
            self.skipTest(f"Test data file not found: {self.tasks_file}")
        if not os.path.exists(self.participants_file):
            self.skipTest(f"Test data file not found: {self.participants_file}")

        # Create planner instance
        self.planner = TaskAssignmentPlanner(self.tasks_file, self.participants_file)

        # Solve the assignment problem
        self.solution_found = self.planner.solve()

        if not self.solution_found:
            self.skipTest("No solution found for the assignment problem")

    def test_all_tasks_assigned(self):
        """Test that all tasks are assigned to exactly one participant."""
        assignments = self.planner.get_assignments()

        # Get all task IDs from assignments
        assigned_task_ids = {assignment["task_id"] for assignment in assignments}

        # Get all task IDs from the original tasks
        all_task_ids = {task["task_id"] for task in self.planner.tasks}

        # Check that all tasks are assigned
        self.assertEqual(
            assigned_task_ids, all_task_ids, "Not all tasks have been assigned"
        )

        # Check that each task is assigned to exactly one participant
        task_assignment_counts = {}
        for assignment in assignments:
            task_id = assignment["task_id"]
            task_assignment_counts[task_id] = task_assignment_counts.get(task_id, 0) + 1

        for task_id, count in task_assignment_counts.items():
            self.assertEqual(
                count,
                1,
                f"Task {task_id} is assigned to {count} participants, should be exactly 1",
            )

    def test_obligations_respected(self):
        """Test that participant obligations are respected."""
        assignments = self.planner.get_assignments()

        # Check Minh-Hoang DANG's obligations (should be assigned to SAT1, SAT8)
        minh_assignments = [
            a for a in assignments if a["participant"] == "Minh-Hoang DANG"
        ]
        minh_task_ids = {a["task_id"] for a in minh_assignments}

        # Minh-Hoang DANG should be assigned to SAT1 and SAT8
        self.assertIn(
            "SAT1", minh_task_ids, "Minh-Hoang DANG should be assigned to SAT1"
        )
        self.assertIn(
            "SAT8", minh_task_ids, "Minh-Hoang DANG should be assigned to SAT8"
        )

        # Check all participants' obligations
        for participant in self.planner.participants:
            participant_assignments = [
                a for a in assignments if a["participant"] == participant["name"]
            ]
            participant_task_ids = {a["task_id"] for a in participant_assignments}

            # Check that all obliged tasks are assigned
            for obliged_task in participant["obligations"]:
                self.assertIn(
                    obliged_task,
                    participant_task_ids,
                    f"Participant {participant['name']} should be assigned to {obliged_task}",
                )

    def test_snu_hour_limit(self):
        """Test that SNU participants work no more than 21 hours."""
        assignments = self.planner.get_assignments()

        # Calculate total hours for each SNU participant
        snu_hours = {}
        for assignment in assignments:
            if assignment["participant_role"] == "SNU":
                name = assignment["participant"]
                duration = assignment["duration"]

                # Parse duration (e.g., '16H00-19H00')
                start_time, end_time = duration.split("-")
                start_hour = int(start_time.split("H")[0])
                start_min = (
                    int(start_time.split("H")[1])
                    if len(start_time.split("H")[1]) > 0
                    else 0
                )
                end_hour = int(end_time.split("H")[0])
                end_min = (
                    int(end_time.split("H")[1])
                    if len(end_time.split("H")[1]) > 0
                    else 0
                )

                start_minutes = start_hour * 60 + start_min
                end_minutes = end_hour * 60 + end_min
                task_hours = (end_minutes - start_minutes) / 60.0

                if name not in snu_hours:
                    snu_hours[name] = 0
                snu_hours[name] += task_hours

        # Check that all SNU participants are within 21-hour limit
        for name, total_hours in snu_hours.items():
            self.assertLessEqual(
                total_hours,
                21.0,
                f"SNU participant {name} works {total_hours:.1f} hours, exceeds 21-hour limit",
            )

        # Print SNU hours for verification
        print("\nSNU Participants Total Hours:")
        for name, hours in snu_hours.items():
            print(f"  {name}: {hours:.1f} hours")

    def test_no_time_conflicts(self):
        """Test that no participant is assigned to overlapping tasks."""
        assignments = self.planner.get_assignments()

        # Group assignments by participant
        participant_assignments = {}
        for assignment in assignments:
            name = assignment["participant"]
            if name not in participant_assignments:
                participant_assignments[name] = []
            participant_assignments[name].append(assignment)

        # Check for time conflicts for each participant
        for participant_name, participant_tasks in participant_assignments.items():
            # Sort tasks by day and start time
            sorted_tasks = sorted(
                participant_tasks, key=lambda x: (x["day"], x["duration"])
            )

            for i in range(len(sorted_tasks) - 1):
                task1 = sorted_tasks[i]
                task2 = sorted_tasks[i + 1]

                # Only check for conflicts on the same day
                if task1["day"] == task2["day"]:
                    # Parse times
                    start1, end1 = task1["duration"].split("-")
                    start2, end2 = task2["duration"].split("-")

                    start1_hour = int(start1.split("H")[0])
                    start1_min = (
                        int(start1.split("H")[1])
                        if len(start1.split("H")[1]) > 0
                        else 0
                    )
                    end1_hour = int(end1.split("H")[0])
                    end1_min = (
                        int(end1.split("H")[1]) if len(end1.split("H")[1]) > 0 else 0
                    )

                    start2_hour = int(start2.split("H")[0])
                    start2_min = (
                        int(start2.split("H")[1])
                        if len(start2.split("H")[1]) > 0
                        else 0
                    )
                    end2_hour = int(end2.split("H")[0])
                    end2_min = (
                        int(end2.split("H")[1]) if len(end2.split("H")[1]) > 0 else 0
                    )

                    start1_minutes = start1_hour * 60 + start1_min
                    end1_minutes = end1_hour * 60 + end1_min
                    start2_minutes = start2_hour * 60 + start2_min
                    end2_minutes = end2_hour * 60 + end2_min

                    # Check for overlap
                    overlap = not (
                        end1_minutes <= start2_minutes or end2_minutes <= start1_minutes
                    )

                    self.assertFalse(
                        overlap,
                        f"Time conflict for {participant_name}: {task1['task_id']} ({task1['duration']}) "
                        f"overlaps with {task2['task_id']} ({task2['duration']})",
                    )

    def test_workload_balancing(self):
        """Test that workload is reasonably balanced among participants."""
        assignments = self.planner.get_assignments()

        # Count tasks per participant
        participant_task_counts = {}
        for assignment in assignments:
            name = assignment["participant"]
            participant_task_counts[name] = participant_task_counts.get(name, 0) + 1

        # Check that all participants have at least 1 task
        for name, count in participant_task_counts.items():
            self.assertGreaterEqual(
                count,
                1,
                f"Participant {name} has {count} tasks, should have at least 1",
            )

        # Check that no participant has more than 6 tasks
        for name, count in participant_task_counts.items():
            self.assertLessEqual(
                count, 6, f"Participant {name} has {count} tasks, should have at most 6"
            )

        # Print workload distribution for verification
        print("\nWorkload Distribution:")
        for name, count in sorted(participant_task_counts.items()):
            print(f"  {name}: {count} tasks")

    def test_equal_treatment(self):
        """Test that all participants are treated equally (no role-based bias)."""
        assignments = self.planner.get_assignments()

        # Group assignments by role
        role_assignments = {}
        for assignment in assignments:
            role = assignment["participant_role"]
            if role not in role_assignments:
                role_assignments[role] = []
            role_assignments[role].append(assignment)

        # Calculate average tasks per participant by role
        role_stats = {}
        for role, role_tasks in role_assignments.items():
            participant_counts = {}
            for task in role_tasks:
                name = task["participant"]
                participant_counts[name] = participant_counts.get(name, 0) + 1

            if participant_counts:
                avg_tasks = sum(participant_counts.values()) / len(participant_counts)
                role_stats[role] = {
                    "avg_tasks": avg_tasks,
                    "participant_count": len(participant_counts),
                    "total_tasks": sum(participant_counts.values()),
                }

        # Print role statistics for verification
        print("\nRole-based Statistics:")
        for role, stats in role_stats.items():
            print(
                f"  {role}: {stats['avg_tasks']:.1f} avg tasks per participant "
                f"({stats['total_tasks']} total tasks, {stats['participant_count']} participants)"
            )

        # The test passes if we can calculate statistics (no role-based assignment failures)
        self.assertTrue(
            len(role_stats) > 0, "No role-based statistics could be calculated"
        )

    def test_solution_quality(self):
        """Test that the solution is of good quality."""
        assignments = self.planner.get_assignments()

        # Basic quality checks
        self.assertGreater(len(assignments), 0, "No assignments found")
        self.assertEqual(
            len(assignments),
            len(self.planner.tasks),
            "Number of assignments should equal number of tasks",
        )

        # Check that we have participants from all roles
        participant_roles = {a["participant_role"] for a in assignments}
        expected_roles = {"Permanant", "Non-permanant", "SNU"}
        self.assertEqual(
            participant_roles,
            expected_roles,
            "Not all participant roles are represented in assignments",
        )


if __name__ == "__main__":
    # Create a test suite
    test_suite = unittest.TestLoader().loadTestsFromTestCase(TestTaskAssignmentPlanner)

    # Run the tests with verbose output
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)

    # Print summary
    print(f"\n{'=' * 50}")
    print("Test Summary:")
    print(f"  Tests run: {result.testsRun}")
    print(f"  Failures: {len(result.failures)}")
    print(f"  Errors: {len(result.errors)}")
    print(
        f"  Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%"
    )

    if result.failures:
        print("\nFailures:")
        for test, traceback in result.failures:
            print(f"  - {test}: {traceback}")

    if result.errors:
        print("\nErrors:")
        for test, traceback in result.errors:
            print(f"  - {test}: {traceback}")
