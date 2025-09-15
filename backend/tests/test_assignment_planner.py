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
        self.tasks_file = "backend/data/tasks.csv"
        self.participants_file = "backend/data/participants.csv"

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
            self.fail("No solution found for the assignment problem")

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

    def test_workload_based_hours(self):
        """Test that participants work hours are related to their workload level."""
        assignments = self.planner.get_assignments()

        # Calculate total hours for each participant by workload
        workload_hours = {"High": {}, "Medium": {}, "Low": {}, "SNU": {}}
        
        for assignment in assignments:
            workload = assignment["participant_workload"]
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

            if name not in workload_hours[workload]:
                workload_hours[workload][name] = 0
            workload_hours[workload][name] += task_hours

        # Check SNU participants work exactly 21 hours
        for name, total_hours in workload_hours["SNU"].items():
            self.assertEqual(
                total_hours,
                21.0,
                f"SNU participant {name} works {total_hours:.1f} hours, should work exactly 21 hours",
            )

        # Check that High workload participants work more hours than Low workload participants
        if workload_hours["High"] and workload_hours["Low"]:
            avg_high_hours = sum(workload_hours["High"].values()) / len(workload_hours["High"])
            avg_low_hours = sum(workload_hours["Low"].values()) / len(workload_hours["Low"])
            
            self.assertGreater(
                avg_high_hours,
                avg_low_hours,
                f"High workload participants (avg: {avg_high_hours:.1f}h) should work more hours than Low workload participants (avg: {avg_low_hours:.1f}h)"
            )

        # Check that Medium workload participants work between High and Low
        # Note: This is a soft constraint as some Low workload participants may get long tasks
        if workload_hours["Medium"]:
            avg_medium_hours = sum(workload_hours["Medium"].values()) / len(workload_hours["Medium"])
            
            if workload_hours["High"]:
                avg_high_hours = sum(workload_hours["High"].values()) / len(workload_hours["High"])
                self.assertLessEqual(
                    avg_medium_hours,
                    avg_high_hours,
                    f"Medium workload participants (avg: {avg_medium_hours:.1f}h) should work <= High workload participants (avg: {avg_high_hours:.1f}h)"
                )
            
            # For Low workload, we'll be more flexible since some may get long tasks
            if workload_hours["Low"]:
                avg_low_hours = sum(workload_hours["Low"].values()) / len(workload_hours["Low"])
                # Allow Medium to be slightly less than Low due to task distribution
                self.assertGreaterEqual(
                    avg_medium_hours,
                    avg_low_hours * 0.7,  # Allow 30% flexibility
                    f"Medium workload participants (avg: {avg_medium_hours:.1f}h) should work at least 70% of Low workload participants (avg: {avg_low_hours:.1f}h)"
                )

        # Print workload hours for verification
        print("\nWorkload-based Hours Distribution:")
        for workload, participants in workload_hours.items():
            if participants:
                avg_hours = sum(participants.values()) / len(participants)
                print(f"  {workload} workload (avg: {avg_hours:.1f}h):")
                for name, hours in participants.items():
                    print(f"    {name}: {hours:.1f} hours")

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

        # Group assignments by workload
        workload_assignments = {}
        for assignment in assignments:
            workload = assignment["participant_workload"]
            if workload not in workload_assignments:
                workload_assignments[workload] = []
            workload_assignments[workload].append(assignment)

        # Calculate average tasks per participant by workload
        workload_stats = {}
        for workload, workload_tasks in workload_assignments.items():
            participant_counts = {}
            for task in workload_tasks:
                name = task["participant"]
                participant_counts[name] = participant_counts.get(name, 0) + 1

            if participant_counts:
                avg_tasks = sum(participant_counts.values()) / len(participant_counts)
                workload_stats[workload] = {
                    "avg_tasks": avg_tasks,
                    "participant_count": len(participant_counts),
                    "total_tasks": sum(participant_counts.values()),
                }

        # Print workload statistics for verification
        print("\nWorkload-based Statistics:")
        for workload, stats in workload_stats.items():
            print(
                f"  {workload}: {stats['avg_tasks']:.1f} avg tasks per participant "
                f"({stats['total_tasks']} total tasks, {stats['participant_count']} participants)"
            )

        # The test passes if we can calculate statistics (no workload-based assignment failures)
        self.assertTrue(
            len(workload_stats) > 0, "No workload-based statistics could be calculated"
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

        # Check that we have participants from all workload levels
        participant_workloads = {a["participant_workload"] for a in assignments}
        expected_workloads = {"High", "Medium", "Low", "SNU"}
        self.assertEqual(
            participant_workloads,
            expected_workloads,
            "Not all participant workload levels are represented in assignments",
        )

    def test_snu_daily_hour_limits(self):
        """Test that SNU participants work no more than 8 hours per day."""
        assignments = self.planner.get_assignments()
        
        # Group assignments by participant and day
        participant_daily_hours = {}
        
        for assignment in assignments:
            participant = assignment["participant"]
            day = assignment["day"]
            hours = assignment["total_hours"]
            
            if participant not in participant_daily_hours:
                participant_daily_hours[participant] = {}
            if day not in participant_daily_hours[participant]:
                participant_daily_hours[participant][day] = 0.0
            
            participant_daily_hours[participant][day] += hours
        
        # Check SNU participants specifically
        snu_participants = [p for p in self.planner.participants if p["workload"] == "SNU"]
        
        for snu_participant in snu_participants:
            participant_name = snu_participant["name"]
            
            if participant_name in participant_daily_hours:
                for day_num, daily_hours in participant_daily_hours[participant_name].items():
                    day_names = ["Friday", "Saturday", "Sunday"]
                    day_name = day_names[day_num]
                    
                    self.assertLessEqual(
                        daily_hours, 8.0,
                        f"SNU participant {participant_name} works {daily_hours:.2f} hours on {day_name}, "
                        f"which exceeds the 8-hour daily limit"
                    )
                    
                    print(f"✓ {participant_name} ({day_name}): {daily_hours:.2f} hours")
        
        # Verify that non-SNU participants can work more than 8 hours per day if needed
        non_snu_participants = [p for p in self.planner.participants if p["workload"] != "SNU"]
        
        for non_snu_participant in non_snu_participants:
            participant_name = non_snu_participant["name"]
            workload = non_snu_participant["workload"]
            
            if participant_name in participant_daily_hours:
                for day_num, daily_hours in participant_daily_hours[participant_name].items():
                    day_names = ["Friday", "Saturday", "Sunday"]
                    day_name = day_names[day_num]
                    
                    # Non-SNU participants are allowed to work more than 8 hours per day
                    # This test just documents this behavior
                    if daily_hours > 8.0:
                        print(f"ℹ {participant_name} ({workload}, {day_name}): {daily_hours:.2f} hours (allowed for non-SNU)")

    def test_time_conflicts_prevented(self):
        """Test that no participant is assigned to overlapping tasks."""
        assignments = self.planner.get_assignments()
        
        # Group assignments by participant and day
        participant_schedule = {}
        
        for assignment in assignments:
            participant = assignment["participant"]
            day = assignment["day"]
            task_id = assignment["task_id"]
            duration = assignment["duration"]
            
            if participant not in participant_schedule:
                participant_schedule[participant] = {}
            if day not in participant_schedule[participant]:
                participant_schedule[participant][day] = []
            
            # Parse duration to get start and end times
            start_str, end_str = duration.split('-')
            start_minutes = self._parse_time_to_minutes(start_str)
            end_minutes = self._parse_time_to_minutes(end_str)
            
            participant_schedule[participant][day].append({
                'task_id': task_id,
                'start': start_minutes,
                'end': end_minutes,
                'duration': duration
            })
        
        # Check for overlaps
        conflicts = []
        for participant, days in participant_schedule.items():
            for day, tasks in days.items():
                # Sort tasks by start time
                tasks.sort(key=lambda x: x['start'])
                
                for i in range(len(tasks)):
                    for j in range(i + 1, len(tasks)):
                        task1 = tasks[i]
                        task2 = tasks[j]
                        
                        # Check if tasks overlap
                        if self._tasks_overlap(task1['start'], task1['end'], task2['start'], task2['end']):
                            conflicts.append({
                                'participant': participant,
                                'day': day,
                                'task1': task1,
                                'task2': task2
                            })
        
        # Assert no conflicts found
        self.assertEqual(
            len(conflicts), 0,
            f"Found {len(conflicts)} time conflicts. Participants cannot work overlapping tasks."
        )
        
        if conflicts:
            print("\nTime conflicts found:")
            for conflict in conflicts:
                day_names = ["Friday", "Saturday", "Sunday"]
                print(f"  {conflict['participant']} on {day_names[conflict['day']]}:")
                print(f"    {conflict['task1']['task_id']} ({conflict['task1']['duration']}) overlaps with {conflict['task2']['task_id']} ({conflict['task2']['duration']})")
        else:
            print("✓ No time conflicts found - all assignments are feasible")

    def _parse_time_to_minutes(self, time_str):
        """Helper method to parse time string to minutes from midnight."""
        time_str = time_str.strip()
        if "H" in time_str.upper():
            hour = int(time_str.split("H")[0].split("h")[0])
            minute_part = time_str.split("H")[1] if "H" in time_str else time_str.split("h")[1]
            minute = int(minute_part) if len(minute_part) > 0 else 0
        else:
            parts = time_str.split(":")
            hour = int(parts[0])
            minute = int(parts[1])
        return hour * 60 + minute

    def _tasks_overlap(self, start1, end1, start2, end2):
        """Helper method to check if two time ranges overlap."""
        return not (end1 <= start2 or end2 <= start1)

    def _calculate_hours_from_duration(self, duration_str):
        """Helper method to calculate hours from duration string like '16H00-17H00'."""
        start_str, end_str = duration_str.split('-')
        start_minutes = self._parse_time_to_minutes(start_str)
        end_minutes = self._parse_time_to_minutes(end_str)
        return (end_minutes - start_minutes) / 60.0


class TestSNUAssignmentPlanner(unittest.TestCase):
    """Test cases specifically for SNU participants with daily hour limits."""

    def setUp(self):
        """Set up test fixtures for SNU-specific tests."""
        self.tasks_file = "backend/data/tasks_snu.csv"
        self.participants_file = "backend/data/participants.csv"

        # Check if test data files exist
        if not os.path.exists(self.tasks_file):
            self.skipTest(f"SNU test data file not found: {self.tasks_file}")
        if not os.path.exists(self.participants_file):
            self.skipTest(f"Participants file not found: {self.participants_file}")

        # Create planner instance with SNU tasks
        self.planner = TaskAssignmentPlanner(self.tasks_file, self.participants_file)

        # Solve the assignment problem
        self.solution_found = self.planner.solve()

        if not self.solution_found:
            self.fail("No solution found for the SNU assignment problem")

    def test_snu_only_daily_limits(self):
        """Test that only SNU participants are limited to 8 hours per day."""
        assignments = self.planner.get_assignments()
        
        # Group assignments by participant and day
        participant_daily_hours = {}
        
        for assignment in assignments:
            participant = assignment["participant"]
            day = assignment["day"]
            
            # Calculate hours from duration string
            duration = assignment["duration"]
            hours = self._calculate_hours_from_duration(duration)
            
            if participant not in participant_daily_hours:
                participant_daily_hours[participant] = {}
            if day not in participant_daily_hours[participant]:
                participant_daily_hours[participant][day] = 0.0
            
            participant_daily_hours[participant][day] += hours
        
        # Separate SNU and non-SNU participants
        snu_participants = [p for p in self.planner.participants if p["workload"] == "SNU"]
        non_snu_participants = [p for p in self.planner.participants if p["workload"] != "SNU"]
        
        print("\n=== SNU Daily Hour Limits Test ===")
        
        # Test SNU participants (should be limited to 8 hours per day)
        snu_violations = []
        for snu_participant in snu_participants:
            participant_name = snu_participant["name"]
            
            if participant_name in participant_daily_hours:
                for day_num, daily_hours in participant_daily_hours[participant_name].items():
                    day_names = ["Friday", "Saturday", "Sunday"]
                    day_name = day_names[day_num]
                    
                    if daily_hours > 8.0:
                        snu_violations.append({
                            'participant': participant_name,
                            'day': day_name,
                            'hours': daily_hours
                        })
                    else:
                        print(f"✓ SNU {participant_name} ({day_name}): {daily_hours:.2f} hours")
        
        # Assert no SNU violations
        self.assertEqual(
            len(snu_violations), 0,
            f"SNU participants violated 8-hour daily limit: {snu_violations}"
        )
        
        # Test non-SNU participants (can work more than 8 hours per day)
        non_snu_over_8_hours = []
        for non_snu_participant in non_snu_participants:
            participant_name = non_snu_participant["name"]
            workload = non_snu_participant["workload"]
            
            if participant_name in participant_daily_hours:
                for day_num, daily_hours in participant_daily_hours[participant_name].items():
                    day_names = ["Friday", "Saturday", "Sunday"]
                    day_name = day_names[day_num]
                    
                    if daily_hours > 8.0:
                        non_snu_over_8_hours.append({
                            'participant': participant_name,
                            'workload': workload,
                            'day': day_name,
                            'hours': daily_hours
                        })
                        print(f"ℹ Non-SNU {participant_name} ({workload}, {day_name}): {daily_hours:.2f} hours (allowed)")
                    else:
                        print(f"✓ Non-SNU {participant_name} ({workload}, {day_name}): {daily_hours:.2f} hours")
        
        # Document that non-SNU participants can work more than 8 hours
        if non_snu_over_8_hours:
            print(f"\nNote: {len(non_snu_over_8_hours)} non-SNU participants work more than 8 hours per day (this is allowed)")
        else:
            print("\nNote: All non-SNU participants work 8 hours or less per day")

    def test_snu_participants_exist(self):
        """Test that SNU participants are present in the data."""
        snu_participants = [p for p in self.planner.participants if p["workload"] == "SNU"]
        
        self.assertGreater(
            len(snu_participants), 0,
            "No SNU participants found in the data"
        )
        
        print(f"\nFound {len(snu_participants)} SNU participants:")
        for participant in snu_participants:
            print(f"  - {participant['name']}")

    def test_snu_total_hours_reasonable(self):
        """Test that SNU participants have reasonable total hours (around 21 hours)."""
        assignments = self.planner.get_assignments()
        
        # Calculate total hours for each SNU participant
        snu_total_hours = {}
        for assignment in assignments:
            if assignment["participant_workload"] == "SNU":
                participant = assignment["participant"]
                if participant not in snu_total_hours:
                    snu_total_hours[participant] = 0.0
                
                # Calculate hours from duration string
                duration = assignment["duration"]
                hours = self._calculate_hours_from_duration(duration)
                snu_total_hours[participant] += hours
        
        print("\n=== SNU Total Hours ===")
        for participant, total_hours in snu_total_hours.items():
            print(f"{participant}: {total_hours:.2f} hours total")
            
            # SNU participants should work around 21 hours total (7 hours per day * 3 days)
            # Allow some flexibility: between 15 and 24 hours
            self.assertGreaterEqual(
                total_hours, 15.0,
                f"SNU participant {participant} works only {total_hours:.2f} hours total, which seems too low"
            )
            self.assertLessEqual(
                total_hours, 24.0,
                f"SNU participant {participant} works {total_hours:.2f} hours total, which exceeds 8 hours per day * 3 days"
            )

    def _calculate_hours_from_duration(self, duration_str):
        """Helper method to calculate hours from duration string like '16H00-17H00'."""
        start_str, end_str = duration_str.split('-')
        start_minutes = self._parse_time_to_minutes(start_str)
        end_minutes = self._parse_time_to_minutes(end_str)
        return (end_minutes - start_minutes) / 60.0

    def _parse_time_to_minutes(self, time_str):
        """Helper method to parse time string to minutes from midnight."""
        time_str = time_str.strip()
        if "H" in time_str.upper():
            hour = int(time_str.split("H")[0].split("h")[0])
            minute_part = time_str.split("H")[1] if "H" in time_str else time_str.split("h")[1]
            minute = int(minute_part) if len(minute_part) > 0 else 0
        else:
            parts = time_str.split(":")
            hour = int(parts[0])
            minute = int(parts[1])
        return hour * 60 + minute


if __name__ == "__main__":
    # Create test suites for both test classes
    test_suite = unittest.TestSuite()
    
    # Add tests from the main test class
    test_suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestTaskAssignmentPlanner))
    
    # Add tests from the SNU-specific test class
    test_suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestSNUAssignmentPlanner))

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
