# Backend - Python Assignment Planner

The backend contains the Python assignment planner logic that processes participant and task data to generate optimal assignments.

## Features

- Processes participant data from CSV files
- Handles task assignments and scheduling
- Generates optimized assignment outputs
- Provides data for frontend visualization

## Setup

### Prerequisites

- Python 3.8+
- Poetry (for dependency management)

### Installation

```bash
cd backend
poetry install
```

This will install all required dependencies as specified in `pyproject.toml`.

## Running

### Generate Assignments

```bash
cd backend
poetry run planner
```

This will:
1. Read participant data from `data/` directory
2. Process the assignment logic
3. Generate output files in `output/` directory

## Project Structure

```
backend/
├── planner/           # Main Python package
│   ├── __init__.py
│   └── main.py        # Entry point
├── tests/             # Python tests
│   ├── __init__.py
│   └── test_assignment_planner.py
├── data/              # Input data files (CSV)
│   ├── participants.csv
│   ├── participants_anon.csv
│   ├── tasks.csv
│   ├── saumon.csv
│   └── programmation.txt
├── output/            # Generated output files
│   └── assignments.csv
├── pyproject.toml     # Python project configuration
└── poetry.lock        # Python dependencies lock file
```

## Data Files

### Input Data (`data/` directory)

- `participants.csv` - Participant information
- `participants_anon.csv` - Anonymized participant data
- `tasks.csv` - Task definitions and requirements
- `saumon.csv` - Additional data file
- `programmation.txt` - Programming/scheduling information

### Output Data (`output/` directory)

- `assignments.csv` - Generated assignment results (used by frontend)

## Development

### Running Tests

```bash
cd backend
poetry run pytest
```

### Code Structure

The main logic is contained in the `planner` package:
- `main.py` - Entry point and main processing logic
- Additional modules can be added as needed

## Dependencies

All dependencies are managed through Poetry and defined in `pyproject.toml`. Key dependencies include:

- Python standard library modules
- Data processing libraries (pandas, numpy)
- Any additional packages required for assignment logic

## Integration with Frontend

The backend generates `assignments.csv` in the `output/` directory, which is consumed by the frontend for visualization. The frontend reads this file to display Gantt charts and other assignment visualizations.
