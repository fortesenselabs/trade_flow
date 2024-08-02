import base64
import sys
import click
from trade_flow.cli.rpc import rpc_call
from rich import print
from rich.console import Console
from rich.table import Table


@click.group(name="agents")
def agents():
    """agents commands"""


@agents.command()
def available():
    """
    List available agents in Trade Flow
    """
    console = Console()
    result = rpc_call("agents_available", None)
    if not isinstance(result, list):  # Make mypy happy
        print(f"Error. Expected list but got {type(result)}: {result}")
        sys.exit(1)

    # Create the table
    table = Table(show_header=True, header_style="bold")
    table.add_column("Name")
    table.add_column("Description")

    for scenario in result:
        table.add_row(scenario[0], scenario[1])
    console.print(table)


@agents.command(context_settings={"ignore_unknown_options": True})
@click.argument("scenario", type=str)
@click.argument("additional_args", nargs=-1, type=click.UNPROCESSED)
@click.option("--network", default="warnet", show_default=True)
def run(scenario, network, additional_args):
    """
    Run <scenario> from the Trade Flow on [network] with optional arguments
    """
    params = {
        "scenario": scenario,
        "additional_args": additional_args,
        "network": network,
    }
    print(rpc_call("agents_run", params))


@agents.command(context_settings={"ignore_unknown_options": True})
@click.argument("scenario_path", type=str)
@click.argument("additional_args", nargs=-1, type=click.UNPROCESSED)
@click.option("--network", default="warnet", show_default=True)
def run_file(scenario_path, network, additional_args):
    """
    Run <scenario_path> from the Trade Flow on [network] with optional arguments
    """
    scenario_base64 = ""
    with open(scenario_path, "rb") as f:
        scenario_base64 = base64.b64encode(f.read()).decode("utf-8")

    params = {
        "scenario_base64": scenario_base64,
        "additional_args": additional_args,
        "network": network,
    }
    print(rpc_call("agents_run_file", params))


@agents.command()
def active():
    """
    List running agents "name": "pid" pairs
    """
    console = Console()
    result = rpc_call("agents_list_running", {})
    if not result:
        print("No agents running")
        return
    assert isinstance(result, list)  # Make mypy happy

    table = Table(show_header=True, header_style="bold")
    for key in result[0].keys():  # noqa: SIM118
        table.add_column(key.capitalize())

    for scenario in result:
        table.add_row(*[str(scenario[key]) for key in scenario])

    console.print(table)


@agents.command()
@click.argument("pid", type=int)
def stop(pid: int):
    """
    Stop scenario with PID <pid> from running
    """
    params = {"pid": pid}
    print(rpc_call("agents_stop", params))

# build 
# list 
# deploy
# cli agent build <file>
# cli agent list: List all trained and un-trained agents