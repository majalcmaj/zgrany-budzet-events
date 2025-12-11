debug:
	poetry run python -m flask --app flaskr.main run --debug

run:
	gunicorn --bind 0.0.0.0:5000 --workers 1 --threads 8 flaskr.main:app

lint:
	poetry run black --check .

lint-fix:
	poetry run black .

typecheck:
	poetry run mypy .

test:
	poetry run pytest

test-headed:
	poetry run pytest --headed

init-db:
	poetry run python flaskr/scripts/init_db.py
