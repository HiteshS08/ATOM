#!/bin/bash

# Exit on error
set -e

# Define colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Print section header
print_header() {
  echo -e "\n${PURPLE}==== $1 ====${NC}\n"
}

# Check if .env file exists and copy to backend
check_env_file() {
  print_header "Checking environment configuration"
  
  if [ -f ".env" ]; then
    echo -e "${GREEN}Found existing .env file.${NC}"
    # Extract API key from .env file
    API_KEY=$(grep TOGETHER_API_KEY .env | cut -d '=' -f2)
    if [ -z "$API_KEY" ]; then
      echo -e "${YELLOW}WARNING: TOGETHER_API_KEY not found in .env file.${NC}"
      echo -e "Please add your API key to the .env file."
    else
      echo -e "${GREEN}TOGETHER_API_KEY found in .env file.${NC}"
    fi
  else
    echo -e "${YELLOW}No .env file found. Creating one...${NC}"
    if [ -z "$TOGETHER_API_KEY" ]; then
      echo -e "${YELLOW}WARNING: TOGETHER_API_KEY environment variable is not set.${NC}"
      echo -e "Please set it by running: export TOGETHER_API_KEY=your_api_key_here"
      echo "TOGETHER_API_KEY=" > .env
    else
      echo -e "${GREEN}Using TOGETHER_API_KEY from environment.${NC}"
      echo "TOGETHER_API_KEY=$TOGETHER_API_KEY" > .env
    fi
  fi
  
  # Copy .env to backend directory
  if [ ! -d "backend" ]; then
    mkdir -p backend
  fi
  cp .env backend/.env
}

# Check if required commands are available
check_requirements() {
  print_header "Checking requirements"
  
  # Check for Python
  if ! command -v python3 &> /dev/null; then
    echo -e "${YELLOW}Python 3 is not installed. Please install Python 3 before continuing.${NC}"
    exit 1
  else
    echo -e "${GREEN}Python 3 is installed.${NC}"
  fi
  
  # Check for pip
  if ! command -v pip3 &> /dev/null; then
    echo -e "${YELLOW}pip3 is not installed. Please install pip3 before continuing.${NC}"
    exit 1
  else
    echo -e "${GREEN}pip3 is installed.${NC}"
  fi
  
  # Check for virtualenv
  if ! command -v python3 -m venv &> /dev/null; then
    echo -e "${YELLOW}Python venv module is not available. Installing it...${NC}"
    pip3 install --user virtualenv
  fi
}

# Check and create necessary files
check_files() {
  print_header "Checking necessary files"
  
  # Check if middleware.py exists in core directory
  if [ ! -f "backend/core/middleware.py" ]; then
    echo "Creating middleware.py file..."
    mkdir -p backend/core
    cat > backend/core/middleware.py << 'EOL'
from fastapi import Request
import uuid
from starlette.middleware.base import BaseHTTPMiddleware
import logging

logger = logging.getLogger(__name__)

class CorrelationIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
        request.state.correlation_id = correlation_id
        response = await call_next(request)
        response.headers["X-Correlation-ID"] = correlation_id
        return response

class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        logger.info(f"Request: {request.method} {request.url}")
        response = await call_next(request)
        logger.info(f"Response: {response.status_code}")
        return response
EOL
  fi
  
  # Check if log_config.py exists in core directory
  if [ ! -f "backend/core/log_config.py" ]; then
    echo "Creating log_config.py file..."
    mkdir -p backend/core
    cat > backend/core/log_config.py << 'EOL'
def get_log_config():
    return {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
        },
        "handlers": {
            "console": {
                "level": "INFO",
                "class": "logging.StreamHandler",
                "formatter": "default",
            },
        },
        "loggers": {
            "": {"handlers": ["console"], "level": "INFO"},
            "uvicorn": {"handlers": ["console"], "level": "INFO"},
            "uvicorn.error": {"handlers": ["console"], "level": "INFO"},
            "uvicorn.access": {"handlers": ["console"], "level": "INFO"},
        },
    }
EOL
  fi
}

# Setup virtual environment
setup_venv() {
  print_header "Setting up Python virtual environment"
  
  # Create virtual environment if it doesn't exist
  if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
  else
    echo "Virtual environment already exists."
  fi
}

# Start backend server
start_backend() {
  print_header "Starting backend server"
  
  # Activate virtual environment
  echo "Activating virtual environment..."
  source venv/bin/activate
  
  # Change to backend directory
  cd backend
  
  echo "Starting FastAPI server..."
  # Run uvicorn directly without redirecting output to allow logs to be visible
  python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
  
  # Deactivate virtual environment when done
  deactivate
  cd ..
}

# Main function
main() {
  print_header "ATOM: Agent-based Task Orchestration Module"
  
  # Check requirements
  check_requirements
  
  # Check .env file
  check_env_file
  
  # Check and create necessary files
  check_files
  
  # Setup virtual environment
  setup_venv
  
  # Start backend server only
  start_backend
}

# Run main function
main