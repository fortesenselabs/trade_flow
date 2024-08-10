# Packages

This directory contains external packages and dependencies used within the TradeFlow project. These packages provide functionalities or integrations that are not built directly into the core codebase.

## Structure

- **adapters:** This subdirectory houses Nautilus Trader adapters. These adapters handle communication protocols and data exchange between TradeFlow and the Nautilus Trader platform.
- **mt5linux:** This subdirectory contain code related to the MT5 trading platform on Linux. It is a custom library for interacting with MT5 on the Linux operating system. It depends on the [metatrader5-terminal](https://github.com/fortesenselabs/trade_flow/pkgs/container/metatrader5-terminal) docker image.

**Important Note:**

The documentation for these packages might be located elsewhere, depending on their origin.

- **External Packages:**
  - If the packages are external libraries downloaded from repositories like PyPI, their documentation can usually be found on the official project website or repository.
  - You can try searching for documentation using the package name and version information.
- **Custom Packages:**
  - For custom packages developed specifically for the TradeFlow project, the documentation might reside within the TradeFlow codebase itself. Check the parent directory (trade_flow) or the project repository for potential documentation files.
