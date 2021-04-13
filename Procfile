release: python manage.py migrate && python manage.py loaddata demo/fixtures/*.json
web: gunicorn convbackend.wsgi --log-file -
