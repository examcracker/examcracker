
Setup Instructions

1. Download and install python 3.0 or higher (https://www.python.org/downloads/)
2. Download and install pip (https://pip.pypa.io/en/stable/installing/)
3. Checkout the source code from https://github.com/examcracker/examcracker into a directory examcracker
4. Create python virtual environment with following commands
--  python -m venv py34env (this creates a folder py34env)
--  cd py34env\Scripts
--  activate.bat
5. Go to examcracker directory created in step 4 and run the following commands
--  cd eLearningCMS
--  pip install -r requirements.txt
--  cd src
--  python manage.py makemigrations
--  python manage.py migrate
6. To run the project, go to examcracker\eLearningCMS\src and type python manage.py runserver

Execution Instructions

1. Go to py34env\Scripts and run activate.bat
2. If there are any database schema changes, run
--  python manage.py makemigrations
--  python manage.py migrate
3. To execute run python manage.py runserver
4. Open the browser and type localhost:8000 to start working

Developer Note

1. Everytime an additional package is installed, make sure its captured in requirements.txt with needed version


