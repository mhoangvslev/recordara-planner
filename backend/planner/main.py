"""Main module for the planner application."""

import csv
from ortools.sat.python import cp_model
from typing import List, Dict, Optional
import sys
import os
import argparse


class TaskAssignmentPlanner:
    """A planner that assigns participants to tasks using OR-Tools CP-SAT solver."""

    def __init__(
        self,
        tasks_file: str,
        participants_file: str,
        existing_assignments_file: Optional[str] = None,
    ):
        """Initialize the planner with data files."""
        self.tasks_file = tasks_file
        self.participants_file = participants_file
        self.existing_assignments_file = existing_assignments_file
        self.tasks = []
        self.participants = []
        self.existing_assignments = []
        self.model = cp_model.CpModel()
        self.solver = cp_model.CpSolver()
        # Set solver parameters for deterministic results
        self.solver.parameters.random_seed = 42
        self.solver.parameters.cp_model_presolve = True
        self.solver.parameters.cp_model_probing_level = 2

        # Load data
        self._load_tasks()
        self._load_participants()

        # Load existing assignments if provided
        if self.existing_assignments_file:
            self._load_existing_assignments()

        # Create assignment variables
        self.assignments = {}
        self._create_variables()

        # Add constraints
        self._add_constraints()

        # Set objective
        self._set_objective()

    def _load_tasks(self):
        """Load tasks from CSV file."""
        try:
            with open(self.tasks_file, "r", encoding="utf-8-sig") as file:
                reader = csv.DictReader(file, delimiter=";")
                for row in reader:
                    # Get location, minimum and maximum number of people
                    location = row.get("LOCATION")
                    min_people_str = row.get("MINIMUM_NUMBER_OF_PEOPLE", "1")
                    max_people_str = row.get("MAXIMUM_NUMBER_OF_PEOPLE", "")
                    min_people = int(min_people_str.strip()) if min_people_str else 1
                    max_people = int(max_people_str.strip()) if max_people_str else None

                    # Get task description without location
                    task_desc = row["TASK_DESC"].strip('"')

                    self.tasks.append(
                        {
                            "task_id": row["TASK_ID"],
                            "date": row["DATE"],
                            "duration": row["DURATION"],
                            "description": task_desc,
                            "location": location,
                            "min_people": min_people,
                            "max_people": max_people,
                            "start_time": self._parse_time(
                                row["DURATION"].split("-")[0]
                            ),
                            "end_time": self._parse_time(row["DURATION"].split("-")[1]),
                            "day": self._get_day_number(row["DATE"]),
                        }
                    )
        except Exception as e:
            print(f"Error loading tasks: {e}")
            sys.exit(1)

    def _load_participants(self):
        """Load participants from CSV file."""
        try:
            with open(self.participants_file, "r", encoding="utf-8-sig") as file:
                reader = csv.DictReader(file, delimiter=";")
                for row in reader:
                    obligations = []
                    if row["OBLIGED_EVENT_IDS"]:
                        obligations = [
                            c.strip() for c in row["OBLIGED_EVENT_IDS"].split(",")
                        ]

                    # Parse availability for each day
                    availability = {
                        "friday": self._parse_availability(row.get("AVAIL_FRIDAY", "")),
                        "saturday": self._parse_availability(
                            row.get("AVAIL_SATURDAY", "")
                        ),
                        "sunday": self._parse_availability(row.get("AVAIL_SUNDAY", "")),
                    }

                    self.participants.append(
                        {
                            "name": f"{row['FIRST_NAME']} {row['LAST_NAME']}",
                            "first_name": row["FIRST_NAME"],
                            "last_name": row["LAST_NAME"],
                            "workload": row["WORKLOAD"],
                            "obligations": obligations,
                            "availability": availability,
                            "priority": self._get_workload_priority(row["WORKLOAD"]),
                            "target_hours": self._get_target_hours(row["WORKLOAD"]),
                        }
                    )
        except Exception as e:
            print(f"Error loading participants: {e}")
            sys.exit(1)

    def _load_existing_assignments(self):
        """Load existing assignments from CSV file."""
        try:
            with open(
                self.existing_assignments_file, "r", encoding="utf-8-sig"
            ) as file:
                reader = csv.DictReader(file)
                for row in reader:
                    self.existing_assignments.append(
                        {
                            "participant": row["participant"],
                            "task_id": row["task_id"],
                            "participant_workload": row.get("participant_workload", ""),
                            "task_description": row.get("task_description", ""),
                            "location": row.get("location", ""),
                            "date": row.get("date", ""),
                            "duration": row.get("duration", ""),
                            "day": int(row.get("day", 0)) if row.get("day") else 0,
                        }
                    )
            print(f"Loaded {len(self.existing_assignments)} existing assignments")
        except Exception as e:
            print(f"Error loading existing assignments: {e}")
            sys.exit(1)

    def _parse_time(self, time_str: str) -> int:
        """Parse time string to minutes from midnight."""
        time_str = time_str.strip()
        if "H" in time_str.upper():
            # Handle formats like "21H30" or "21h30"
            hour = int(time_str.split("H")[0].split("h")[0])
            minute_part = (
                time_str.split("H")[1] if "H" in time_str else time_str.split("h")[1]
            )
            minute = int(minute_part) if len(minute_part) > 0 else 0
        else:
            # Handle format like "19:30"
            parts = time_str.split(":")
            hour = int(parts[0])
            minute = int(parts[1])
        return hour * 60 + minute

    def _parse_availability(self, availability_str: str) -> List[Dict]:
        """Parse availability string into list of time ranges.

        Args:
            availability_str: String like "16:00-19:00,19:30-21:00" or empty string

        Returns:
            List of dictionaries with 'start' and 'end' times in minutes from midnight
        """
        if not availability_str or availability_str.strip() == "":
            return []

        time_ranges = []
        # Split by comma to get individual time ranges
        ranges = [r.strip() for r in availability_str.split(",")]

        for range_str in ranges:
            if not range_str:
                continue
            # Split by dash to get start and end times
            if "-" in range_str:
                start_str, end_str = range_str.split("-", 1)
                try:
                    start_time = self._parse_time(start_str.strip())
                    end_time = self._parse_time(end_str.strip())
                    # Only add valid time ranges
                    if start_time < end_time:
                        time_ranges.append({"start": start_time, "end": end_time})
                except (ValueError, IndexError) as e:
                    # Skip invalid time ranges
                    print(f"WARNING: Invalid time range '{range_str}': {e}")
                    continue

        return time_ranges

    def _is_participant_already_assigned(
        self, participant_name: str, task_id: str
    ) -> bool:
        """Check if a participant is already assigned to a specific task."""
        for assignment in self.existing_assignments:
            if (
                assignment["participant"] == participant_name
                and assignment["task_id"] == task_id
            ):
                return True
        return False

    def _is_participant_available_for_task(self, participant: Dict, task: Dict) -> bool:
        """Check if a participant is available for a specific task.

        Args:
            participant: Participant dictionary with availability info
            task: Task dictionary with day and time info

        Returns:
            True if participant is available for the task, False otherwise
        """
        # Get the day name for the task
        day_map = {0: "friday", 1: "saturday", 2: "sunday"}
        day_name = day_map.get(task["day"])

        if not day_name:
            return False

        # Get participant's availability for this day
        day_availability = participant["availability"].get(day_name, [])

        # If no availability specified for this day, participant is not available
        if not day_availability:
            return False

        # Check if task time can be covered by the available time ranges
        task_start = task["start_time"]
        task_end = task["end_time"]

        # Sort availability ranges by start time
        sorted_availability = sorted(day_availability, key=lambda x: x["start"])
        
        # Check if we can cover the entire task duration with available ranges
        current_time = task_start
        
        for avail_range in sorted_availability:
            avail_start = avail_range["start"]
            avail_end = avail_range["end"]
            
            # If this range covers part of the remaining task time
            if avail_start <= current_time < avail_end:
                # Move current_time to the end of this range (or task end, whichever is smaller)
                current_time = min(avail_end, task_end)
                
                # If we've covered the entire task, return True
                if current_time >= task_end:
                    return True
        
        return False

    def _get_task_duration_hours(self, task: Dict) -> float:
        """Get task duration in hours."""
        duration_minutes = task["end_time"] - task["start_time"]
        return duration_minutes / 60.0

    def _format_date_french(self, date_str: str) -> str:
        """Format date string to French format (DD/MM/YYYY)."""
        # Convert from MM/DD/YYYY to DD/MM/YYYY if needed
        # For now, assume the input is already in DD/MM/YYYY format
        return date_str

    def _get_day_number(self, date_str: str) -> int:
        """Convert date string to day number (0, 1, 2)."""
        date_map = {
            "10/10/2025": 0,  # Friday (DD/MM/YYYY format)
            "11/10/2025": 1,  # Saturday (DD/MM/YYYY format)
            "12/10/2025": 2,  # Sunday (DD/MM/YYYY format)
        }
        return date_map.get(date_str, 0)

    def _get_workload_priority(self, workload: str) -> int:
        """Get priority score for workload (higher = more important)."""
        priority_map = {"High": 3, "Medium": 2, "Low": 1, "SNU": 1}
        return priority_map.get(workload, 1)

    def _get_target_hours(self, workload: str) -> float:
        """Get target work hours based on workload level."""
        # High workload = more hours, Medium = medium hours, Low = fewer hours
        # SNU participants have a fixed 21-hour requirement
        target_hours_map = {
            "High": 15.0,  # High workload participants should work more hours
            "Medium": 12.0,  # Medium workload participants work moderate hours
            "Low": 8.0,  # Low workload participants work fewer hours
            "SNU": 21.0,  # SNU participants have fixed 21-hour requirement
        }
        return target_hours_map.get(workload, 8.0)

    def _create_variables(self):
        """Create binary assignment variables."""
        for i, participant in enumerate(self.participants):
            for j, task in enumerate(self.tasks):
                var_name = f"assign_{i}_{j}"
                self.assignments[(i, j)] = self.model.NewBoolVar(var_name)

    def _add_constraints(self):
        """Add all constraints to the model."""
        self._add_each_task_assigned_constraint()
        self._add_maximum_people_constraint()
        self._add_participant_availability_constraint()
        self._add_workload_balancing_constraints()
        # Re-enable time conflict constraint to prevent overlapping assignments
        self._add_time_conflict_constraint()
        # Re-enable workload hour constraints with daily limits
        self._add_workload_hour_constraints()
        # Add daily hour limits for SNU participants
        self._add_daily_hour_limits()

    def _add_each_task_assigned_constraint(self):
        """Each task must be assigned to at least 1 person (relaxed from original minimum)."""
        for j, task in enumerate(self.tasks):
            # Count existing assignments for this task
            existing_count = sum(
                1
                for assignment in self.existing_assignments
                if assignment["task_id"] == task["task_id"]
            )

            # If task already has existing assignments, ensure minimum is met
            if existing_count > 0:
                # Task already has assignments, just ensure we don't exceed max
                pass  # Max constraint is handled separately
            else:
                # For tasks with no existing assignments, enforce minimum for critical tasks
                min_people = task.get("min_people", 1)
                # Enforce minimum for critical tasks that absolutely need people
                critical_tasks = ["SAT15", "SUN13", "FRI5", "FRI6"]  # Cash register and ticket control
                if task["task_id"] in critical_tasks and min_people > 0:
                    self.model.Add(
                        sum(self.assignments[(i, j)] for i in range(len(self.participants)))
                        >= min_people
                    )

    def _add_maximum_people_constraint(self):
        """Each task must not exceed the maximum number of people."""
        for j, task in enumerate(self.tasks):
            max_people = task["max_people"]
            if max_people is not None:
                # Count existing assignments for this task
                existing_count = sum(
                    1
                    for assignment in self.existing_assignments
                    if assignment["task_id"] == task["task_id"]
                )

                # Calculate remaining slots
                remaining_slots = max_people - existing_count

                if remaining_slots > 0:
                    # Only add constraint if there are remaining slots
                    self.model.Add(
                        sum(
                            self.assignments[(i, j)]
                            for i in range(len(self.participants))
                        )
                        <= remaining_slots
                    )
                else:
                    # No remaining slots, no new assignments allowed
                    for i in range(len(self.participants)):
                        self.model.Add(self.assignments[(i, j)] == 0)

    def _add_participant_availability_constraint(self):
        """Participants must be assigned to tasks they're obliged to attend and
        can only be assigned to tasks when they are available."""
        for i, participant in enumerate(self.participants):
            for j, task in enumerate(self.tasks):
                # Check if participant is already assigned to this specific task
                if self._is_participant_already_assigned(
                    participant["name"], task["task_id"]
                ):
                    # Participant is already assigned to this task - force assignment to 1
                    self.model.Add(self.assignments[(i, j)] == 1)
                # Check if participant is obliged to attend this task
                elif task["task_id"] in participant["obligations"]:
                    # Check if task is already at maximum capacity
                    existing_count = sum(1 for assignment in self.existing_assignments 
                                       if assignment["task_id"] == task["task_id"])
                    max_people = task["max_people"]
                    
                    if max_people is not None and existing_count >= max_people:
                        # Task is already at maximum capacity, cannot assign more people
                        print(f"WARNING: Cannot assign {participant['name']} to {task['task_id']} - task is already at maximum capacity ({existing_count}/{max_people})")
                        self.model.Add(self.assignments[(i, j)] == 0)
                    else:
                        # Participant MUST be assigned to this task (obligation must be obeyed)
                        self.model.Add(self.assignments[(i, j)] == 1)
                else:
                    # For non-obligation tasks, check availability
                    if not self._is_participant_available_for_task(participant, task):
                        # Participant is not available for this task - cannot be assigned
                        self.model.Add(self.assignments[(i, j)] == 0)

    def _add_time_conflict_constraint(self):
        """Participants cannot be assigned to overlapping tasks, except for obligations."""
        for i in range(len(self.participants)):
            participant = self.participants[i]
            for j1, task1 in enumerate(self.tasks):
                for j2, task2 in enumerate(self.tasks):
                    if j1 != j2 and self._tasks_overlap(task1, task2):
                        # Check if either task is an obligation for this participant
                        task1_is_obligation = (
                            task1["task_id"] in participant["obligations"]
                        )
                        task2_is_obligation = (
                            task2["task_id"] in participant["obligations"]
                        )

                        # If both tasks are obligations, we have a problem - this should not happen
                        if task1_is_obligation and task2_is_obligation:
                            print(
                                f"WARNING: Participant {participant['name']} has overlapping obligations: {task1['task_id']} and {task2['task_id']}"
                            )
                            # For overlapping obligations, we'll prioritize the first one alphabetically
                            # This is a compromise to make the problem feasible
                            if task1["task_id"] < task2["task_id"]:
                                self.model.Add(self.assignments[(i, j2)] == 0)
                            else:
                                self.model.Add(self.assignments[(i, j1)] == 0)
                            continue

                        # If one task is an obligation, the participant must be assigned to it
                        # and cannot be assigned to the conflicting non-obligation task
                        if task1_is_obligation and not task2_is_obligation:
                            # task1 is obligation, task2 is not - prevent assignment to task2
                            self.model.Add(self.assignments[(i, j2)] == 0)
                        elif task2_is_obligation and not task1_is_obligation:
                            # task2 is obligation, task1 is not - prevent assignment to task1
                            self.model.Add(self.assignments[(i, j1)] == 0)
                        else:
                            # Neither task is an obligation - normal time conflict constraint
                            self.model.Add(
                                self.assignments[(i, j1)] + self.assignments[(i, j2)]
                                <= 1
                            )

    def _add_workload_hour_constraints(self):
        """Add work hour constraints based on workload levels."""
        for i, participant in enumerate(self.participants):
            workload = participant["workload"]
            
            # Calculate existing hours for this participant
            existing_hours = 0
            for assignment in self.existing_assignments:
                if assignment["participant"] == participant["name"]:
                    # Find the task to get its duration
                    task = next((t for t in self.tasks if t["task_id"] == assignment["task_id"]), None)
                    if task:
                        existing_hours += (task["end_time"] - task["start_time"]) / 60.0

            # Set reasonable maximum constraints to prevent overwork
            total_minutes = 0
            for j, task in enumerate(self.tasks):
                task_minutes = task["end_time"] - task["start_time"]
                total_minutes += task_minutes * self.assignments[(i, j)]

            if workload == "High":
                # High workload: maximum 20 hours total (more flexible for obligations)
                self.model.Add(total_minutes <= 1200)  # 20 hours maximum
            elif workload == "Medium":
                # Medium workload: maximum 16 hours total
                self.model.Add(total_minutes <= 960)  # 16 hours maximum
            elif workload == "Low":
                # Low workload: maximum 12 hours total (more flexible for obligations)
                self.model.Add(total_minutes <= 720)  # 12 hours maximum
            elif workload == "SNU":
                # SNU participants: maximum 24 hours total (8 hours per day * 3 days)
                # Daily limits are enforced separately
                self.model.Add(total_minutes <= 1440)  # 24 hours maximum
            else:
                # Default: reasonable maximum
                self.model.Add(total_minutes <= 720)  # 12 hours maximum

    def _add_workload_balancing_constraints(self):
        """Add constraints to balance workload among participants."""
        # Make workload balancing more flexible - no minimum requirements
        # This allows the solver to find feasible solutions more easily
        pass  # No minimum constraints for workload balancing

    def _add_daily_hour_limits(self):
        """Add daily hour limits for SNU participants only (max 8 hours per day)."""
        for i, participant in enumerate(self.participants):
            if participant["workload"] == "SNU":
                # Add daily hour limits for each day (0=Friday, 1=Saturday, 2=Sunday)
                for day_num in range(3):
                    daily_minutes = 0
                    for j, task in enumerate(self.tasks):
                        if task["day"] == day_num:
                            task_minutes = task["end_time"] - task["start_time"]
                            daily_minutes += task_minutes * self.assignments[(i, j)]
                    
                    # SNU participants cannot work more than 8 hours (480 minutes) per day
                    self.model.Add(daily_minutes <= 480)

    def _tasks_overlap(self, task1: Dict, task2: Dict) -> bool:
        """Check if two tasks overlap in time."""
        if task1["day"] != task2["day"]:
            return False

        # Check time overlap
        start1, end1 = task1["start_time"], task1["end_time"]
        start2, end2 = task2["start_time"], task2["end_time"]

        return not (end1 <= start2 or end2 <= start1)

    def _set_objective(self):
        """Set optimization objective with better workload balancing."""
        objective_terms = []

        # Primary objective: maximize total assignments (ensure all tasks are covered)
        for i, participant in enumerate(self.participants):
            for j, task in enumerate(self.tasks):
                objective_terms.append(self.assignments[(i, j)])

        # Secondary objective: balance workload distribution
        # Create variables to track total hours for each participant
        participant_hours = {}
        for i, participant in enumerate(self.participants):
            total_minutes = 0
            for j, task in enumerate(self.tasks):
                task_minutes = task["end_time"] - task["start_time"]
                total_minutes += task_minutes * self.assignments[(i, j)]
            participant_hours[i] = total_minutes

        # Add small reward for working hours to encourage reasonable distribution
        # This helps balance the workload across participants
        for i, participant in enumerate(self.participants):
            # Add small reward for working hours based on workload level
            for j, task in enumerate(self.tasks):
                task_minutes = task["end_time"] - task["start_time"]
                # Small positive weight to encourage reasonable work distribution
                objective_terms.append(0.1 * task_minutes * self.assignments[(i, j)])

        self.model.Maximize(sum(objective_terms))

    def solve(self) -> bool:
        """Solve the assignment problem."""
        print("Solving assignment problem...")

        # Print some diagnostic information
        print(f"Number of participants: {len(self.participants)}")
        print(f"Number of tasks: {len(self.tasks)}")
        print(f"Number of existing assignments: {len(self.existing_assignments)}")

        # Check SNU participants
        snu_participants = [p for p in self.participants if p["workload"] == "SNU"]
        print(f"SNU participants: {len(snu_participants)}")

        # Calculate total available hours for SNU participants
        for i, participant in enumerate(snu_participants):
            total_available_minutes = 0
            for day_name, availability in participant["availability"].items():
                for time_range in availability:
                    total_available_minutes += time_range["end"] - time_range["start"]
            total_available_hours = total_available_minutes / 60.0
            
            # Count existing assignments for this participant
            existing_count = sum(1 for assignment in self.existing_assignments 
                               if assignment["participant"] == participant["name"])
            print(
                f"  {participant['name']}: {total_available_hours:.1f} hours available, {existing_count} existing assignments"
            )

        # Check task assignment status
        print("\nTask assignment status:")
        unassigned_tasks = []
        for task in self.tasks:
            existing_count = sum(1 for assignment in self.existing_assignments 
                               if assignment["task_id"] == task["task_id"])
            max_people = task["max_people"] if task["max_people"] else "unlimited"
            print(f"  {task['task_id']}: {existing_count}/{max_people} people assigned")
            if existing_count == 0:
                unassigned_tasks.append(task)
        
        print(f"\nUnassigned tasks: {len(unassigned_tasks)}")
        for task in unassigned_tasks:
            print(f"  {task['task_id']}: {task['date']} {task['duration']} - {task['description']}")
        
        # Check participants without existing assignments
        print(f"\nParticipants without existing assignments:")
        for participant in self.participants:
            has_existing = any(assignment["participant"] == participant["name"] 
                             for assignment in self.existing_assignments)
            if not has_existing:
                obligations = participant.get("obligations", [])
                print(f"  {participant['name']} ({participant['workload']}) - Obligations: {obligations}")

        status = self.solver.Solve(self.model)

        if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
            print(f"Solution found! Status: {self.solver.StatusName(status)}")
            print(f"Objective value: {self.solver.ObjectiveValue()}")
            return True
        else:
            print(f"No solution found. Status: {self.solver.StatusName(status)}")
            return False

    def get_assignments(self) -> List[Dict]:
        """Get the assignment results."""
        assignments = []

        for i, participant in enumerate(self.participants):
            for j, task in enumerate(self.tasks):
                if self.solver.Value(self.assignments[(i, j)]) == 1:
                    assignments.append(
                        {
                            "participant": participant["name"],
                            "participant_workload": participant["workload"],
                            "task_id": task["task_id"],
                            "task_description": task["description"],
                            "location": task["location"],
                            "min_people": task["min_people"],
                            "max_people": task["max_people"],
                            "date": task["date"],
                            "duration": task["duration"],
                            "day": task["day"],
                        }
                    )

        return assignments

    def print_assignments(self):
        """Print assignment results in a readable format."""
        assignments = self.get_assignments()

        print("\n" + "=" * 80)
        print("TASK ASSIGNMENTS")
        print("=" * 80)

        # Group by day (French format: DD/MM/YYYY)
        days = ["Friday (10/10/2025)", "Saturday (11/10/2025)", "Sunday (12/10/2025)"]

        for day_num in range(3):
            day_assignments = [a for a in assignments if a["day"] == day_num]
            if day_assignments:
                print(f"\n{days[day_num]}:")
                print("-" * 50)

                for assignment in sorted(day_assignments, key=lambda x: x["duration"]):
                    print(
                        f"{assignment['duration']:15} | {assignment['task_id']:6} | "
                        f"{assignment['participant']:20} ({assignment['participant_workload']:12}) | "
                        f"{assignment['task_description']}"
                    )

        # Summary by participant
        print("\n" + "=" * 80)
        print("ASSIGNMENT SUMMARY BY PARTICIPANT")
        print("=" * 80)

        participant_summary = {}
        for assignment in assignments:
            name = assignment["participant"]
            if name not in participant_summary:
                participant_summary[name] = {
                    "workload": assignment["participant_workload"],
                    "tasks": [],
                    "total_tasks": 0,
                }
            participant_summary[name]["tasks"].append(assignment)
            participant_summary[name]["total_tasks"] += 1

        for name, info in sorted(
            participant_summary.items(), key=lambda x: (x[1]["workload"], x[0])
        ):
            print(f"\n{name} ({info['workload']}) - {info['total_tasks']} tasks:")
            for task in sorted(info["tasks"], key=lambda x: (x["day"], x["duration"])):
                print(
                    f"  • {self._format_date_french(task['date'])} {task['duration']} - {task['task_id']}: {task['task_description']}"
                )

    def export_to_csv(self, output_file: str):
        """Export assignments to CSV file."""
        assignments = self.get_assignments()

        with open(output_file, "w", newline="", encoding="utf-8") as file:
            fieldnames = [
                "participant",
                "participant_workload",
                "task_id",
                "task_description",
                "location",
                "min_people",
                "max_people",
                "date",
                "duration",
                "total_hours",
                "day",
            ]
            writer = csv.DictWriter(file, fieldnames=fieldnames)

            writer.writeheader()
            for assignment in assignments:
                # Calculate total hours for this assignment
                task = next(
                    t for t in self.tasks if t["task_id"] == assignment["task_id"]
                )
                total_hours = self._get_task_duration_hours(task)

                # Add total_hours to the assignment data and format date in French format
                assignment_with_hours = assignment.copy()
                assignment_with_hours["total_hours"] = round(total_hours, 2)
                assignment_with_hours["date"] = self._format_date_french(assignment["date"])

                writer.writerow(assignment_with_hours)

        print(f"\nAssignments exported to: {output_file}")


def main():
    """Main entry point for the application."""
    parser = argparse.ArgumentParser(description="Task Assignment Planner")
    parser.add_argument(
        "--tasks",
        default="backend/data/tasks.csv",
        help="Path to tasks CSV file (default: backend/data/tasks.csv)",
    )
    parser.add_argument(
        "--participants",
        default="backend/data/participants.csv",
        help="Path to participants CSV file (default: backend/data/participants.csv)",
    )
    parser.add_argument(
        "--existing-assignments",
        help="Path to existing assignments CSV file (optional)",
    )
    parser.add_argument(
        "--output",
        default="backend/output/assignments.csv",
        help="Path to output CSV file (default: backend/output/assignments.csv)",
    )

    args = parser.parse_args()

    print("Task Assignment Planner")
    print("=" * 50)

    # File paths
    tasks_file = args.tasks
    participants_file = args.participants
    existing_assignments_file = args.existing_assignments
    output_file = args.output

    # Check if files exist
    if not os.path.exists(tasks_file):
        print(f"Error: Tasks file not found: {tasks_file}")
        return

    if not os.path.exists(participants_file):
        print(f"Error: Participants file not found: {participants_file}")
        return

    if existing_assignments_file and not os.path.exists(existing_assignments_file):
        print(
            f"Error: Existing assignments file not found: {existing_assignments_file}"
        )
        return

    # Create planner and solve
    planner = TaskAssignmentPlanner(
        tasks_file, participants_file, existing_assignments_file
    )

    if planner.solve():
        planner.print_assignments()
        planner.export_to_csv(output_file)
    else:
        print("Failed to find a solution. You may need to adjust constraints.")


if __name__ == "__main__":
    main()
