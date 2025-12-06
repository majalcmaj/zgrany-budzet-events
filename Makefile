init:
	poetry run python src/init_db.py

debug:
	cd src && poetry run python -m flask --app main run --debug

run:
	cd src && poetry run python -m flask --app main run

lint:
	poetry run black src/

test:
	cd src && poetry run pytest

