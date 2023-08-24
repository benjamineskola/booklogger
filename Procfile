release: .venv/bin/python manage.py migrate && tsc
web: .venv/bin/python .venv/bin/gunicorn -u www -g www --bind 127.0.0.1:3000 --workers 2 --access-logfile /var/www/logs/booklogger.eskola.uk-access.log booklogger.wsgi
worker: .venv/bin/python manage.py process_queue
dev_web: python manage.py runserver 0.0.0.0:8000
jsbuild: npm run watch
