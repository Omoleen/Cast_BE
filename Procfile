web: python manage.py makemigrations && python manage.py migrate --run-syncdb && python manage.py loaddata courses contents courses_content && gunicorn Castellum.wsgi

worker: celery -A Castellum worker —loglevel=info
