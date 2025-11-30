# Use a Python 3.14 slim image
FROM python:3.14-slim

# Set the working directory inside the container
WORKDIR /app

# Copy the dependency file first to leverage Docker layer caching.
COPY pyproject.toml .

# Install 'uv' and then install dependencies using 'uv'.
# Combining these into a single RUN command reduces the number of image layers.
# The '--system' flag ensures uv installs into the base Python environment.
RUN pip install uv \
    && uv pip install . --system

# Copy the application code into the container
COPY . .

# Expose the port that Uvicorn will run on
EXPOSE 8000

# Define the command to run the application using Uvicorn.
# The format is 'module_name:variable_name'.
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
