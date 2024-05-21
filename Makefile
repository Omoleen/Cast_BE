run:
	python manage.py loaddata courses contents course_content questions answers phishing_templates
	# python manage.py x
	python manage.py runserver

shell:
	python manage.py shell_plus

migrate:
	python manage.py makemigrations
	python manage.py makemigrations --merge
	python manage.py migrate

test:
	python manage.py test

run-celery:
	celery -A Castellum worker --beat --scheduler django --loglevel=info
