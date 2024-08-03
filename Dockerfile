# Use a lightweight Python base image
FROM python:3.11-slim-buster

# Set the working directory
WORKDIR /app

# Install system dependencies including wget
RUN apt-get update && \
    apt-get install -y \
    sudo \
    wget \
    build-essential \
    clang \
    libssl-dev \
    libffi-dev \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# RUN useradd -m docker && echo "docker:docker" | chpasswd && adduser docker sudo

# USER docker

# Copy the application code
COPY . .

# Install application system dependencies (e.g., TA-Lib)
RUN bash scripts/install-talib.sh
# RUN bash scripts/install-pygame.sh

# Install package
RUN pip install -e .

# Set the command to run when the container starts
ENTRYPOINT ["sh"]
