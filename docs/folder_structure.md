# Folder Structure

This breakdown provides a general overview of the project structure.

- **docs:** Documentation related to the project.
- **infrastructure:** Infrastructure-related code or configurations.
- **notebooks:** Jupyter notebooks or similar interactive development environments.
- **packages:** External packages or dependencies used in the project.
  - **adapters:** Adapters for integrating with nautilus trader systems.
  - **mt5linux:** Likely related to a specific platform or integration.
- **scripts:** Scripts for various tasks or automation.
- **tests:** Test cases and related files.
- **trade_flow:** Core project code.
  - **agents:** Agent-related configurations or code.
  - **cli:** Command-line interface for interacting with server/daemon.
  - **commons:** Common utilities or shared code.
  - **environments:** Environment-related configurations or code.
  - **flow:** Core management and server logic or workflow.
  - **interfaces:** Interfaces for different flow servers/daemons.
  - **repositories:** Data storage and retrieval mechanisms.
  - **venues:** Code for interacting with different trading venues.
- **.gitignore:** File specifying which files or directories to ignore in Git version control.
- **pyproject.toml:** Project configuration for tools like pipenv or poetry.
- **requirements.txt:** List of project dependencies.
- **Tiltfile:** Configuration file for the Tilt deployment tool.
- **README.md:** General project information and instructions.
