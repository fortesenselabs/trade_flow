from trade_flow.environments.generic import Informer, TradingEnvironment


class TradeFlowInformer(Informer):

    def __init__(self) -> None:
        super().__init__()

    def info(self, env: "TradingEnvironment") -> dict:
        return {"step": self.clock.step, "net_worth": env.action_scheme.portfolio.net_worth}
