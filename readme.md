# Tickup Backend API

Tickup is a FastAPI Backend to support Tickup, an awesome solution for trips and travel

## Installation

Use the package manager [pip](https://pip.pypa.io/en/stable/) to install Tickup.

```bash
pip install -r requirements.txt
```

## Usage
In the root of project, run this in cmd
```python
uvicorn main:app --reload
```
--reload flag is only for development.

Now go to the url given as output of above command and move to '/docs'
 to see the full power of Tickup
## Contributing
Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

# Migrations

We use Alembic migrations. 

Install requirements by pip.

on cmd, run 
```bash
alembic revision --autogenerate -m "whats happening in the migration e.g. 'added profile picture column'"

alembic upgrade head
```

