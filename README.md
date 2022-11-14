# sd43.ru 
design exhibition of created projects


## Install

Start a new project:
`pip install git+https://github.com/Starck43/sferadesign.git`
`npm i`

Run project on localhost with Gulp:<br />
### `gulp [default|styles|scripts|scripts-compress|css-compress|deploy|rsync]`

Open [http://localhost:3000](http://localhost:3000) to view it in the browser.


## Project structure:

BASE FOLDER APPS (`sd43.ru`):
`crm` - main app
`exhibition` - designers' portfolio
`rating` - portfolio rates & reviews
`blog` - designers' articles
`ads` - sponsors' banners
`designers` - designers' pages



## Django main packages:

`django-environ` - environments with main parameters for development (.env) and production (prod.env)
`python-memcached`
`django-uuslug`
`python-slugify`
`django-debug-toolbar`
`django-static-jquery-ui`
`django-crispy-forms` - bootstrap styles in forms
`mysqlclient` - client for mySQL databases
`django-smart-selects` - auto select field's values on changing value for related table in admin
`django-tabbed-changeform-admin` - tabs structure in admin forms
`sorl-thumbnail` - thumbnail generator (requires Pillow, Wand)
`django-ckeditor` - html editor for text fields in admin
`django-watson` - search through the site ( look exhibition/apps.py for adjusting included sesarching tables )
`django-allauth` - login & register package for all users via social accounts also (needs to include 'django.contrib.sites')
