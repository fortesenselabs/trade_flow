FROM rust:slim-buster

ENV USER=root
ENV PYTHON_VERSION=3.11.3

# Install system dependencies 
RUN apt-get update && \
    apt-get install -y \
    sudo \
    build-essential \ 
    clang \
    zlib1g-dev \
    libncurses5-dev \
    libgdbm-dev \
    libnss3-dev \
    libssl-dev \
    libreadline-dev \ 
    libffi-dev \
    libsqlite3-dev \
    wget \
    curl \
    libbz2-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /tmp
RUN wget https://www.python.org/ftp/python/$PYTHON_VERSION/Python-$PYTHON_VERSION.tgz \
    && tar -xzf Python-$PYTHON_VERSION.tgz \
    && cd Python-$PYTHON_VERSION \
    && ./configure --enable-optimizations \ 
    && make -j $(nproc) \
    && make altinstall

# ENV PATH="/usr/local/bin:$PATH"
RUN ln -s /usr/local/bin/python3.11 /usr/local/bin/python

# Set the working directory
WORKDIR /app

# Copy the application code
COPY . .

# Install application system dependencies (e.g., TA-Lib)
RUN bash scripts/install-talib.sh
# RUN bash scripts/install-pygame.sh

# Install package
RUN python -m pip install -e .

# Set the command to run when the container starts
ENTRYPOINT ["sh"]

