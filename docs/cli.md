# TradeFlow CLI Documentation

This documentation serves as a guide for interacting with TradeFlow through the command-line interface (CLI). The CLI provides a convenient way to manage various aspects of TradeFlow, including:

- **Venues:** Configure connections to data and execution platforms (exchanges, brokers)
- **Environments:** Manage trading environments for different market simulations
- **Agents:** Define and deploy trading agents with various strategies
- **Generate:** Generate trading signals or reports based on current market conditions
- **Stop:** Stop the running TradeFlow server

## Installation

Assuming you have TradeFlow installed, the CLI should be readily available. You can verify its location using your system's command launcher (e.g., terminal on macOS/Linux, Command Prompt on Windows).

## Basic Usage

To execute a TradeFlow CLI command, simply open your terminal or command prompt and type:

```bash
flowcli <command> [options]
```

Replace `<command>` with the specific command you want to run (e.g., `venues`, `environments`, etc.). Options are additional arguments that can further customize the command's behavior.

For detailed information about individual commands and their options, refer to the dedicated sections below.

## Available Commands

- **help:** Provides help information for the main CLI or specific subcommands.

```bash
flowcli help
flowcli environments --help
```

- **venues:** Manage venue (data & execution platform) configurations.

  - **available:** List available venues in TradeFlow.
  - **active:** List running venues.

- **environments:** Manage trading environments for simulation purposes.

  - **available:** List available environments in TradeFlow.
  - **active:** List running environments.

- **agents:** Define and deploy trading agents with different strategies.

  - **available:** List available agents in TradeFlow.
  - **active:** List running agents.
  - **stop:** Stop a running agent.
  - **build:** Build a new trading agent from a source file.
  - **deploy:** Deploy a built agent to a specific environment.
  - **all:** List all available trading agents (trained and untrained).

- **generate:** Generate trading signals or reports based on market data (venue, environment and agent templates).
- **stop:** Stop the running TradeFlow server.

## Stopping TradeFlow

Use the `stop` command to gracefully shut down the TradeFlow server:

```bash
flowcli stop
```

This is a recommended way to stop TradeFlow as it allows the server to properly clean up resources before termination.

## Additional Notes

- This documentation utilizes `rich` library for enhanced output formatting. The actual output may vary based on your system configuration.
- For detailed breakdowns of each command's functionalities and options, refer to the specific command sections (not provided in this documentation snippet).

**This documentation provides a high-level overview of the TradeFlow CLI. For comprehensive information about specific commands and their options, consult the individual command documentation within the CLI itself using `flowcli help <command>`.**
