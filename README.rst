=====
earthquake
=====

Process and display earthquake data.
Optional Module for ISDC

Quick start
-----------

1. Add "earthquake" to your DASHBOARD_PAGE_MODULES setting like this::

    DASHBOARD_PAGE_MODULES = [
        ...
        'earthquake',
    ]

    If necessary add "earthquake" in (check comment for description): 
        QUICKOVERVIEW_MODULES, 
        MAP_APPS_TO_DB_CUSTOM

    For development in virtualenv add EARTHQUAKE_PROJECT_DIR path to VENV_NAME/bin/activate:
        export PYTHONPATH=${PYTHONPATH}:\
        ${HOME}/EARTHQUAKE_PROJECT_DIR

2. To create the earthquake tables:

   python manage.py makemigrations
   python manage.py migrate earthquake --database geodb

