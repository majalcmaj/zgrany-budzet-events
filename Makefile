MAKEFLAGS += --always-make

debug:
	poetry run python -m flask --app flaskr.main run --debug

run:
	gunicorn --bind 0.0.0.0:5000 --workers 1 --threads 8 flaskr.main:app

all-checks: lint typecheck test verify

lint:
	poetry run black --check .

lint-fix:
	poetry run isort .
	poetry run autoflake --in-place --remove-all-unused-imports --recursive .
	poetry run black .

typecheck:
	poetry run pyright

test:
	poetry run pytest -m "not e2e"

verify:
	poetry run pytest -m e2e	

verify-headed:
	poetry run pytest --headed

init-db:
	poetry run python flaskr/scripts/init_db.py

run-eventstore:
	docker run -d --name kurrentdb -it -p 2113:2113 --env "HOME=/tmp" docker.eventstore.com/kurrent-latest/kurrentdb:25.1.1-x64-8.0-bookworm-slim --rm --insecure
