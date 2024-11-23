#!/usr/bin/env bash
# exit on error
set -o errexit

# Install dependencies
pip install -r requirements.txt

# Create database directory if it doesn't exist
mkdir -p instance

# Run any database initialization or migration scripts
python3 -c "
from app import app, db
with app.app_context():
    db.create_all()
"