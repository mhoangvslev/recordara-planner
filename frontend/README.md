# Frontend - Nuxt.js Assignment Visualizer

The frontend provides a modern web interface for visualizing assignment data with interactive charts and multilingual support.

## Features

- Interactive Gantt charts for assignment visualization
- Workload distribution analysis with box plots
- Participant and task management views
- File upload functionality
- Multilingual support (English/French)
- Responsive design

## Setup

### Prerequisites

- Node.js 18+
- npm or yarn

### Installation

```bash
cd frontend
npm install
```

## Development

### Running the Development Server

```bash
cd frontend
npm run dev
```

The frontend will be available at http://localhost:3000

### Available Scripts

```bash
npm run dev          # Start development server
npm run build        # Build for production
npm run preview      # Preview production build
npm run generate     # Generate static site
```

## Project Structure

```
frontend/
├── app.vue              # Main Vue app component
├── components/          # Vue components
│   ├── FileUpload.vue   # File upload component
│   ├── GanttChart.vue   # Gantt chart visualization
│   ├── LanguageSwitcher.vue # Language selection
│   ├── ParticipantsView.vue # Participant management
│   ├── TasksView.vue    # Task management
│   └── WorkloadBoxPlot.vue # Workload visualization
├── composables/         # Vue composables
│   └── useAssignments.js # Assignment data management
├── assets/              # Static assets
│   └── css/
│       └── main.css     # Main stylesheet
├── i18n/                # Internationalization
│   └── locales/
│       ├── en.json      # English translations
│       └── fr.json      # French translations
├── plugins/             # Vue plugins
│   └── vue-ganttastic.client.js # Gantt chart plugin
├── server/              # Nuxt server API
│   └── api/
│       ├── assignments.get.js    # Get assignments endpoint
│       └── upload-assignments.post.js # Upload endpoint
├── public/              # Public static files
│   └── data/
│       └── (no static data files)
├── package.json         # Node.js dependencies
└── nuxt.config.ts       # Nuxt configuration
```

## Components

### Core Components

- **GanttChart.vue** - Interactive Gantt chart for visualizing assignments
- **WorkloadBoxPlot.vue** - Box plot visualization for workload distribution
- **ParticipantsView.vue** - Participant management and display
- **TasksView.vue** - Task management and display
- **FileUpload.vue** - File upload functionality
- **LanguageSwitcher.vue** - Language selection component

### Composables

- **useAssignments.js** - Manages assignment data state and API interactions

## Internationalization

The app supports multiple languages:
- English (en)
- French (fr)

Language files are located in `i18n/locales/` and can be extended for additional languages.

## API Endpoints

### Server API (`server/api/`)

- `GET /api/assignments` - Retrieve assignment data
- `POST /api/upload-assignments` - Upload new assignment data

## Data Integration

### Data Loading
- Assignment data is loaded dynamically via API endpoints
- No static CSV files are bundled with the frontend
- Data is served from the backend when available

## Styling

The app uses a custom CSS framework with:
- Responsive design principles
- Modern UI components
- Consistent color scheme and typography

## Deployment

### GitHub Pages

The app is automatically deployed to GitHub Pages via GitHub Actions when pushing to the main branch.

### Manual Deployment

```bash
# Build the static site
npm run generate

# Preview the build
npm run preview
```

### Production URL

The deployed app is available at: `https://mhoangvslev.github.io/recordara-planner/`

## Browser Support

- Modern browsers (Chrome, Firefox, Safari, Edge)
- Mobile responsive design
- Progressive Web App capabilities

## Development Guidelines

- Use Vue 3 Composition API
- Follow Nuxt.js best practices
- Maintain responsive design
- Ensure accessibility compliance
- Write component documentation
