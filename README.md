# Planner Project

This project has been reorganized into separate backend and frontend components.

## Project Structure

```
planner/
├── backend/           # Python backend
│   ├── planner/       # Main Python package
│   ├── tests/         # Python tests
│   ├── data/          # Input data files (CSV)
│   ├── output/        # Generated output files
│   ├── pyproject.toml # Python project configuration
│   └── poetry.lock    # Python dependencies lock file
├── frontend/          # Nuxt.js frontend
│   ├── app.vue        # Main Vue app
│   ├── components/    # Vue components
│   ├── assets/        # Static assets
│   ├── composables/   # Vue composables
│   ├── plugins/       # Vue plugins
│   ├── server/        # Nuxt server API
│   ├── package.json   # Node.js dependencies
│   └── nuxt.config.ts # Nuxt configuration
└── README.md          # This file
```

## Backend (Python)

The backend contains the Python assignment planner logic.

### Setup
```bash
cd backend
poetry install
```

### Running
```bash
cd backend
poetry run planner
```

## Frontend (Nuxt.js)

The frontend provides a web interface for visualizing the assignment data.

### Setup
```bash
cd frontend
npm install
```

### Development
```bash
cd frontend
npm run dev
```

The frontend will be available at http://localhost:3000

## Data Flow

1. Python backend processes data from `backend/data/` and generates assignments in `backend/output/`
2. Frontend reads the generated assignments from `backend/output/assignments.csv`
3. Frontend displays the data using Gantt charts and other visualizations