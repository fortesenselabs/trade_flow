FROM rust:slim-buster

ENV USER=root
ENV PYTHON_VERSION=3.11.3

# Install system dependencies 
RUN apt-get update && \
    apt-get install -y \
    sudo \
    build-essential \ 
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

# RUN apt-get update && \
#     apt-get install -y \
#     sudo \
#     wget \
#     curl \
#     build-essential \
#     clang \
#     libssl-dev \
#     libffi-dev \
#     python3-dev \
#     && rm -rf /var/lib/apt/lists/*

# Install Rust compiler (required for nautilus-trader)
# RUN curl -sSL https://sh.rustup.rs | sh -s -- -y && \
#     . $HOME/.cargo/env

# USER docker
# RUN useradd -m docker && echo "docker:docker" | chpasswd && adduser docker sudo

# # Copy the application code
COPY . .

# # Install application system dependencies (e.g., TA-Lib)
# RUN bash scripts/install-talib.sh
# # RUN bash scripts/install-pygame.sh

# # Install package
# RUN python -m pip install -e .

# Set the command to run when the container starts
ENTRYPOINT ["sh"]


# RUN adduser --disabled-password --gecos '' $USER
# RUN adduser $USER sudo
# RUN echo '%sudo ALL=(ALL) NOPASSWD:ALL' >> /etc/sudoers
# RUN chown -R $USER /home/$USER

# USER root 

# RUN sudo apt-get install -y python3 make build-essential libssl-dev zlib1g-dev libbz2-dev \
#     libreadline-dev libsqlite3-dev wget curl llvm libncurses5-dev libncursesw5-dev \
#     xz-utils tk-dev libffi-dev liblzma-dev python-openssl git && \
#     curl https://pyenv.run | bash && \
#     curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py | python3

# ENV HOME /home/$USER
# ENV PYENV_ROOT $HOME/.pyenv
# ENV POETRY_ROOT $HOME/.poetry
# ENV CARGO_ROOT /usr/local/cargo
# ENV PATH $PYENV_ROOT/shims:$PYENV_ROOT/bin:$PATH
# ENV PATH $POETRY_ROOT/bin:$PATH
# ENV PATH $CARGO_ROOT/bin:$PATH