import threading
from typing import Callable, Dict, Optional, Any
from trade_flow.commons import Logger  

class TaskManager:
    def __init__(self):
        self.logger = Logger(name=__class__.__name__)
        self.processes: Dict[str, threading.Thread] = {}  # Dictionary to keep track of processes
    
    def start_process_in_thread(self, task_name: str, target_function: Callable, *args: Any, **kwargs: Any) -> Optional[threading.Thread]:
        """
        Start a process in a separate thread.

        Args:
        - task_name (str): Unique name for the task.
        - target_function (Callable): The function to run in the thread.
        - *args: Arguments to pass to the target_function.
        - **kwargs: Keyword arguments to pass to the target_function.

        Returns:
        - Optional[threading.Thread]: The created thread, or None if the task already exists.
        """
        if task_name in self.processes:
            self.logger.error(f"Task '{task_name}' is already running.")
            return None
        
        thread = threading.Thread(target=target_function, args=args, kwargs=kwargs)
        thread.start()
        self.processes[task_name] = thread
        self.logger.info(f"Started task '{task_name}' in a separate thread.")
        return thread

    def get_thread(self, task_name: str) -> Optional[threading.Thread]:
        """
        Retrieve the thread associated with a given task name.

        Args:
        - task_name (str): The name of the task.

        Returns:
        - Optional[threading.Thread]: The thread associated with the task, or None if it doesn't exist.
        """
        return self.processes.get(task_name)
    
    def stop_process(self, task_name: str) -> bool:
        """
        Stop a running process by its task name.

        Args:
        - task_name (str): The name of the task to stop.

        Returns:
        - bool: True if the task was successfully stopped, False otherwise.
        """
        thread = self.processes.pop(task_name, None)
        if thread and thread.is_alive():
            # Note: Python's threading doesn't provide a direct way to stop threads
            # In practice, you'd use a flag or other mechanism to signal the thread to stop
            self.logger.warning(f"Stopping thread '{task_name}' is not directly supported. Consider implementing a stop mechanism.")
            return False
        return True

    def list_tasks(self) -> Dict[str, str]:
        """
        List all running tasks.

        Returns:
        - Dict[str, str]: Dictionary with task names and their statuses.
        """
        return {name: ("Running" if thread.is_alive() else "Stopped") for name, thread in self.processes.items()}
