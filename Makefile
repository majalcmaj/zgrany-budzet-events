export PYTHONPATH=flaskr

debug:
	poetry run python -m flask --app main run --debug

run:
	poetry run python -m flask --app main run

lint:
	poetry run black --check .

lint-fix:
	poetry run black .

test:
	poetry run pytest

test-headed:
	poetry run pytest --headed

init-db:
	poetry run python flaskr/init_db.py
