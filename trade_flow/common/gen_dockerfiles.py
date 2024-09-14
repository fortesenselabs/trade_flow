
import os
import docker

"""Instantiate a client to talk to the docker daemon"""
client = docker.from_env()

metatrader_base_image = "ghcr.io/fortesenselabs/metatrader5-terminal:latest"
nautilus_base_image = "ghcr.io/nautechsystems/nautilus_trader:latest"
workdir = "/app/common"
ports = [8080]
cmd = ["/usr/bin/sh"]

def select_image():
    selected_base_image = input("Press M to build metatrader5 image/ N to build nautilus image ")
    selected_base_image = selected_base_image.lower() 
    if selected_base_image == "m":
        dockerfile_content = generate_dockerfile(metatrader_base_image, workdir, ports, cmd)
        with open("Dockerfile", "w") as f:
            f.write(dockerfile_content)
        # client.images.build(path= "./")
    elif selected_base_image == "n":
        dockerfile_content = generate_dockerfile(nautilus_base_image, workdir, ports, cmd)
        with open("Dockerfile", "w") as f:
            f.write(dockerfile_content)
        # client.images.build(path= "./")
    else:
        select_image() 
    

def generate_dockerfile(base_image, workdir, ports=[], cmd=[]):
    """
    Generates a Dockerfile based on the provided parameters.

    Args:
        base_image (str): The base image to use.
        workdir (str): The working directory within the container.
        commands (list[str]): A list of commands to execute in the container.
        ports (list[int]): A list of ports to expose.

    Returns:
        str: The generated Dockerfile content.
    """

    dockerfile_content = f"""
    FROM {base_image}
    
    CMD {", ".join(str(c) for c in cmd)}

    WORKDIR {workdir}

    COPY . .

    EXPOSE {", ".join(str(port) for port in ports)}


    """

    return dockerfile_content

select_image()
