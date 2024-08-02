import os
import time
import pytest
from unittest.mock import patch
from trade_flow.venues import VenueManager
from trade_flow.environments import EnvironmentManager, TrainingEnvironment, BacktestEnvironment, SandboxEnvironment, LiveEnvironment
from trade_flow.commons import Logger, EnvironmentMode


@pytest.fixture
def tmp_env_ids_file(tmpdir):
    """Fixture to provide a temporary file for environment IDs."""
    return str(tmpdir.join("training_environment_ids.json"))


@pytest.fixture
def venue_manager():
    return VenueManager()


@pytest.fixture
def env_manager(tmp_env_ids_file, venue_manager):
    """Fixture to initialize EnvironmentManager with a temporary file for environment IDs."""
    with patch('ray.rllib.env.register_env') as mock_register_env:
        env_manager = EnvironmentManager(EnvironmentMode.TRAIN, venue_manager)
        env_manager.env_ids_file = tmp_env_ids_file
        yield env_manager
        # Clean up after each test
        env_manager.dispose()
        if os.path.exists(tmp_env_ids_file):
            os.remove(tmp_env_ids_file)


def test_init_live_mode(venue_manager, tmp_env_ids_file):
    env_manager = EnvironmentManager(EnvironmentMode.LIVE, venue_manager)
    env_manager.env_ids_file = tmp_env_ids_file
    env_manager.init()

    assert env_manager.mode == EnvironmentMode.LIVE
    assert isinstance(env_manager.logger, Logger)
    assert isinstance(env_manager.selected_environment, LiveEnvironment)


def test_init_sandbox_mode(venue_manager, tmp_env_ids_file):
    env_manager = EnvironmentManager(EnvironmentMode.SANDBOX, venue_manager)
    env_manager.env_ids_file = tmp_env_ids_file
    env_manager.init()

    assert env_manager.mode == EnvironmentMode.SANDBOX
    assert isinstance(env_manager.logger, Logger)
    assert isinstance(env_manager.selected_environment, SandboxEnvironment)


def test_init_backtest_mode(venue_manager, tmp_env_ids_file):
    env_manager = EnvironmentManager(EnvironmentMode.BACKTEST, venue_manager)
    env_manager.env_ids_file = tmp_env_ids_file
    env_manager.init()

    assert env_manager.mode == EnvironmentMode.BACKTEST
    assert isinstance(env_manager.logger, Logger)
    assert isinstance(env_manager.selected_environment, BacktestEnvironment)


def test_init_train_mode(venue_manager, tmp_env_ids_file):
    env_manager = EnvironmentManager(EnvironmentMode.TRAIN, venue_manager)
    env_manager.env_ids_file = tmp_env_ids_file
    env_manager.init()

    assert env_manager.mode == EnvironmentMode.TRAIN
    assert isinstance(env_manager.logger, Logger)
    assert isinstance(env_manager.selected_environment, TrainingEnvironment)
    assert env_manager.environments  


def test_init_unknown_mode(venue_manager):
    with pytest.raises(ValueError):
        EnvironmentManager(EnvironmentMode("UNKNOWN"), venue_manager)


def test_init_with_existing_env_ids(venue_manager, tmp_env_ids_file):
    # Create an EnvironmentManager with TRAIN mode and a temporary env IDs file
    env_manager1 = EnvironmentManager(EnvironmentMode.TRAIN, venue_manager)
    env_manager1.env_ids_file = tmp_env_ids_file
    env_manager1.init()  # Create and save an environment ID
    
    time.sleep(2)
    
    # Create a new EnvironmentManager to load the saved environment ID
    env_manager2 = EnvironmentManager(EnvironmentMode.TRAIN, venue_manager, new=False)
    env_manager2.env_ids_file = tmp_env_ids_file
    env_manager2.init()

    assert env_manager2.mode == EnvironmentMode.TRAIN
    print(env_manager2.environments)
    assert env_manager2.environments  
