mig:
	python3 manage.py makemigrations
	python3 manage.py migrate

admin:
	python3 manage.py createsuperuser

celery:
	celery -A root worker -l info

install:
	uv sync

run:
	python3 ./manage.py runserver

lang:
	django-admin makemessages -l uz
	django-admin makemessages -l ru
	django-admin makemessages -l en

compile:
	django-admin compilemessages
