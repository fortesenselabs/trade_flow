import logging
import os
from enum import IntEnum
from time import sleep
from typing import ClassVar

from rpyc.utils.classic import DEFAULT_SERVER_PORT
from metatrader5.config import DockerizedMT5TerminalConfig
from nautilus_trader.common.component import Logger as NautilusLogger


class ContainerStatus(IntEnum):
    NO_CONTAINER = 1
    CONTAINER_CREATED = 2
    CONTAINER_STARTING = 3
    CONTAINER_STOPPED = 4
    NOT_LOGGED_IN = 5
    READY = 6
    UNKNOWN = 7


class DockerizedMT5Terminal:
    """
    A class to manage starting an MetaTrader 5 docker container.

    TODO: use -> ghcr.io/fortesenselabs/metatrader5-terminal:latest as IMAGE
    """

    IMAGE: ClassVar[str] = "metatrader5-terminal:latest" 
    CONTAINER_NAME: ClassVar[str] = "nautilus-mt5"
    PORTS: ClassVar[dict[str, int]] = {"web": 8000, "vnc": 5900, "rpyc": DEFAULT_SERVER_PORT}

    def __init__(self, config: DockerizedMT5TerminalConfig):
        self.log = NautilusLogger(repr(self))
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
        except NoContainer:
            return False
        return any(b"Login successful: True" in line for line in logs.split(b"\n")) and any(b":18812" in line for line in logs.split(b"\n"))

    def start(self, wait: int | None = None) -> None:
        """
        Start the terminal.

        Parameters
        ----------
        wait : int, optional
            The seconds to wait until container is ready.

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

        self.log.debug("Starting new container")
        self._container = self._docker.containers.run(
            image=self.IMAGE,
            name=f"{self.CONTAINER_NAME}-{self.port}",
            restart_policy={"Name": "always"},
            detach=True,
            ports={
                f"{self.PORTS['vnc']}": (self.host, self.PORTS['vnc']),
                f"{self.PORTS['rpyc']}": (self.host, self.PORTS['rpyc']),
                # f"{self.PORTS['web']}": (self.host, self.PORTS['web']),
            },
            platform="amd64",
            environment={
                "MT5_ACCOUNT_NUMBER": self.account_number,
                "MT5_PASSWORD": self.password,
                "MT5_SERVER": self.server
            },
        )
        self.log.info(f"Container `{self.CONTAINER_NAME}-{self.port}` starting, waiting for ready")

        for _ in range(wait or self.timeout):
            if self.is_logged_in(container=self._container):
                break
            self.log.debug("Waiting for Terminal to start")
            sleep(1)
        else:
            raise RuntimeError(f"Terminal `{self.CONTAINER_NAME}-{self.port}` not ready")

        self.log.info(
            f"Terminal `{self.CONTAINER_NAME}-{self.port}` ready. VNC port is {self.PORTS['vnc']}",
        )

    def safe_start(self, wait: int | None = None) -> None:
        try:
            self.start(wait=wait)
        except self._docker_module.errors.APIError as e:
            raise RuntimeError("Container already exists") from e

    def stop(self) -> None:
        if self.container:
            self.container.stop()
            self.container.remove()

    def __enter__(self):
        self.start()

    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            self.stop()
        except Exception:
            logging.exception("Error stopping container")


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
