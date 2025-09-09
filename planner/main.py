"""Main module for the planner application."""

import csv
from ortools.sat.python import cp_model
from typing import List, Dict
import sys
import os


class TaskAssignmentPlanner:
    """A planner that assigns participants to tasks using OR-Tools CP-SAT solver."""

    def __init__(self, tasks_file: str, participants_file: str):
        """Initialize the planner with data files."""
        self.tasks_file = tasks_file
        self.participants_file = participants_file
        self.tasks = []
        self.participants = []
        self.model = cp_model.CpModel()
        self.solver = cp_model.CpSolver()

        # Load data
        self._load_tasks()
        self._load_participants()

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
                reader = csv.DictReader(file)
                for row in reader:
                    self.tasks.append(
                        {
                            "task_id": row["TASK_ID"],
                            "date": row["DATE"],
                            "duration": row["DURATION"],
                            "description": row["TASK_DESC"].strip('"'),
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

                    self.participants.append(
                        {
                            "name": f"{row['FIRST_NAME']} {row['LAST_NAME']}",
                            "first_name": row["FIRST_NAME"],
                            "last_name": row["LAST_NAME"],
                            "role": row["ROLE"],
                            "obligations": obligations,
                            "priority": self._get_role_priority(row["ROLE"]),
                        }
                    )
        except Exception as e:
            print(f"Error loading participants: {e}")
            sys.exit(1)

    def _parse_time(self, time_str: str) -> int:
        """Parse time string to minutes from midnight."""
        time_str = time_str.strip()
        if "H" in time_str:
            hour = int(time_str.split("H")[0])
            minute = (
                int(time_str.split("H")[1]) if len(time_str.split("H")[1]) > 0 else 0
            )
        else:
            # Handle format like "19:30"
            parts = time_str.split(":")
            hour = int(parts[0])
            minute = int(parts[1])
        return hour * 60 + minute

    def _get_task_duration_hours(self, task: Dict) -> float:
        """Get task duration in hours."""
        duration_minutes = task["end_time"] - task["start_time"]
        return duration_minutes / 60.0

    def _get_day_number(self, date_str: str) -> int:
        """Convert date string to day number (0, 1, 2)."""
        date_map = {
            "10/10/2025": 0,  # Friday
            "11/10/2025": 1,  # Saturday
            "12/10/2025": 2,  # Sunday
        }
        return date_map.get(date_str, 0)

    def _get_role_priority(self, role: str) -> int:
        """Get priority score for role (higher = more important)."""
        priority_map = {"Permanant": 3, "Non-permanant": 2, "SNU": 1}
        return priority_map.get(role, 1)

    def _create_variables(self):
        """Create binary assignment variables."""
        for i, participant in enumerate(self.participants):
            for j, task in enumerate(self.tasks):
                var_name = f"assign_{i}_{j}"
                self.assignments[(i, j)] = self.model.NewBoolVar(var_name)

    def _add_constraints(self):
        """Add all constraints to the model."""
        self._add_each_task_assigned_constraint()
        self._add_participant_availability_constraint()
        self._add_time_conflict_constraint()
        self._add_snu_hour_limit_constraint()
        self._add_workload_balancing_constraints()

    def _add_each_task_assigned_constraint(self):
        """Each task must be assigned to exactly one participant."""
        for j, task in enumerate(self.tasks):
            self.model.Add(
                sum(self.assignments[(i, j)] for i in range(len(self.participants)))
                == 1
            )

    def _add_participant_availability_constraint(self):
        """Participants must be assigned to tasks they're obliged to attend."""
        for i, participant in enumerate(self.participants):
            for j, task in enumerate(self.tasks):
                if task["task_id"] in participant["obligations"]:
                    # Participant MUST be assigned to this task
                    self.model.Add(self.assignments[(i, j)] == 1)

    def _add_time_conflict_constraint(self):
        """Participants cannot be assigned to overlapping tasks."""
        for i in range(len(self.participants)):
            for j1, task1 in enumerate(self.tasks):
                for j2, task2 in enumerate(self.tasks):
                    if j1 != j2 and self._tasks_overlap(task1, task2):
                        # Cannot be assigned to both tasks
                        self.model.Add(
                            self.assignments[(i, j1)] + self.assignments[(i, j2)] <= 1
                        )

    def _add_snu_hour_limit_constraint(self):
        """Add 21-hour work limit constraint for SNU participants."""
        for i, participant in enumerate(self.participants):
            if participant["role"] == "SNU":
                # Calculate total minutes for SNU participant (21 hours = 1260 minutes)
                total_minutes = 0
                for j, task in enumerate(self.tasks):
                    task_minutes = task["end_time"] - task["start_time"]
                    total_minutes += task_minutes * self.assignments[(i, j)]

                # SNU participants cannot work more than 21 hours (1260 minutes)
                self.model.Add(total_minutes <= 1260)

    def _add_workload_balancing_constraints(self):
        """Add constraints to balance workload among participants."""
        # Equal treatment: all participants should have reasonable number of tasks
        max_tasks_per_participant = 6  # Reasonable upper limit
        min_tasks_per_participant = 1  # Everyone should have at least one task

        for i in range(len(self.participants)):
            total_tasks = sum(self.assignments[(i, j)] for j in range(len(self.tasks)))
            self.model.Add(total_tasks <= max_tasks_per_participant)
            self.model.Add(total_tasks >= min_tasks_per_participant)

    def _tasks_overlap(self, task1: Dict, task2: Dict) -> bool:
        """Check if two tasks overlap in time."""
        if task1["day"] != task2["day"]:
            return False

        # Check time overlap
        start1, end1 = task1["start_time"], task1["end_time"]
        start2, end2 = task2["start_time"], task2["end_time"]

        return not (end1 <= start2 or end2 <= start1)

    def _set_objective(self):
        """Set optimization objective."""
        # Equal treatment for all participants (except SNU hour limits)
        objective_terms = []

        # Simple objective: maximize total assignments (treat everyone equally)
        for i, participant in enumerate(self.participants):
            for j, task in enumerate(self.tasks):
                # Equal weight for all participants
                objective_terms.append(self.assignments[(i, j)])

        # Workload balancing: minimize variance in task distribution
        # Add penalty for participants with too many tasks
        for i in range(len(self.participants)):
            workload = sum(self.assignments[(i, j)] for j in range(len(self.tasks)))
            # Penalize high workload linearly to encourage balance
            objective_terms.append(-1 * workload)

        self.model.Maximize(sum(objective_terms))

    def solve(self) -> bool:
        """Solve the assignment problem."""
        print("Solving assignment problem...")
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
                            "participant_role": participant["role"],
                            "task_id": task["task_id"],
                            "task_description": task["description"],
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

        # Group by day
        days = ["Friday (10/10/2025)", "Saturday (11/10/2025)", "Sunday (12/10/2025)"]

        for day_num in range(3):
            day_assignments = [a for a in assignments if a["day"] == day_num]
            if day_assignments:
                print(f"\n{days[day_num]}:")
                print("-" * 50)

                for assignment in sorted(day_assignments, key=lambda x: x["duration"]):
                    print(
                        f"{assignment['duration']:15} | {assignment['task_id']:6} | "
                        f"{assignment['participant']:20} ({assignment['participant_role']:12}) | "
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
                    "role": assignment["participant_role"],
                    "tasks": [],
                    "total_tasks": 0,
                }
            participant_summary[name]["tasks"].append(assignment)
            participant_summary[name]["total_tasks"] += 1

        for name, info in sorted(
            participant_summary.items(), key=lambda x: (x[1]["role"], x[0])
        ):
            print(f"\n{name} ({info['role']}) - {info['total_tasks']} tasks:")
            for task in sorted(info["tasks"], key=lambda x: (x["day"], x["duration"])):
                print(
                    f"  • {task['date']} {task['duration']} - {task['task_id']}: {task['task_description']}"
                )

    def export_to_csv(self, output_file: str):
        """Export assignments to CSV file."""
        assignments = self.get_assignments()

        with open(output_file, "w", newline="", encoding="utf-8") as file:
            fieldnames = [
                "participant",
                "participant_role",
                "task_id",
                "task_description",
                "date",
                "duration",
                "day",
            ]
            writer = csv.DictWriter(file, fieldnames=fieldnames)

            writer.writeheader()
            for assignment in assignments:
                writer.writerow(assignment)

        print(f"\nAssignments exported to: {output_file}")


def main():
    """Main entry point for the application."""
    print("Task Assignment Planner")
    print("=" * 50)

    # File paths
    tasks_file = "data/tasks.csv"
    participants_file = "data/participants.csv"
    output_file = "data/assignments.csv"

    # Check if files exist
    if not os.path.exists(tasks_file):
        print(f"Error: Tasks file not found: {tasks_file}")
        return

    if not os.path.exists(participants_file):
        print(f"Error: Participants file not found: {participants_file}")
        return

    # Create planner and solve
    planner = TaskAssignmentPlanner(tasks_file, participants_file)

    if planner.solve():
        planner.print_assignments()
        planner.export_to_csv(output_file)
    else:
        print("Failed to find a solution. You may need to adjust constraints.")


if __name__ == "__main__":
    main()
