# Froide GovPlan

A Django app that allows tracking government plans. Deployed at: https://fragdenstaat.de/koalitionstracker/


## Install stand-alone

Requires [GDAL/Geos for GeoDjango](https://docs.djangoproject.com/en/4.1/ref/contrib/gis/install/geolibs/).

```bash
# Start a Postgres server with Postgis
docker compose up -d
# Setup virtualenv
python3 -m venv .venv
source .venv/bin/activate
# Install dependencies
pip install -e git+https://github.com/okfde/froide.git@main#egg=froide
pip install -e .
# Setup initial database
./manage.py migrate
# Create admin user
./manage.py createsuperuser
# Start development server
./manage.py runserver
```


1. Go to http://localhost:8000/admin/
2. Setup a homepage in the CMS: http://localhost:8000/admin/cms/page/
3. Setup a page (could be the homepage) and then choose under advanced setting the Govplan app as application.
4. Publish that page
5. Setup a government and plans via the admin.

## Possible next steps

- Use the `project` directory as a blueprint for an app that uses this repo as a depdency.
- Setup [djangocms-text-ckeditor](https://github.com/django-cms/djangocms-text-ckeditor), [djangocms-frontend](https://github.com/django-cms/djangocms-frontend) and other CMS components/
- Use Django apps for social authentication.
- Override templates in your custom project.
