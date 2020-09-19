<h1>Template for Django project</h1>

## Available Scripts

Start new project:
### `pip install git+https://github.com/Starck43/sferadesign.git`
### `bash startproject.sh [appname]`

In the project directory run:
### `npm i`
### `npm update`

Runs the app in the development mode.<br />
### `gulp [default|styles|scripts|vendors-scripts|css-compress|browser-sync|watch|rsync]`

Open [http://localhost:3000](http://localhost:3000) to view it in the browser.


## Additional Django packages:

admin-miltiupload
### `pip install git+git://github.com/gkuhn1/django-admin-multiupload.git`

# Note
It is nessesary to change below:
1. venv/lib/python3.8/site-packages/admin-miltiupload/admin.py
'django.core.urlresolvers' to 'django.urls'
2. venv/lib/python3.8/site-packages/admin-miltiupload/templates/upload.html
{% load staticfiles %} to {% load static %}