#!/usr/bin/env bash
# exit on error
set -o errexit

# Create instance directory
mkdir -p instance

# Install dependencies
pip install -r requirements.txt

# Run database initialization
python3 -c "
from app import init_db
init_db()
"