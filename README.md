<h1>sd43.ru web project</h1>

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

## Applications list:

BASE FOLDER APPS (`sd43.ru`):
`crm` - main app
`exhibition`
`rating` - rates & reviews


## Additional Django packages:

`django-environ`
`python-memcached`
`django-uuslug`
`python-slugify`
`django-debug-toolbar`
`django-crispy-forms`
`django-static-jquery-ui`
`django-smart-selects` - auto select field's values on changing value for related table in admin
`django-tabbed-changeform-admin` - tabs structure in admin forms
`sorl-thumbnail` - auto thumbnail generator (requires Pillow, Wand)
`django-ckeditor` - html editor for text fields in admin
`django-cleanup` - delete all related files with instance removing on disk
`django-watson` - search through the site ( look exhibition/apps.py for adjusting included sesarching tables )
`django-allauth` - login & register package for all users via social accounts also (needs to include 'django.contrib.sites')


## Favicon Package

Generate favicons with [RealFaviconGenerator](https://realfavicongenerator.net/)

To install this package:

If the site is <code>http://www.example.com</code>, you should be able to access a file named <code>http://www.example.com/favicon.ico</code>.
Put the `favicon.ico` file to your root directory `public_html`

Insert the following code in the `head` section of `base.html`:

    <link rel="apple-touch-icon" sizes="180x180" href="/apple-touch-icon.png">
    <link rel="icon" type="image/png" sizes="32x32" href="/favicon-32x32.png">
    <link rel="icon" type="image/png" sizes="16x16" href="/favicon-16x16.png">
    <link rel="manifest" href="/site.webmanifest">
    <link rel="mask-icon" href="/safari-pinned-tab.svg" color="#160d32">
    <meta name="msapplication-TileColor" content="#160d32">
    <meta name="msapplication-TileImage" content="/mstile-144x144.png">
    <meta name="theme-color" content="#ffffff">

*Optional* - Check your favicon with the [favicon checker](https://realfavicongenerator.net/favicon_checker)

