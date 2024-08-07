WeBook
==============================

Flexible booking and event management solution.

### Quick setup

> The next steps assume that conda is already installed

1 - <a name="step-1">Create a conda environment:</a>


```bash
conda create python=3.8 -n webook
```
2 - <a name="step-2">Activate the conda environment</a>

```bash
conda activate webook
```

3 - <a name="step-3">Install the project basic dependencies and development dependencies</a>

> Make sure you are inside the root project directory before executing the next commands.
>
> The root project directory is the directory that contains the `manage.py` file

On Linux and Mac

```bash
pip install -r requirements/local.txt
```

On Windows

```bash
pip install -r requirements\local.txt
```

4 - <a name="step-4">Configure the database connection string on the .env</a>

On Linux and Mac

```bash
cp env.sample.mac_or_linux .env
```

On Windows

```bash
copy env.sample.windows .env
```

Change the value of the variable `DATABASE_URL` inside the file` .env` with the information of the database we want to connect.

Note: Several project settings have been configured so that they can be easily manipulated using environment variables or a plain text configuration file, such as the `.env` file.
This is done with the help of a library called django-environ. We can see the formats expected by `DATABASE_URL` at https://github.com/jacobian/dj-database-url#url-schema. 

5 - <a name="step-5">Use the django-extension's `sqlcreate` management command to help to create the database</a>

On Linux:

```bash
python manage.py sqlcreate | sudo -u postgres psql -U postgres
```

On Mac:

```bash
python manage.py sqlcreate | psql
```

On Windows:

Since [there is no official support for PostgreSQL 12 on Windows 10](https://www.postgresql.org/download/windows/) (officially PostgreSQL 12 is only supported on Windows Server), we choose to use SQLite3 on Windows

6 - <a name="step-6">Run the `migrations` to finish configuring the database to able to run the project</a>


```bash
python manage.py migrate
```


### <a name="running-tests">Running the tests and coverage test</a>


```bash
coverage run -m pytest
```

### <a name="installing-npm">Installing NPM</a>


```bash
choco install -y --force nodejs
```
or use the web-browser to install it. [NodeJS](https://nodejs.org/en/download/)

## <a name="update-assets">Update assets</a>

```
Please update your APP_LOGO in the .env file. And upload the new logo to the server.
```


## <a name="troubleshooting">Troubleshooting</a>

If for some reason you get an error similar to bellow, is because the DATABASE_URL is configured to `postgres:///webook` and because of it the generated `DATABASES` settings are configured to connect on PostgreSQL using the socket mode.
In that case, you must create the database manually because the `sqlcreate` is not capable to correctly generate the SQL query in this case.

```sql
ERROR:  syntax error at or near "WITH"
LINE 1: CREATE USER  WITH ENCRYPTED PASSWORD '' CREATEDB;
                     ^
ERROR:  zero-length delimited identifier at or near """"
LINE 1: CREATE DATABASE webook WITH ENCODING 'UTF-8' OWNER "";
                                                             ^
ERROR:  syntax error at or near ";"
LINE 1: GRANT ALL PRIVILEGES ON DATABASE webook TO ;
```



```sql
ERROR:  role "myuser" already exists
ERROR:  database "webook" already exists
GRANT
```

<a name="troubleshooting-delete-database">You can delete the database and the user with the commands below and then [perform step 5 again](#step-5).</a>

> :warning: **Be very careful here!**: The commands below erase data, and should only be executed on your local development machine and **NEVER** on a production server.


On Linux:

```bash
sudo -u postgres dropdb -U postgres --if-exists webook
sudo -u postgres dropuser -U postgres --if-exists myuser
```

On Mac:

```bash
dropdb --if-exists webook
dropuser --if-exists myuser
```

## Environment Variables

### APP_TITLE
The name of the application shown to users. For instance on the log-in screen, sidemenu, and so on.

### APP_LOGO
Path to the main application logo. Shown on login screen, sidemenu, etc..

### FULLCALENDAR_LICENSEKEY
The FullCalendar License Key. Needed for rendering FullCalendar. In non-commercial use cases one can use the trial key. But in commercial context you need to use a valid key. WeBook is written with the premium version of FullCalendar in mind, so it is important this is dealt with. If the project is open source, the `'GPL-My-Project-Is-Open-Source'` key can be used instead.

### ASSET_SERVER_URL
Links to an asset server, that serves assets that can because of license constraints not be included in the repository. The way we run this internally on our environments is to simply use an NGINX server that serves out  or MDBOOTSTRAP assets to our development instances.

### USER_DEFAULT_TIMEZONE
The default timezone that each user will be assigned on-creation. If none is defined then UTC is used.
Set the timezone you expect most of your users to be in. This can later be changed on a user to user basis.

## About translations
To activate another translation you need to compile the .po files into .mo files. We do not store the .mo files
in git. It can be done very simply:

```bash
python manage.py compilemessages
```
This command will run over all available .po files and create .mo files, which are binary files optimized for
use by gettext.

Remember to also change the language code.
