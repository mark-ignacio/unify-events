# Unify Events

## Installation and Setup
1. Install Elasticsearch on your server (tested with v1.1.0) (http://www.elasticsearch.org/overview/elkdownloads/).  Requires at least Java 6.
	- via Homebrew: `brew install elasticsearch`
	- via apt/yum: http://www.elasticsearch.org/guide/en/elasticsearch/reference/current/setup-repositories.html
2. Start Elasticsearch
	- Unix: `bin/elasticsearch`
	- Windows: `bin/elasticsearch.bat`
	- See Linux service docs:
		- http://www.elasticsearch.org/guide/en/elasticsearch/reference/current/setup.html
		- http://www.elasticsearch.org/guide/en/elasticsearch/reference/current/setup-service.html

3. Install Open-LDAP development headers (debian: openldap-dev, rhel: openldap-devel)
4. Install Virtualenv for Python
  - via pip: `[sudo] pip install virtualenv`
5. Create virtual environment and `cd` to it

        virtualenv ENV
        cd ENV
6. Clone repo to a subdirectory (ex. `git clone REPO_URL src`)
7. Activate virtual environment

        source bin/activate
8. `cd` to new src directory and install requirements

        cd src
        pip install -r requirements.txt
9. Set up local settings using the local_settings.templ.py file
10. Set up apache/python.wsgi using apache/python.templ.wsgi
11. If necessary, configure VirtualHosts using apache/vhost.conf template
12. Sync the database. Create a new admin user when prompted. This user should have a unique (non-NID based) username.

        python manage.py syncdb
13. If you don't intend on importing any existing calendar data, create a Main Calendar. Otherwise, skip this step

        python manage.py shell
        >>> from events.models import Calendar
        >>> c = Calendar(title='Events at UCF')
        >>> c.save()
        >>> exit()
14. Rebuild the search index

        python manage.py rebuild_index
15. Collect static files

        python manage.py collectstatic -cl


## Importing Data

### UNL Events Import
Note that this importer should only be run on a fresh database, immediately after running `python manage.py syncdb` or `python manage.py flush`.

1. cd to the new virtual environment src folder
2. Activate virtual environment

        source ../bin/activate
3. Add old events database information to settings_local.py under DATABASES name 'unlevents'
4. Run import command

        python manage.py import-unl-events
5. Rebuild the search index

        python manage.py rebuild_index
6. Ban cache and restart app as necessary

### Locations Import
1. cd to the new virtual environment src folder
2. Activate virtual environment

        source ../bin/activate
3. Make sure that MAPS_DOMAIN and LOCATION_DATA_URL are set in settings_local.py
4. Run import command

        python manage.py import-locations
5. Rebuild the search index

        python manage.py rebuild_index
6. Ban cache and restart app as necessary


## Code Contribution
Never commit directly to master. Create a branch or fork and work on the new feature. Once it is complete it will be merged back to the master branch.

If you use a branch to develop a feature, make sure to delete the old branch once it has been merged to master.


## Development

### Sass

#### Codekit Setup
This project is configured to compile .scss assets and javascript files (located in `static_files/assets/`) using Codekit 2.x. Before modifying any style-related files, create a new project with this repo in Codekit (see Codekit docs: http://incident57.com/codekit/help.html)

After creating the new project, any modifications to files in `static_files/assets/` will automatically compile and minify to their respective `static_files/static/` locations.

#### Bootstrap
This project uses the official Sass port of Twitter Bootstrap (https://github.com/twbs/bootstrap-sass) for base styling of templates. **Do not modify the files in this directory**--override variables as necessary in `static_files/assets/scss/style.scss`.

The current version of Bootstrap is v3.2.0.

To upgrade Bootstrap, download the latest tagged release and replace the `static_files/static/vendor/bootstrap/` directory contents in this repo with the downloaded `assets/` directory contents (do not copy the Bootstrap root directory.)  Make sure to compile `static_files/assets/scss/style.scss` AND `static_files/static/vendor/bootstrap/javascripts/bootstrap.js` after!

#### Font Awesome
Version 4.0.3 of Font Awesome (http://fontawesome.io/) is used as a replacement for Bootstrap's Glyphicon icon library. **Do not modify the files in this directory**--override variables as necessary in `static_files/assets/scss/style.scss`.

Note that these icons do not overwrite the Glyphicon library; both are available to use, but Font Awesome fonts are preferred. See the Font Awesome docs for usage.

To upgrade, download the latest tagged release and replace the `static_files/static/vendor/fonts/font-awesome-4.x.x/` directory in this repo with the downloaded root directory.  Make sure to compile `static_files/assets/scss/style.scss` after!

#### Theme Sass Files
All of the raw custom styles for this project are contained in separate Sass files in `static_files/assets/scss/`. When modifying stylesheets in this project, only modify the files in this directory; **do NOT modify files in `static_files/static/css/`**! Sass files compile and write to this directory.

Partial Sass files are generally separated out by function, and must be compiled in a specific order. Keep in mind the following guidelines when modifying or adding styles:

1. `_utilities.scss`  
   Where generic "helper" classes are defined.
2. `_type.scss`  
   Where generic paragraph, heading, link, list, etc. styles are defined. These can override Bootstrap-related classes.
3. `_components.scss`  
   Where generic Bootstrap component overrides (buttons, modals, panels, dropdowns, etc.) are defined.
4. `_forms.scss`  
   Where generic form-related styles are defined. These can override Bootstrap-related classes.
5. `_calendar-small.scss`  
   Styles specific to the small calendar sidebar widget, generated by the `{% calendar_widget %}` template tag. These styles do not modify the publicly-available Events Widget styles; these are managed separately in `/static_files/events-widget/`.
6. `_calendar-large.scss`  
   Styles specific to the full-size calendar (used in the frontend Calendar Month View), generated by the `{% calendar_widget %}` template tag.
7. `_layout.scss`  
   Styles related to base page structure; i.e. elements you would find in templates named `base.html` (header, navigation, sidebar, footer). View-specific styles should not be added here.
8. `_views-frontend.scss`  
   Frontend, view-specific styles. Make sure to label each view with specific comments, and group similar views together (i.e. a set of single Calendar view styles should go directly above or below already-defined Calendar view styles.)
9. `_views-backend.scss`  
   Backend, view-specific styles. Make sure to label each view with specific comments, and group similar views together (i.e. a set of single Calendar view styles should go directly above or below already-defined Calendar view styles.)
