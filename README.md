# Froide GovPlan

A Django app that allows tracking government plans. Deployed at: https://fragdenstaat.de/koalitionstracker/


## Install stand-alone

Requires [GDAL/Geos for GeoDjango](https://docs.djangoproject.com/en/4.1/ref/contrib/gis/install/geolibs/).

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
./manage.py migrate
# Create admin user
./manage.py createsuperuser
./manage.py runserver
```


1. Go to http://localhost:8000/admin/
2. Setup a homepage in the CMS: http://localhost:8000/admin/cms/page/
3. Setup a page (could be the homepage) and then choose under advanced setting the Govplan app as application.
4. Publish that page
5. Setup a government and plans via the admin.

