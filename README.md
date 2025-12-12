# Zgrany Budżet

Authors: Grzegorz Krajewski, Artur Pawelczyk, Wojciech Skwierawski, Michał Ciesielski

## Flow

```mermaid
---
config:
  look: handDrawn
---
flowchart TD
    Start((Start)) --> MinBefore
    MinBefore[&lt;optional&gt;Minister may decide on the guidelines upfront] --> A
    A[Administrator starts the planning process, sets a deadline] --> B
    B[Department fills out forms] --> C
    C[Once the department finishes editing the form, they cannot edit it afterwards.] --> D
    D[Administrator generates a summary] --> E
    E[Minister reviews, accepts or rejects] --> F
    F{Minister accepts?} --> |No. They receive new guidelines|B
    F --> |No. Administrator receives new guidelines|D
    F --> |Yes|Stop
    Stop((Stop))
```

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

## Initialize the database
```
make init-db
```

## Run with Docker

1. **Build the image:**
   ```bash
   docker build -t budget .
   ```

2. **Run the container:**
   ```bash
   docker run -d -p 5000:5000 --name budget -v $(pwd)/uploads:/app/flaskr/static/uploads budget
   ```
