# Metatrader 5 Terminal with RPYC API

This Docker image provides a lightweight environment for running the Metatrader 5 Terminal with RPYC API access. It uses the base image:

- `tobix/pywine:3.9`: Provides a Wine environment with Python. [tobix/pywine:3.9](https://github.com/webcomics/pywine)

## Features

- Runs Metatrader 5 Terminal using Wine.
- Enables access to the RPYC API and VNC (ports 18812 and 5900 respectively) for remote control.
- Includes `easy-novnc` for optional remote desktop access (requires additional configuration)

## Usage

1. **Build the image:**

```
docker build -t metatrader5-terminal .
```

2. **Run the container:**

```
docker run -d --name metatrader5-terminal \
             -p 18812:18812 \
             -p 8000:8000 \
             metatrader5-terminal
```

**OR**

```bash
sudo chmod +x run_dev_container.sh
./run_dev_container.sh
```

This command runs the container in detached mode (`-d`) and maps the container's port 18812 to the host's port 18812 (`-p 18812:18812`). You can access the RPYC API from your host at `localhost:18812`.

**Optional: Remote Desktop Access**

This image includes `easy-novnc` for potential remote desktop access. However, additional configuration is needed outside the container, such as using a reverse proxy like Caddy. Refer to the following resources for setting up remote desktop access:

- [https://www.digitalocean.com/community/tutorial-collections/how-to-set-up-a-remote-desktop-with-x2go](https://www.digitalocean.com/community/tutorial-collections/how-to-set-up-a-remote-desktop-with-x2go)
- [https://github.com/gnzsnz/ib-gateway-docker/](https://github.com/gnzsnz/ib-gateway-docker/)

# TODOs:

- upgrade to wine >= 8 as wine 7 is unstable and unsupported by MT5

## Dependencies

- Requires Docker to be installed and running.

## Additional notes

<!-- Access the MetaTrader 5 Terminal with a web browser using this Docker image: [https://github.com/fortesenselabs/trade_flow/pkgs/container/metatrader5-terminal](https://github.com/fortesenselabs/trade_flow/pkgs/container/metatrader5-terminal) -->

- The container starts the `supervisord` process to manage services within the container.
- The container utilizes the `gosu` user management tool.
- Configuration files like `menu.xml` and `supervisord.conf` are copied into the container.

<!-- - `golang:1.14-buster`: Used to build the `easy-novnc` tool for remote desktop access. -->

```Dockerfile
# Used for debugs:
# - tiger vnc server => 5900
# - easy-novnc => 8000

# 18812 => RPYC API port
```
