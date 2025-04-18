# Use an official Python runtime as a parent image
FROM python:3.12-slim
ENV PROJECT_HOME=/work

# Create data directory for output
RUN mkdir /work

WORKDIR ${PROJECT_HOME}

# Install runtime dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy necessary files
COPY main.py /usr/local/bin

# Run the script when the container launches
ENTRYPOINT ["python", "/usr/local/bin/main.py"]
