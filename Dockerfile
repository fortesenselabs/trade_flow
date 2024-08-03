FROM ghcr.io/nautechsystems/nautilus_trader:latest

# Install system dependencies 
RUN apt-get update && \
    apt-get install -y \
    sudo \
    build-essential \ 
    clang \
    wget \
    curl \
    libbz2-dev \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory
WORKDIR /app

# Copy the application code
COPY . .

# Install application system dependencies (e.g., TA-Lib)
RUN bash scripts/install-talib.sh
# RUN bash scripts/install-pygame.sh
RUN curl -sSL https://install.python-poetry.org | python - 

# Install package
RUN python -m pip install -e .

# Set the command to run when the container starts
ENTRYPOINT ["sh"]

