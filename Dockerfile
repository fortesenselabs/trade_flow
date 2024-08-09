FROM ghcr.io/nautechsystems/nautilus_trader:latest

LABEL org.opencontainers.image.source=https://github.com/fortesenselabs/trade_flow
LABEL org.opencontainers.image.description="Tradeflow Development Environment(TDE)"

# Install system dependencies 
RUN apt-get update && \
    apt-get install -y \
    sudo \
    build-essential \ 
    clang \
    wget \
    curl \
    git \
    libbz2-dev \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory
WORKDIR /app

# Copy the application code
COPY . .

# Install application system dependencies (e.g., TA-Lib)
RUN bash scripts/install-talib.sh
RUN bash scripts/install-pygame.sh
RUN curl -sSL https://install.python-poetry.org | python - 

# Install package | python -m pip install -e .
RUN poetry install 

# Set the command to run when the container starts
ENTRYPOINT ["sh"]

