# Task Assignment Planner

A Python application that uses OR-Tools to optimally assign participants to tasks for a multi-day event, taking into account constraints, role priorities, and workload balancing.

## Features

- **Optimal Assignment**: Uses OR-Tools CP-SAT solver to find the best possible task assignments
- **Constraint Handling**: Respects participant availability constraints and time conflicts
- **Role-Based Priority**: Prioritizes permanent staff for critical tasks
- **Workload Balancing**: Distributes tasks fairly among participants
- **Time Conflict Detection**: Prevents double-booking of participants
- **CSV Export**: Generates detailed assignment reports

## Data Structure

### Tasks CSV (`data/tasks.csv`)
Contains event tasks with the following columns:
- `DATE`: Event date (DD/MM/YYYY format)
- `DURATION`: Time range (e.g., "16H00-19H00")
- `TASK_ID`: Unique task identifier
- `TASK_DESC`: Task description

### Participants CSV (`data/participants.csv`)
Contains participant information with the following columns:
- `FIRST_NAME`: Participant's first name
- `LAST_NAME`: Participant's last name
- `ROLE`: Role type (Permanant, Non-permanant, SNU)
- `CONSTRAINT_EVENT_IDS`: Comma-separated list of task IDs the participant cannot be assigned to

## Assignment Logic

### Constraints
1. **Each task must be assigned to exactly one participant**
2. **Participants cannot be assigned to tasks they're constrained from**
3. **No time conflicts**: Participants cannot be assigned to overlapping tasks
4. **SNU hour limits**: SNU volunteers cannot work more than 21 hours
5. **Workload limits**: Each participant has minimum and maximum task limits

### Optimization Objectives
1. **Equal Treatment**: All participants are treated equally regardless of role
2. **Workload Balancing**: Distributes tasks fairly among all participants
3. **SNU Hour Limit**: SNU volunteers cannot work more than 21 hours total

## Usage

### Prerequisites
```bash
# Install dependencies
pip install ortools pandas
```

### Running the Program
```bash
python planner/main.py
```

### Output
The program generates:
1. **Console Output**: Detailed assignment summary organized by day and participant
2. **CSV Export**: `data/assignments.csv` with all assignment details

## Example Output

```
Task Assignment Planner
==================================================
Solving assignment problem...
Solution found! Status: OPTIMAL
Objective value: 7136.0

================================================================================
TASK ASSIGNMENTS
================================================================================

Friday (10/10/2025):
--------------------------------------------------
16H00-19H00     | FRI1   | Minh-Hoang DANG      (Permanant   ) | Déchargement voitures et installation
19H30-21H00     | FRI2   | Eric FRANCO          (Permanant   ) | Accueil public
...
```

## Assignment Results Summary

The program successfully assigns all 32 tasks across 3 days to 22 participants:

- **All Participants**: Treated equally with balanced workload distribution
- **SNU Volunteers**: Limited to maximum 21 hours of work total
- **Non-Permanent Staff**: Assigned to various event tasks with balanced workload
- **Permanent Staff**: Assigned to various tasks with balanced workload

### Key Features Demonstrated:
- ✅ Respects Minh-Hoang DANG's constraints (not assigned to SAT1, SAT8)
- ✅ All participants treated equally regardless of role
- ✅ SNU volunteers respect 21-hour work limit (all under 10 hours)
- ✅ No time conflicts between assignments
- ✅ Balanced workload distribution across all participants
- ✅ All tasks assigned to exactly one participant

## Customization

You can modify the assignment logic by adjusting:
- `max_tasks_per_participant` and `min_tasks_per_participant` in `_add_workload_balancing_constraints()`
- `critical_tasks` list in `_add_role_based_constraints()`
- Priority weights in `_set_objective()`
- Time parsing logic in `_parse_time()` for different time formats

## Technical Details

- **Solver**: OR-Tools CP-SAT (Constraint Programming)
- **Problem Type**: Binary Integer Programming
- **Variables**: Binary assignment variables for each (participant, task) pair
- **Constraints**: Linear constraints for assignment rules
- **Objective**: Linear combination of role priorities and workload penalties