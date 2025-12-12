MAKEFLAGS += --always-make

debug:
	poetry run python -m flask --app flaskr.main run --debug

run:
	gunicorn --bind 0.0.0.0:5000 --workers 1 --threads 8 flaskr.main:app

all-checks: lint typecheck test verify

lint:
	poetry run black --check .

lint-fix:
	poetry run black .

typecheck:
	poetry run mypy --strict .

test:
	poetry run pytest -m "not e2e"

verify:
	poetry run pytest -m e2e	

verify-headed:
	poetry run pytest --headed

init-db:
	poetry run python flaskr/scripts/init_db.py
