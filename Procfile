release: python manage.py migrate
web: gunicorn booklogger.wsgi
worker: python ./manage.py process_queue
