import sys

import click
from cli.rpc import rpc_call
from rich import print
from rich.console import Console
from rich.table import Table


@click.group(name="exchanges")
def exchanges():
    """Exchanges commands"""


@exchanges.command()
def available():
    """
    List available exchanges/brokers in Trade Flow
    """
    console = Console()
    result = rpc_call("exchanges_available", None)
    if not isinstance(result, list): 
        print(f"Error. Expected list but got {type(result)}: {result}")
        sys.exit(1)

    # Create the table
    table = Table(show_header=True, header_style="bold")
    table.add_column("Name")
    table.add_column("Description")

    for scenario in result:
        table.add_row(scenario[0], scenario[1])
    console.print(table)