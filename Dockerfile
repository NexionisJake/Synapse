# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=off \
    FLASK_ENV=production

# Set the working directory in the container
WORKDIR /app

# Install system dependencies that might be required by Python packages
RUN apt-get update && apt-get install -y --no-install-recommends build-essential && rm -rf /var/lib/apt/lists/*

# Copy the dependencies file to the working directory
COPY requirements.txt .

# Install any needed packages specified in requirements.txt and gunicorn
RUN pip install --no-cache-dir -r requirements.txt gunicorn

# Copy the rest of the application's code to the working directory
COPY . .

# Create a non-root user and group
RUN addgroup --system synapse && adduser --system --ingroup synapse synapse
RUN chown -R synapse:synapse /app

# Make the entrypoint script executable
RUN chmod +x /app/docker-entrypoint.sh

# Switch to the non-root user
USER synapse

# Expose the port the app runs on
EXPOSE 5000

# Define the entrypoint for the container
ENTRYPOINT ["/app/docker-entrypoint.sh"]

# Define the default command to run the application
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "--timeout", "120", "app:app"]
