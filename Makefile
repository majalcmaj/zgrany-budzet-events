run:
	cd src && poetry run python -m flask --app main run

lint:
	poetry run black src/

test:
	cd src && poetry run pytest

