# Install TradeFlow

```bash
git clone https://github.com/FortesenseLabs/trade_flow

cd trade_flow
```

### Optional: use a virtual Python environment such as `venv`

```bash
python3 -m venv .venv # Use alternative venv manager if desired
source .venv/bin/activate
```

```bash
pip install --upgrade pip
pip install -e .
```

## Setup a docker environment

1. **Build the Docker Image Again:**

```sh
    docker build -t trade_flow .
```

2. **Run the Docker Container:**

```sh
    docker run -it trade_flow trade_flow-environment
```

3. **Run a shell (optional):**

```sh
    docker exec -it trade_flow sh
```

### Extra(s)

_This medium article can show you how to setup docker desktop for windows:_

- https://medium.com/@meghasharmaa704/install-docker-desktop-on-windows-ce0f2f987bfc

## Info:

Extensions would be called flows.
