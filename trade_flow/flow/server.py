import os
import argparse
import pkgutil
import platform
import traceback

import trade_flow.environments
import trade_flow
from trade_flow.commons import Logger, TRADE_FLOW_SERVER_PORT
from trade_flow.flow import Flow, TaskManager
from flask import Flask, json, jsonify, request
from flask_jsonrpc.app import JSONRPC
from flask_jsonrpc.exceptions import ServerError



class Server:
    def __init__(self):
        system = os.name
        if system == "nt" or platform.system() == "Windows":
            self.basedir = os.path.join(os.path.expanduser("~"), "trade_flow")
        elif (
            system == "posix"
            or platform.system() == "Linux"
            or platform.system() == "Darwin"
        ):
            self.basedir = os.environ.get("XDG_STATE_HOME")
            if self.basedir is None:
                self.basedir = os.path.join(os.environ["HOME"], ".trade_flow")
            else:
                self.basedir = os.path.join(self.basedir, "trade_flow")
        else:
            raise NotImplementedError("Unsupported operating system")
        
        self.app = Flask(__name__)
        self.jsonrpc = JSONRPC(self.app, "/api")

        self.log_file_path = os.path.join(self.basedir, "trade_flow.log")
        self.setup_global_exception_handler()
        self.setup_logging()
        self.setup_rpc()

        self.flows: dict = dict()
        self.logger.info("Started server")

        # Initialize TaskManager
        self.task_manager = TaskManager()

    def setup_global_exception_handler(self):
        """
        Use flask to log traceback of unhandled exceptions
        """
        @self.app.errorhandler(Exception)
        def handle_exception(e):
            trace = traceback.format_exc()
            self.logger.error(f"Unhandled exception: {e}\n{trace}")
            response = {
                    "jsonrpc": "2.0",
                    "error": {
                        "code": -32603,
                        "message": "Internal server error",
                        "data": str(e),
                    },
                    "id": request.json.get("id", None) if request.json else None,
                }
            return jsonify(response), 500
    
    def setup_logging(self):
        os.makedirs(os.path.dirname(self.log_file_path), exist_ok=True)

        self.logger = Logger(name="trade_flow", filename=str(self.log_file_path))
        self.logger.info("Logging started")

        def log_request():
            if "healthy" in request.path:
                return  # No need to log all these
            if not request.path.startswith("/api"):
                self.logger.debug(request.path)
            else:
                self.logger.debug(request.json)

        self.app.before_request(log_request)

    def setup_rpc(self):
        # Environments
        self.jsonrpc.register(self.environments_available)
        # Venues
        self.jsonrpc.register(self.venues_available)
        # Agents
        self.jsonrpc.register(self.agents_available)
        # Task Management
        # self.jsonrpc.register(self.start_task)
        # self.jsonrpc.register(self.stop_task)
        # self.jsonrpc.register(self.list_tasks)

    def healthy(self):
        return "trade_flow is healthy"
    
    def get_flow(self, flow: str) -> Flow:
        """
        Will get a flow from the cache if it exists.
        Otherwise it will create the flow using from_file() and save it
        to the cache before returning it.
        """
        if flow in self.flows:
            return self.flows[flow]
        fl = Flow.from_file(flow)
        if isinstance(fl, Flow):
            self.flows[flow] = fl
            return fl
        raise ServerError(f"Could not find flow {flow}")
    
    def environments_available(self) -> list[tuple]:
        """
        List available environments in Trade Flow
        """
        try:
            environment_list = []
            for s in pkgutil.iter_modules(trade_flow.environments.__path__):
                m = pkgutil.resolve_name(f"trade_flow.environments.{s.name}")
                if hasattr(m, "cli_help"):
                    environment_list.append((s.name, m.cli_help()))
            return environment_list
        except Exception as e:
            msg = f"Error listing environments: {e}"
            self.logger.error(msg)
            raise ServerError(message=msg) from e
        
    def venues_available(self) -> list[tuple]:
        """
        List available venues in Trade Flow
        """
        try:
            venue_list = []
            for s in pkgutil.iter_modules(trade_flow.venues.__path__):
                m = pkgutil.resolve_name(f"trade_flow.venues.{s.name}")
                if hasattr(m, "cli_help"):
                    venue_list.append((s.name, m.cli_help()))
            return venue_list
        except Exception as e:
            msg = f"Error listing venues: {e}"
            self.logger.error(msg)
            raise ServerError(message=msg) from e
        
    def agents_available(self) -> list[tuple]:
        """
        List available agents in Trade Flow
        """
        try:
            agent_list = []
            for s in pkgutil.iter_modules(trade_flow.agents.__path__):
                m = pkgutil.resolve_name(f"trade_flow.agents.{s.name}")
                if hasattr(m, "cli_help"):
                    agent_list.append((s.name, m.cli_help()))
            return agent_list
        except Exception as e:
            msg = f"Error listing agents: {e}"
            self.logger.error(msg)
            raise ServerError(message=msg) from e

    def start_task(self, task_name: str, target_function_name: str, *args: str) -> str:
        """
        Start a task in a separate thread.

        Args:
        - task_name (str): Unique name for the task.
        - target_function_name (str): The name of the function to run in the thread.
        - *args: Arguments to pass to the target_function.
        
        Returns:
        - str: Success or failure message.
        """
        target_function = getattr(self, target_function_name, None)
        if target_function is None:
            return f"Function '{target_function_name}' not found."
        
        thread = self.task_manager.start_process_in_thread(task_name, target_function, *args)
        if thread:
            return f"Task '{task_name}' started successfully."
        return f"Failed to start task '{task_name}'."

    def stop_task(self, task_name: str) -> str:
        """
        Stop a running task.

        Args:
        - task_name (str): The name of the task to stop.

        Returns:
        - str: Success or failure message.
        """
        success = self.task_manager.stop_process(task_name)
        if success:
            return f"Task '{task_name}' stopped successfully."
        return f"Failed to stop task '{task_name}'."
    
    def list_tasks(self) -> dict:
        """
        List all running tasks.

        Returns:
        - dict: Dictionary with task names and their statuses.
        """
        return self.task_manager.list_tasks()


def run_server():
    parser = argparse.ArgumentParser(description="Run the server")
    parser.add_argument(
        "--dev", action="store_true", help="Run in development mode with debug enabled"
    )
    args = parser.parse_args()
    debug_mode = args.dev
    server = Server()
    server.app.run(host="0.0.0.0", port=TRADE_FLOW_SERVER_PORT, debug=debug_mode)


if __name__ == "__main__":
    run_server()
