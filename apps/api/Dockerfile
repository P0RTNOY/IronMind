FROM python:3.11-slim as base

WORKDIR /app

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# --- Dev/Test Stage ---
FROM base as dev
COPY requirements-dev.txt /app/requirements-dev.txt
RUN pip install --no-cache-dir -r requirements-dev.txt
COPY . /app
# Default CMD can be overridden by docker-compose for reload
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]

# --- Prod Stage ---
FROM base as prod
COPY . /app
EXPOSE 8080
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
