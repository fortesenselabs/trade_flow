import sys
import click
from cli.rpc import rpc_call
from rich import print
from rich.console import Console
from rich.table import Table


@click.group(name="environments")
def environments():
    """Environments commands"""


@environments.command()
def available():
    """
    List available environments in Trade Flow
    """
    console = Console()
    result = rpc_call("environments_available", None)
    if not isinstance(result, list): 
        print(f"Error. Expected list but got {type(result)}: {result}")
        sys.exit(1)

    # Create the table
    table = Table(show_header=True, header_style="bold")
    table.add_column("Name")
    # add environment type 
    table.add_column("Description")

    for scenario in result:
        table.add_row(scenario[0], scenario[1])
    console.print(table)


@environments.command()
def active():
    """
    List running environments "name": "pid" pairs
    """
    console = Console()
    result = rpc_call("nodes_list_running", {})
    if not result:
        print("No nodes running")
        return
    assert isinstance(result, list)  # Make mypy happy

    table = Table(show_header=True, header_style="bold")
    for key in result[0].keys():  # noqa: SIM118
        table.add_column(key.capitalize())

    for scenario in result:
        table.add_row(*[str(scenario[key]) for key in scenario])

    console.print(table)


@environments.command()
@click.argument("pid", type=int)
def stop(pid: int):
    """
    Stop environment with PID <pid> from running
    """
    params = {"pid": pid}
    print(rpc_call("nodes_stop", params))