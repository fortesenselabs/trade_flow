import yaml
from trade_flow.commons import EnvironmentMode


class FlowConfig:
    agent: str
    objective: str 
    initial_risk_reward_ratio: str
    environment_mode: EnvironmentMode

# Function to parse the YAML and create a Python class instance
def parse_yaml_to_class(yaml_file: str) -> FlowConfig:
    with open(yaml_file, "r") as file:
        data = yaml.safe_load(file)

   
    config = data

    return config


# Example usage
# config = parse_yaml_to_class("path_to_yaml_file.yaml")
# print(config)
