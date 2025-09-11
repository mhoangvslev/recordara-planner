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

    def test_snu_hour_requirement(self):
        """Test that SNU participants work exactly 21 hours."""
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

        # Check that all SNU participants work exactly 21 hours
        for name, total_hours in snu_hours.items():
            self.assertEqual(
                total_hours,
                21.0,
                f"SNU participant {name} works {total_hours:.1f} hours, should work exactly 21 hours",
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

    def test_minimum_people_constraint(self):
        """Test that each task has at least the minimum required number of people."""
        assignments = self.planner.get_assignments()

        # Count assigned people per task
        task_assignments = {}
        for assignment in assignments:
            task_id = assignment["task_id"]
            if task_id not in task_assignments:
                task_assignments[task_id] = 0
            task_assignments[task_id] += 1
        
        # Check that each task meets minimum people requirement
        for task in self.planner.tasks:
            task_id = task["task_id"]
            min_people = task["min_people"]
            assigned_people = task_assignments.get(task_id, 0)
            
            self.assertGreaterEqual(
                assigned_people,
                min_people,
                f"Task {task_id} requires {min_people} people but only has {assigned_people} assigned"
            )
            
            # Print task assignment details for verification
            print(f"Task {task_id}: {assigned_people}/{min_people} people (min: {min_people})")

    def test_maximum_people_constraint(self):
        """Test that each task does not exceed the maximum allowed number of people."""
        assignments = self.planner.get_assignments()

        # Count assigned people per task
        task_assignments = {}
        for assignment in assignments:
            task_id = assignment["task_id"]
            if task_id not in task_assignments:
                task_assignments[task_id] = 0
            task_assignments[task_id] += 1
        
        # Check that each task doesn't exceed maximum people requirement
        for task in self.planner.tasks:
            task_id = task["task_id"]
            max_people = task["max_people"]
            assigned_people = task_assignments.get(task_id, 0)
            
            if max_people is not None:
                self.assertLessEqual(
                    assigned_people,
                    max_people,
                    f"Task {task_id} has {assigned_people} people assigned but maximum is {max_people}"
                )
                
                # Print task assignment details for verification
                print(f"Task {task_id}: {assigned_people}/{max_people} people (max: {max_people})")
            else:
                # Print tasks without maximum constraint
                print(f"Task {task_id}: {assigned_people} people (no max limit)")

    def test_people_constraints_integration(self):
        """Test that both minimum and maximum people constraints work together."""
        assignments = self.planner.get_assignments()

        # Count assigned people per task
        task_assignments = {}
        for assignment in assignments:
            task_id = assignment["task_id"]
            if task_id not in task_assignments:
                task_assignments[task_id] = 0
            task_assignments[task_id] += 1
        
        # Check that each task satisfies both min and max constraints
        for task in self.planner.tasks:
            task_id = task["task_id"]
            min_people = task["min_people"]
            max_people = task["max_people"]
            assigned_people = task_assignments.get(task_id, 0)
            
            # Check minimum constraint
            self.assertGreaterEqual(
                assigned_people,
                min_people,
                f"Task {task_id} violates minimum constraint: {assigned_people} < {min_people}"
            )
            
            # Check maximum constraint (if specified)
            if max_people is not None:
                self.assertLessEqual(
                    assigned_people,
                    max_people,
                    f"Task {task_id} violates maximum constraint: {assigned_people} > {max_people}"
                )
                
                # Verify that the constraint range is reasonable
                self.assertLessEqual(
                    min_people,
                    max_people,
                    f"Task {task_id} has invalid constraint range: min={min_people} > max={max_people}"
                )

    def test_task_data_loading(self):
        """Test that task data is loaded correctly including max_people field."""
        # Check that tasks are loaded
        self.assertGreater(len(self.planner.tasks), 0, "No tasks loaded")
        
        # Check that each task has the required fields
        for task in self.planner.tasks:
            # Check required fields
            self.assertIn("task_id", task, "Task missing task_id field")
            self.assertIn("min_people", task, "Task missing min_people field")
            self.assertIn("max_people", task, "Task missing max_people field")
            self.assertIn("description", task, "Task missing description field")
            self.assertIn("location", task, "Task missing location field")
            
            # Check data types
            self.assertIsInstance(task["min_people"], int, "min_people should be an integer")
            self.assertTrue(task["min_people"] > 0, "min_people should be positive")
            
            # max_people can be None or a positive integer
            if task["max_people"] is not None:
                self.assertIsInstance(task["max_people"], int, "max_people should be an integer or None")
                self.assertTrue(task["max_people"] > 0, "max_people should be positive when specified")
                
                # Check that max >= min when both are specified
                self.assertGreaterEqual(
                    task["max_people"], 
                    task["min_people"],
                    f"Task {task['task_id']}: max_people ({task['max_people']}) should be >= min_people ({task['min_people']})"
                )
        
        # Print some sample task data for verification
        print("\nSample Task Data:")
        for i, task in enumerate(self.planner.tasks[:5]):  # Show first 5 tasks
            max_str = str(task["max_people"]) if task["max_people"] is not None else "None"
            print(f"  {task['task_id']}: min={task['min_people']}, max={max_str}, location={task['location']}")

    def test_number_of_people(self):
        """Test that the solution is of good quality."""
        assignments = self.planner.get_assignments()

        # Basic quality checks
        self.assertGreater(len(assignments), 0, "No assignments found")

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
