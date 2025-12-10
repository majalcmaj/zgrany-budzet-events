debug:
	cd src && poetry run python -m flask --app main run --debug

run:
	cd src && poetry run python -m flask --app main run

lint:
	poetry run black --check src/

test:
	poetry run pytest

test-headed:
	poetry run pytest --headed

init-db:
	poetry run python src/init_db.py
