#!/usr/bin/env bash
# As the instruction at https://render.com/docs/deploy-django
# Exit on error
set -o errexit

# Modify this line as needed for your package manager (pip, poetry, etc.)
pip install -r requirements.txt

# Convert static asset files
python manage.py collectstatic --no-input

# Apply any outstanding database migrations
python manage.py migrate

# Create Django Admin, setting variable in the render dashboard
# This is a workaround because shell is a paid feature of render.com
python manage.py createsuperuser --no-input || true