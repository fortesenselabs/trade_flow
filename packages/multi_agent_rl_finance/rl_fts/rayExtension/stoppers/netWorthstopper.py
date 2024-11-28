import time
from ray import tune
from ray.tune import Stopper

class NetWorthstopper(Stopper):
    def __init__(self, 
        net_worth_mean_threshold: int,
        patience: int = 0
    ):
        self._start = time.time()
        self._net_worth_mean_threshold = net_worth_mean_threshold
        self._patience = patience
        self._iterations = 0
        self.stop = False
        return

    def has_reached_objective(self, result):
        if "net_worth_max" not in result["custom_metrics"]:
            self.stop = False
        elif result["custom_metrics"]["net_worth_mean"] >= self._net_worth_mean_threshold:
            self.stop = True
        return self.stop

    def __call__(self, trial_id, result):
        if self.has_reached_objective(result):
            self._iterations +=1
        else:
            self._iterations = 0
        return self.stop_all()

    def stop_all(self):
        return self.stop and self._iterations >= self._patience