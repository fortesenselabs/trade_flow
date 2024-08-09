# TradeFlow Installation Guide

This guide outlines two methods for installing and running TradeFlow:

## Local Installation

This method installs TradeFlow directly on your machine.

**Prerequisites:**

- Git
- Python 3

**Steps:**

1. **Clone the TradeFlow Repository:**

   ```sh
   git clone https://github.com/fortesenselabs/trade_flow.git
   ```

2. **Navigate to the Project Directory:**

   ```sh
   cd trade_flow
   ```

3. **(Optional) Setup Environment:** You can choose from any of the following environment setups. First **install system dependencies:**

   ```bash
      sudo apt-get update

      sudo apt-get install -y build-essential clang wget curl git libbz2-dev python3-pip

      sudo chmod +x scripts/install-talib.sh && bash scripts/install-talib.sh

      sudo chmod +x scripts/install-pygame.sh && bash scripts/install-pygame.sh # (Optional)

      curl -sSL https://install.python-poetry.org | python -

   ```

   - **(Option A) Create a Virtual Environment:** A virtual environment helps isolate project dependencies. Here's an example using `venv`:

     ```sh
        python3 -m venv .venv  # Use a different venv manager if preferred
        source .venv/bin/activate
     ```

   - **(Option B) Create a Conda Environment:** A conda environment also helps isolate project dependencies. You can also control the version of python too:

     ```sh
     conda create --name trade_flow python=3.11  # Use the tested and recommended python version
     # using conda v4:
      conda activate trade_flow

      # OR

      # using conda v3:
      source activate trade_flow

      # Verify python version:
      python --version
     ```

4. **Install Dependencies:**

```sh
   poetry install # recommended package manager

   # OR

   pip install --upgrade pip
   pip install -e .
```

## Docker Installation

This method uses Docker containers to run TradeFlow.

**Prerequisites:**

- Docker installed and running

**Option A: Pull Pre-built Image**

1. **Pull the TradeFlow Image from GHCR:**

   ```bash
   docker pull ghcr.io/fortesenselabs/trade_flow:latest
   ```

**Option B: Build the Docker Image**

1. **Build the Image:**

   ```bash
   docker build -t trade_flow .
   ```

2. **Run the Container:**

   ```bash
   docker run -it trade_flow trade_flow-environment  # Runs TradeFlow environment
   ```

3. **(Optional) Enter the Container Shell:**

   ```bash
   docker exec -it trade_flow sh
   ```

**Additional Notes:**

- For Docker Desktop installation on Windows, refer to: [https://medium.com/@meghasharmaa704/install-docker-desktop-on-windows-ce0f2f987bfc](https://medium.com/@meghasharmaa704/install-docker-desktop-on-windows-ce0f2f987bfc) (**Note:** This is an external link)
