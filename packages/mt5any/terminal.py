from __future__ import annotations
from dataclasses import dataclass
import logging
import os
from enum import IntEnum
from time import sleep
from typing import ClassVar

from rpyc.utils.classic import DEFAULT_SERVER_PORT
from trade_flow.common.logging import Logger


class ContainerStatus(IntEnum):
    """
    Enumeration of Docker container statuses for the MT5 terminal.

    Attributes:
        NO_CONTAINER (int): No container is running.
        CONTAINER_CREATED (int): Container is created but not started.
        CONTAINER_STARTING (int): Container is starting up.
        CONTAINER_STOPPED (int): Container is stopped.
        NOT_LOGGED_IN (int): Container is running but MT5 is not logged in.
        READY (int): Container is running and MT5 is logged in.
        UNKNOWN (int): Container status is unknown.
    """

    NO_CONTAINER = 1
    CONTAINER_CREATED = 2
    CONTAINER_STARTING = 3
    CONTAINER_STOPPED = 4
    NOT_LOGGED_IN = 5
    READY = 6
    UNKNOWN = 7


@dataclass
class DockerizedMT5TerminalConfig:
    """
    Configuration class for the Dockerized MetaTrader 5 Terminal.

    Attributes:
        account_number (str | None): MT5 account number to login.
        password (str | None): Password for the MT5 account.
        server (str | None): The server for the MT5 login.
        read_only_api (bool): Indicates if the API should be read-only.
        timeout (int): Timeout duration in seconds for container readiness.

    Methods:
        __repr__(): Returns a string representation of the configuration with masked sensitive information.
    """

    account_number: str | None = None
    password: str | None = None
    server: str | None = None
    read_only_api: bool = False
    timeout: int = 300

    def __repr__(self):
        """
        Mask sensitive information in the configuration when representing the class.

        Returns:
            str: String representation of the configuration.
        """
        masked_account_number = self._mask_sensitive_info(self.account_number)
        masked_password = self._mask_sensitive_info(self.password)
        return (
            f"DockerizedMT5TerminalConfig(account_number={masked_account_number}, "
            f"password={masked_password}, server={self.server}, "
            f"read_only_api={self.read_only_api}, timeout={self.timeout})"
        )

    @staticmethod
    def _mask_sensitive_info(value: str | None) -> str:
        """
        Mask sensitive information by partially showing only the first and last characters.

        Args:
            value (str | None): The string to mask.

        Returns:
            str: Masked string.
        """
        if value is None:
            return "None"
        return value[0] + "*" * (len(value) - 2) + value[-1] if len(value) > 2 else "*" * len(value)


class DockerizedMT5Terminal:
    """
    Dockerized MetaTrader 5 Terminal class.

    This class manages a Docker container running MetaTrader 5, handling the container's lifecycle and login state.

    Attributes:
        IMAGE (str): Default Docker image for the terminal.
        FALLBACK_IMAGE (str): Fallback Docker image if the default one fails.
        CONTAINER_NAME (str): Base name for the Docker container.
        PORTS (dict): Ports used by the container (e.g., for VNC and RPC).
        account_number (str): MT5 account number used for login.
        password (str): MT5 account password.
        server (str): MT5 server for login.
        read_only_api (bool): If the API is in read-only mode.
        host (str): Host IP address for the Docker container.
        port (int): RPyC port for the MT5 server.
        timeout (int): Timeout for terminal readiness.
        _docker_module (module): Docker Python module.
        _docker (docker.DockerClient): Docker client instance.
        _container (docker.models.containers.Container | None): Docker container instance.

    Methods:
        start(wait: int | None = None): Start the container and wait until it's logged in.
        stop(): Stop the container if it's running.
        safe_start(wait: int | None = None): Safely start the container.
        is_logged_in(container) -> bool: Check if the MT5 terminal is logged in.
        container_status -> ContainerStatus: Determine the current container status.
        _detect_platform() -> str: Detect platform dynamically for Docker compatibility.
        __enter__(): Start the container using the context manager.
        __exit__(exc_type, exc_val, exc_tb): Stop the container using the context manager.
    """

    IMAGE: ClassVar[str] = "metatrader5-terminal:latest"
    FALLBACK_IMAGE: ClassVar[str] = "ghcr.io/fortesenselabs/metatrader5-terminal:latest"
    CONTAINER_NAME: ClassVar[str] = "itbot-mt5"
    PORTS: ClassVar[dict[str, int]] = {"web": 8000, "vnc": 5900, "rpyc": DEFAULT_SERVER_PORT}

    def __init__(self, config: DockerizedMT5TerminalConfig):
        """
        Initialize the DockerizedMT5Terminal with the given configuration.

        Args:
            config (DockerizedMT5TerminalConfig): Configuration instance for the terminal.
        """
        self.log = Logger(repr(self))
        self.account_number = config.account_number or os.getenv("MT5_ACCOUNT_NUMBER")
        self.password = config.password or os.getenv("MT5_PASSWORD")
        self.server = config.server or os.getenv("MT5_SERVER")

        if self.account_number is None:
            self.log.error("`account_number` not set nor available in env `MT5_ACCOUNT_NUMBER`")
            raise ValueError("`account_number` not set nor available in env `MT5_ACCOUNT_NUMBER`")
        if self.password is None:
            self.log.error("`password` not set nor available in env `MT5_PASSWORD`")
            raise ValueError("`password` not set nor available in env `MT5_PASSWORD`")
        if self.server is None:
            self.log.error("`server` not set nor available in env `MT5_SERVER`")
            raise ValueError("`server` not set nor available in env `MT5_SERVER`")

        self.read_only_api = config.read_only_api
        self.host = "127.0.0.1"
        self.port = self.PORTS["rpyc"]
        self.timeout = config.timeout

        try:
            import docker

            self._docker_module = docker
        except ImportError as e:
            raise RuntimeError(
                "Docker required for MT5 Gateway, install via `pip install docker`",
            ) from e

        self._docker = docker.from_env()
        self._container = None

    def __repr__(self):
        return f"{type(self).__name__}"

    @property
    def container_status(self) -> ContainerStatus:
        container = self.container
        if container is None:
            return ContainerStatus.NO_CONTAINER
        elif container.status == "running":
            if self.is_logged_in(container=container):
                return ContainerStatus.READY
            else:
                return ContainerStatus.CONTAINER_STARTING
        elif container.status in ("stopped", "exited"):
            return ContainerStatus.CONTAINER_STOPPED
        else:
            return ContainerStatus.UNKNOWN

    @property
    def container(self):
        if self._container is None:
            all_containers = {c.name: c for c in self._docker.containers.list(all=True)}
            self._container = all_containers.get(f"{self.CONTAINER_NAME}-{self.port}")
        return self._container

    @staticmethod
    def is_logged_in(container) -> bool:
        """
        Check if account was successfully logged in.
        """
        try:
            logs = container.logs()
        except Exception:
            return False
        return any(b"Login successful: True" in line for line in logs.split(b"\n")) and any(
            b":18812" in line for line in logs.split(b"\n")
        )

    def start(self, wait: int | None = None, restart_policy: str = "always") -> None:
        """
        Start the terminal container.

        Parameters
        ----------
        wait : int, optional
            Time in seconds to wait until the container is ready. Defaults to the class-defined timeout if not provided.

        restart_policy : str, optional
            Policy for restarting the container. Defaults to "always".
        """
        broken_statuses = (
            ContainerStatus.NOT_LOGGED_IN,
            ContainerStatus.CONTAINER_STOPPED,
            ContainerStatus.CONTAINER_CREATED,
            ContainerStatus.UNKNOWN,
        )

        self.log.info("Ensuring terminal is running")
        status = self.container_status
        if status == ContainerStatus.NO_CONTAINER:
            self.log.debug("No container, starting")
        elif status in broken_statuses:
            self.log.debug(f"{status=}, removing existing container")
            self.stop()
        elif status in (ContainerStatus.READY, ContainerStatus.CONTAINER_STARTING):
            self.log.info(f"{status=}, using existing container")
            return

        for image in [self.IMAGE, self.FALLBACK_IMAGE]:
            try:
                self.log.debug(f"Starting new container with image {image}")
                self._container = self._docker.containers.run(
                    image=image,
                    name=f"{self.CONTAINER_NAME}-{self.port}",
                    restart_policy={"Name": restart_policy},
                    detach=True,
                    ports={
                        f"{self.PORTS['vnc']}": (self.host, self.PORTS["vnc"]),
                        f"{self.PORTS['rpyc']}": (self.host, self.PORTS["rpyc"]),
                    },
                    platform=self._detect_platform(),
                    environment={
                        "MT5_ACCOUNT_NUMBER": self.account_number,
                        "MT5_PASSWORD": self.password,
                        "MT5_SERVER": self.server,
                    },
                )
                self.log.info(
                    f"Container `{self.CONTAINER_NAME}-{self.port}` starting, waiting for ready"
                )
                break
            except self._docker_module.errors.ImageNotFound:
                self.log.warning(f"Image {image} not found, trying fallback image.")
        else:
            raise RuntimeError("Failed to start the MT5 Terminal container with any image.")

        for _ in range(wait or self.timeout):
            if self.is_logged_in(container=self._container):
                break
            self.log.debug("Waiting for Terminal to start")
            sleep(0.5)  # Improved polling frequency
        else:
            raise RuntimeError(f"Terminal `{self.CONTAINER_NAME}-{self.port}` not ready")

        self.log.info(
            f"Terminal `{self.CONTAINER_NAME}-{self.port}` ready. VNC port is {self.PORTS['vnc']}"
        )

    def _detect_platform(self) -> str:
        """
        Detect the platform dynamically.
        """
        arch = os.uname().machine
        return "arm64" if arch.startswith("arm") else "amd64"

    def safe_start(self, wait: int | None = None, restart_policy: str = "always") -> None:
        try:
            self.start(wait=wait, restart_policy=restart_policy)
        except self._docker_module.errors.APIError as e:
            raise RuntimeError("Container already exists") from e

    def stop(self) -> None:
        if self.container:
            try:
                self.container.stop()
                self.container.remove()
            except self._docker_module.errors.NotFound:
                self.log.error(f"Container `{self.CONTAINER_NAME}-{self.port}` not found.")
            except Exception as e:
                self.log.exception(f"Error stopping container: {e}")

    def __enter__(self):
        self.start()

    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            self.stop()
        except Exception as e:
            logging.exception(f"Error stopping container: {e}")


# -- Exceptions -----------------------------------------------------------------------------------


class ContainerExists(Exception):
    pass


class NoContainer(Exception):
    pass


class UnknownContainerStatus(Exception):
    pass


class TerminalLoginFailure(Exception):
    pass


__all__ = ["DockerizedMT5Terminal"]
