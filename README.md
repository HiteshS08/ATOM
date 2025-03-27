# ATOM: Agent-based Task Orchestration Module

ATOM is a system that uses AI agents to perform complex tasks. It consists of a backend built with FastAPI and a frontend built with React.

## Setup Instructions

### Prerequisites

- Python 3.8 or higher
- Node.js 14 or higher
- npm 6 or higher

### Environment Setup

1. Clone this repository
2. Create a `.env` file in the root directory with your API keys:
   ```
   TOGETHER_API_KEY=your_api_key_here
   ```

### Installing Dependencies

To install the backend dependencies in a virtual environment:

```bash
# Make the installation script executable
chmod +x install_requirements.sh

# Run the installation script
./install_requirements.sh
```

This will:
- Create a Python virtual environment in the `venv` directory
- Install all required Python packages from `requirements.txt`
- Install browser-use and playwright if needed

### Running the Backend

To run the backend server:

```bash
# Make the run script executable
chmod +x run.sh

# Run the backend server
./run.sh
```

This will:
- Activate the virtual environment
- Start the FastAPI server on http://localhost:8000
- Display all logs in the terminal

### Running the Frontend

To run the frontend server:

```bash
# Navigate to the frontend directory
cd frontend

# Install dependencies
npm install

# Start the development server
npm start
```

The frontend will be available at http://localhost:3000.

## Project Structure

- `backend/`: FastAPI backend code
  - `app/`: Application code
    - `api/`: API endpoints
    - `services/`: Service implementations
  - `core/`: Core functionality
- `frontend/`: React frontend code
  - `src/`: Source code
    - `components/`: React components
    - `services/`: API services

## Styling

The frontend uses Tailwind CSS with a custom theme based on the shadcn/ui design system. The styling is defined in:

- `frontend/tailwind.config.js`: Tailwind configuration
- `frontend/src/globals.css`: Global styles and CSS variables
- `frontend/src/components/ui/`: UI components
