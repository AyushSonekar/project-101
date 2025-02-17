FROM python:3.9

# Set environment variable (adjust version as needed)
ENV NIXPACKS_UV_VERSION=0.4.30

# Install dependencies and create virtual environment
RUN python -m venv /opt/venv && \
    /opt/venv/bin/pip install --upgrade pip && \
    /opt/venv/bin/pip install uv==$NIXPACKS_UV_VERSION && \
    /opt/venv/bin/uv sync --no-dev --frozen

# Copy your application files into the container
COPY . /app/

# Set the working directory to /app
WORKDIR /app

# Your app's entry point (if applicable, replace this with your app's start command)
CMD ["python", "app.py"]
