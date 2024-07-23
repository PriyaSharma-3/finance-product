## Getting Started

Download links:

SSH clone URL: git@github.com:PriyaSharma-3/finance_product.git

HTTPS clone URL: https://github.com/PriyaSharma-3/finance_product.git

## Git New Branch
Create a local branch and commit to it
```
git checkout -b feature/branch
git add .
git commit -m "first commit"
```
### Push your code
```
git push -u feature/branch
```

## Install postgressql
```
Download and install PostgreSQL from PostgresApp.
Download and install the PostgreSQL admin tool pgAdmin.

```
You can also download from https://postgresapp.com/downloads.html

```
Download and install postgressql admin tool
https://www.postgresql.org/ftp/pgadmin/pgadmin4/v6.18/macos/ 
```

## Add new server in pgadmin
```
Open pgAdmin and add a new server.
Create a database

psql postgres
CREATE DATABASE finance; # Create dataabase

```

## Create virtual environment
```
python -m venv venv
source venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```


## install unicorn
```
pip install "uvicorn[standard]"
uvicorn main:app --reload # start server
uvicorn app.main:app --reload # when moved inside folder
```

## export python libraries if installed any
```
pip freeze > requirements.txt
```
## Create .env file
```
DATABASE_HOSTNAME=localhost
DATABASE_PORT=5432
DATABASE_PASSWORD=123
DATABASE_NAME=finance
DATABASE_USERNAME=postgres
```

## alembic
```
pip install alembic
alembic upgrade head
```

### Create new alembic file
```
alembic revision -m "create account table"
```
### create automatic new alembic table
```
alembic revision --autogenerate -m "create table"
``` 

