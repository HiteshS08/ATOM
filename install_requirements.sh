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
  
  # Activate virtual environment
  echo "Activating virtual environment..."
  source venv/bin/activate
}

# Install backend dependencies
install_backend_deps() {
  print_header "Installing backend dependencies"
  
  echo "Upgrading pip..."
  pip install --upgrade pip
  
  echo "Installing requirements..."
  pip install -r requirements.txt
  
  # Install browser-use and playwright if not already installed
  if ! pip show browser-use &> /dev/null; then
    echo "Installing browser-use..."
    pip install browser-use
  fi
  
  if ! pip show playwright &> /dev/null; then
    echo "Installing playwright..."
    pip install playwright
    playwright install
  fi
}

# Main function
main() {
  print_header "ATOM: Installing Requirements"
  
  # Setup virtual environment
  setup_venv
  
  # Install dependencies
  install_backend_deps
  
  echo -e "\n${GREEN}All requirements have been installed successfully!${NC}"
  echo -e "You can now run the backend with ${BLUE}./run.sh${NC}"
  
  # Deactivate virtual environment
  deactivate
}

# Run main function
main