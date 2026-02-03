web: gunicorn wsgi:app --workers=4 --threads=2 --bind=0.0.0.0:$PORT --timeout=120
worker: celery -A utils.tasks.celery worker --loglevel=info
beat: celery -A utils.tasks.celery beat --loglevel=info