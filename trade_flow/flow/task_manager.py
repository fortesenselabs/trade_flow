import docker
from docker.models.containers import Container

class TaskManager:
    def __init__(self):
        self.client = docker.from_env()  # Initialize Docker client from environment
        self.containers = {}  # Dictionary to keep track of container instances

    def start_container(self, image: str, name: str, **kwargs) -> Container:
        """Start a new Docker container."""
        if name in self.containers:
            raise ValueError(f"Container with name '{name}' already exists.")
        
        container = self.client.containers.run(image, name=name, detach=True, **kwargs)
        self.containers[name] = container
        return container

    def stop_container(self, name: str) -> None:
        """Stop a running Docker container."""
        if name not in self.containers:
            raise ValueError(f"Container with name '{name}' does not exist.")
        
        container = self.containers[name]
        container.stop()
        container.remove()
        del self.containers[name]

    def restart_container(self, name: str) -> None:
        """Restart a Docker container."""
        if name not in self.containers:
            raise ValueError(f"Container with name '{name}' does not exist.")
        
        container = self.containers[name]
        container.restart()

    def list_containers(self) -> dict:
        """List all managed Docker containers."""
        return {name: container.status for name, container in self.containers.items()}

    def get_container_logs(self, name: str) -> str:
        """Retrieve logs from a Docker container."""
        if name not in self.containers:
            raise ValueError(f"Container with name '{name}' does not exist.")
        
        container = self.containers[name]
        return container.logs().decode('utf-8')

# Example usage:
if __name__ == "__main__":
    task_manager = TaskManager()

    # Start a container
    container = task_manager.start_container("node:14", "node-container", command="node -e 'console.log(\"Hello World\")'")

    # List all containers
    print("Containers:", task_manager.list_containers())

    # Get logs from the container
    print("Logs:", task_manager.get_container_logs("node-container"))

    # Restart the container
    task_manager.restart_container("node-container")

    # Stop and remove the container
    task_manager.stop_container("node-container")
