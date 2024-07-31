import click
from rich import print as richprint
from cli.rpc import rpc_call
from cli.nodes import nodes
from cli.exchanges import exchanges
from cli.environments import environments
from cli.agents import agents
from cli.generate import generate


@click.group()
def cli():
    pass

cli.add_command(exchanges)
cli.add_command(environments)
cli.add_command(agents)
cli.add_command(nodes)
cli.add_command(generate)

@cli.command(name="help")
@click.argument("commands", required=False, nargs=-1)
@click.pass_context
def help_command(ctx, commands):
    """
    Display help information for the given [command] (and sub-command).
    If no command is given, display help for the main CLI.
    """
    if not commands:
        # Display help for the main CLI
        richprint(ctx.parent.get_help())
        return

    # Recurse down the subcommands, fetching the command object for each
    cmd_obj = cli
    for command in commands:
        cmd_obj = cmd_obj.get_command(ctx, command)
        if cmd_obj is None:
            richprint(f'Unknown command "{command}" in {commands}')
            return
        ctx = click.Context(cmd_obj, info_name=command, parent=ctx)

    if cmd_obj is None:
        richprint(f"Unknown command: {commands}")
        return

    # Get the help info
    help_info = cmd_obj.get_help(ctx).strip()
    # Get rid of the duplication
    help_info = help_info.replace(
        "Usage: flowcli help [COMMANDS]...", "Usage: flowcli", 1
    )
    richprint(help_info)


cli.add_command(help_command)


@cli.command()
def stop():
    """
    Stop trade flow.
    """
    try:
        rpc_call("server_stop", None)
    except ConnectionError:
        richprint("Stopped trade flow")
    except Exception as e:
        print(e)


if __name__ == "__main__":
    cli()
