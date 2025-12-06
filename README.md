# File Upload Application


## Installation

Install [Poetry](https://python-poetry.org/docs/) first. 
Then run:
```bash
poetry install
```

## Running the Application

Just 
```bash
make
```

## Testing and Linting
```
make test
make lint
```

## Activating Virtual Environment
```
$(poetry env activate)
```

## Run with Docker

1. **Build the image:**
   ```bash
   docker build -t budget .
   ```

2. **Run the container:**
   ```bash
   docker run -d -p 5000:5000 --name budget -v $(pwd)/uploads:/app/src/static/uploads budget
   ```
