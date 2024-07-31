import sys

import click
from cli.rpc import rpc_call
from rich import print
from rich.console import Console
from rich.table import Table


@click.group(name="nodes")
def nodes():
    """Nodes commands"""


@nodes.command()
def available():
    """
    List available nodes in Trade Flow
    """
    console = Console()
    result = rpc_call("nodes_available", None)
    if not isinstance(result, list):  # Make mypy happy
        print(f"Error. Expected list but got {type(result)}: {result}")
        sys.exit(1)

    # Create the table
    table = Table(show_header=True, header_style="bold")
    table.add_column("Name")
    table.add_column("Type")
    table.add_column("Description")

    for scenario in result:
        table.add_row(scenario[0], scenario[1])
    console.print(table)


@nodes.command()
def active():
    """
    List running nodes "name": "pid" pairs
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


@nodes.command()
@click.argument("pid", type=int)
def stop(pid: int):
    """
    Stop node with PID <pid> from running
    """
    params = {"pid": pid}
    print(rpc_call("nodes_stop", params))