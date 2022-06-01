#! /usr/bin/env bash
set -e
alembic revision --autogenerate -m 'change model video'
# Let the DB start
export PYTHONPATH=/home/diego/PycharmProjects/ia-api/
python app/backend_pre_start.py

# Run migrations
alembic upgrade head

# Create initial data in DB
#python app/initial_data.py
