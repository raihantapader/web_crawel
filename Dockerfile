FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy code
COPY src/ ./src/
COPY tests/ ./tests/
COPY examples/ ./examples/
COPY run_all.py .

# Create output folder
RUN mkdir -p /app/output

# Set Python path
ENV PYTHONPATH=/app/src

# Default: run ALL examples together
CMD ["python", "run_all.py"]
