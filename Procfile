release: python manage.py migrate
web: gunicorn --bind :8080 --workers 2 booklogger.wsgi
worker: python /app/manage.py process_queue
dev_web: python manage.py runserver 0.0.0.0:8080
