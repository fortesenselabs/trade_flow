import time
from trade_flow.commons import EnvironmentMode
from trade_flow.environments import EnvironmentManager
from trade_flow.venues import VenueManager

# Initialize VenueManager
venue_manager = VenueManager()

# Initialize EnvironmentManager for training mode
env_manager = EnvironmentManager(EnvironmentMode.TRAIN, venue_manager)

# Create and register a new gym environment
env_manager.create_environment()

# Retrieve a specific environment
print(env_manager.environments.keys())
env_keys = list(env_manager.environments.keys())
if len(env_keys) > 0:
    env_id = env_keys[0]
    env = env_manager.get_environment(env_id)

time.sleep(60*60*60)

# Reset all environments
env_manager.reset()

# Dispose of all environments
env_manager.dispose()
