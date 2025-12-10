debug:
	cd flaskr && poetry run python -m flask --app main run --debug

run:
	cd flaskr && poetry run python -m flask --app main run

lint:
	poetry run black --check flaskr/

lint-fix:
	poetry run black flaskr/

test:
	poetry run pytest

test-headed:
	poetry run pytest --headed

init-db:
	poetry run python flaskr/init_db.py
