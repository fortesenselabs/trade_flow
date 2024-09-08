from trade_flow.environments.generic import Venue
from trade_flow.environments.gym_train.train import TrainingEnvironment


class ForexTrainingEnvironment(TrainingEnvironment):
    def __init__(self, venue: Venue, env_id: str = "Trading-v0") -> None:
        super().__init__(venue, env_id)

    pass
