# Planner Project

This project provides a comprehensive assignment planning solution with separate backend and frontend components.

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

## Quick Start

### Backend Setup
```bash
cd backend
poetry install
poetry run planner
```

### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

The frontend will be available at http://localhost:3000

## Data Flow

1. Python backend processes data from `backend/data/` and generates assignments in `backend/output/`
2. Frontend reads the generated assignments from `backend/output/assignments.csv`
3. Frontend displays the data using Gantt charts and other visualizations

## Deployment to GitHub Pages

The app is automatically deployed to GitHub Pages when you push to the main branch.

### Manual Deployment (for testing)

```bash
# Run the deployment script
./deploy.sh

# Preview the static build
cd frontend
npm run preview
```

### GitHub Pages Setup

1. Go to your repository settings on GitHub
2. Navigate to "Pages" in the left sidebar
3. Under "Source", select "GitHub Actions"
4. The deployment will happen automatically when you push to main

The app will be available at: `https://mhoangvslev.github.io/recordara-planner/`

### Local Development vs Production

- **Development**: Frontend reads data from `../backend/output/assignments.csv`
- **Production**: Frontend reads data from `/data/assignments.csv` (static file)

## Documentation

- [Backend Documentation](backend/README.md) - Python backend setup and usage
- [Frontend Documentation](frontend/README.md) - Nuxt.js frontend setup and usage