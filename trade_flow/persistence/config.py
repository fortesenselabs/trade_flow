import os

trade_plan_folder: str = (
    os.getenv("TRADE_PLAN_DIR", ".") if len(os.getenv("TRADE_PLAN_DIR", ".")) > 0 else "."
)
