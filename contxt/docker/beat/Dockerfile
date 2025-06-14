# Use the official Python 3.12 slim image as the base image.
FROM python:3.12-slim

# Set environment variables to ensure Python behaves as expected in Docker.
# PYTHONDOWNWRITEBYTECODE=1 prevents Python from writing .pyc files.
# PYTHONUNBUFFERED=1 ensures that Python output is not buffered, allowing for real-time logging.
ENV PYTHONDOWNWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Copy the current directory contents into the /app directory in the container.
COPY . /app

# Set the working directory inside the container to /app.
WORKDIR /app

# Create a virtual environment in the /py directory.
# Update package lists for APT.
# Install the PostgreSQL client, which is required to interact with PostgreSQL databases.
# Install additional necessary packages: build-essential (for compiling Python packages with native extensions),
# postgresql (for the database system), and musl (for lightweight and fast C standard library).
RUN python -m venv /py && \
    apt-get update && \
    apt-get install -y postgresql-client curl && \
    apt-get install -y --no-install-recommends build-essential postgresql musl && \
    # Upgrade pip to the latest version.
    /py/bin/pip install --upgrade pip && \
    /py/bin/pip install --upgrade setuptools && \
    # Install Python dependencies from the requirements.txt file.
    /py/bin/pip install -r /app/requirements.txt && \
    # Clean up by removing unnecessary packages to reduce the image size.
    apt-get purge -y --auto-remove build-essential postgresql musl && \
    rm -rf /var/lib/apt/lists/* && \
    # Add a new user named 'user' with no home directory and disabled password (for security).
    adduser --disabled-password --no-create-home user

# Add the virtual environment's bin directory to the PATH environment variable.
# This ensures that the correct Python and pip executables are used by default.
ENV PATH="/py/bin:$PATH"

# Switch to the 'user' account created earlier, which is a non-root user.
# Running the application as a non-root user increases security.
USER user
