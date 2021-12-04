# Foodgramm
![YaMDb workflow](https://github.com/Sgonchar89/foodgram-project/actions/workflows/yamdb_workflow.yml/badge.svg)

### Description:
Web application for publishing recipes for various dishes.
Implemented the following functionality: authentication system, view recipes, create new recipes, update recipes, add recipes to favorites and shopping list, download a shopping list to a text file, the ability to subscribe to the authors of the recipes.
The backend part of the project uses the following technologies:
_Python3, Django, DjangoREST Framework, PostgreSQL, CI/CD - GitHub Actions, Docker, Nginx, YandexCloud_


## Project launch
###The project is deployed at: 
```
http://foodgramm.co.vu/
```
###Django's admin panel is deployed at:
```
http://foodgramm.co.vu/admin/
```
###Install Docker and Docker-compose:
```
sudo apt install docker.io 
sudo curl -L "https://github.com/docker/compose/releases/download/1.29.2/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```
###Cloning a project from GitHub:
```
git clone https://github.com/Sgonchar89/foodgram-project.git
```
###Description of the .env file:
This file contains environment variables for working with the database
```
DB_ENGINE=django.db.backends.postgresql - тут указываем, с какой БД работает приложение 

DB_NAME=<имя_базы_данных> - Here we specify the name of the database.

POSTGRES_USER=<логин> - Here you specify the login to connect to the database.

POSTGRES_PASSWORD=<пароль> - Password to connect to the database.

DB_HOST=db - The name of the service (container).

DB_PORT=5432 - DB connection port.
```
###To start the project, run the command from the `/infra` directory:
```
sudo docker-compose up
```
###Next, you need to perform database migrations and collect statics:
```
sudo docker-compose exec backend python manage.py migrate --noinput
sudo docker-compose exec backend python manage.py collectstatic --no-input 
```
###Creating a superuser:
```
sudo docker-compose exec backend python manage.py createsuperuser
```
### Loading data to the database:
To load data into the database, you can use the file `final.json`, which is located in 
directory `data/`, or generate a new file using the script `json_cleaner.py` in the folder `backend/scripts`.
The file `final.json` should be copied to the directory `backend/` and then you need to execute:
```
sudo docker-compose exec backend python manage.py loaddata final.json
```

_Author of the project - [Sergey Gonchar](https://github.com/Sgonchar89)_