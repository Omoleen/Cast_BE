export LANG=C.UTF-8
python manage.py migrate --run-syncdb & python manage.py migrate & python manage.py loaddata courses contents course_content questions answers phishing_templates & gunicorn --bind=0.0.0.0 --timeout 600 Castellum.wsgi & celery -A Castellum worker --loglevel=info & celery -A Castellum beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler
