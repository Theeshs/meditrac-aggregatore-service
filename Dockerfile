
FROM python:3.10-alpine
RUN pip install poetry
WORKDIR /app
COPY pyproject.toml poetry.lock /app/
RUN poetry config virtualenvs.create false
COPY . /app
CMD ["poetry", "run", "python", "aggregator_service.py"]
