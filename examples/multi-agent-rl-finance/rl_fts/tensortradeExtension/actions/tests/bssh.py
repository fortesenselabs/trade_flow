from rl_fts.environments.sinewaveBSSH import create_env
from tensortrade.env.generic import TradingEnv

# TESTS
"""
    Test case - 0`
    description: test case which was causing an exception
    reason: the precision of the instrument was too low, 
    issue: this caused the enter order to be cancelled, but the short hold action scheme thought that the action was
    successful, which allowed the simulator to attempt to exit a position that was never entered
    resolution: pushed up my instrument precision to from 2 decimal points to 8
    NOTE: pay attention to the terminal output on a crash.
"""

def test_0():
    return [
        {'price': 100.00000000000011, 'action': -1},
        {'price': 75.00000000000006, 'action': 2},
        {'price': 56.69872981077811, 'action': 0},
        {'price': 50.69872981077811, 'action': 2}
    ]

def test_1():
    return [
        {'price': 100.00000000000011, 'action': -1}, 
        {'price': 75.00000000000006, 'action': 0}, 
        {'price': 56.69872981077811, 'action': 0}, 
        {'price': 50.0, 'action': 1}, 
        {'price': 56.69872981077799, 'action': 3}, 
        {'price': 74.99999999999984, 'action': 0},
        {'price': 99.99999999999999, 'action': 2},
    ]

def test_2():
    return [
        {'price': 100.00000000000011, 'action': -1}, 
        {'price': 75.00000000000006, 'action': 1}, 
    ]

def main():
    config = {
        "type": "train",
        "period": 20,
        "window_size": 30,
        "min_periods": 30,
        "max_allowed_loss": 1,
        "trading_days": 121
    }

    env: TradingEnv = create_env(config)

    trading_simulations = []
    trading_simulations.append(test_2())
    for simulation in trading_simulations:
        for row in simulation:
            action = row['action']
            env.step(action=action)
    print("done")

main()
