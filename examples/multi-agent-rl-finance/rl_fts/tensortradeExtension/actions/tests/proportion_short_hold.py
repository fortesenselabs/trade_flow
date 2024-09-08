from rl_fts.environments.sinewave.environment5 import create_env
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
        {'price': 150.0, 'action': [-1, [100.0]]}, 
        {'price': 148.2962913144534, 'action': [1, [66.806496]]}, 
        {'price': 143.30127018922195, 'action': [1, [53.88804]]}, 
        {'price': 135.35533905932743, 'action': [1, [72.43087]]}, 
        {'price': 125.00000000000007, 'action': [0, [72.55122]]}, 
        {'price': 112.94095225512612, 'action': [0, [27.27025]]}, 
        {'price': 100.00000000000001, 'action': [0, [15.324399]]}, 
        {'price': 87.059047744874, 'action': [1, [1.0]]}, 
        {'price': 75.00000000000004, 'action': [1, [10.140526]]}, 
        {'price': 64.64466094067268, 'action': [1, [75.25075]]}, 
        {'price': 56.69872981077811, 'action': [0, [1.0]]}, 
        {'price': 51.703708685546616, 'action': [1, [18.112087]]},
        {'price': 50.0, 'action': [0, [57.92346]]}, 
        {'price': 51.70370868554657, 'action': [0, [19.80013]]},
        {'price': 56.69872981077804, 'action': [1, [1.0]]},
        {'price': 64.64466094067258, 'action': [0, [6.0199556]]},
        {'price': 74.99999999999993, 'action': [0, [1.0]]},
        {'price': 87.05904774487387, 'action': [1, [1]]}
    ]

def test_1():
    return [
        {'price': 150.0, 'action': -1, 'proportion': -1}, 
        {'price': 148.2962913144534, 'action': 1, 'proportion': 1.4757745}, 
        {'price': 143.30127018922195, 'action': 1, 'proportion': 1.4757745}, 
        {'price': 135.35533905932743, 'action': 0, 'proportion': 43.059055}, 
        {'price': 125.00000000000007, 'action': 0, 'proportion': 43.059055}, 
        {'price': 112.94095225512612, 'action': 1, 'proportion': 27.988918}, 
        {'price': 100.00000000000001, 'action': 0, 'proportion': 14.296924}, 
        {'price': 87.059047744874, 'action': 1, 'proportion': 95.708885}, 
        {'price': 75.00000000000004, 'action': 0, 'proportion': 16.883928}, 
        {'price': 64.64466094067268, 'action': 0, 'proportion': 16.883928}, 
        {'price': 56.69872981077811, 'action': 1, 'proportion': 36.75924}, 
        {'price': 51.703708685546616, 'action': 1, 'proportion': 36.75924},
        {'price': 50.0, 'action': 0, 'proportion': 48.31173}, 
        {'price': 51.70370868554657, 'action': 0, 'proportion': 48.31173},
        {'price': 56.69872981077804, 'action': 0, 'proportion': 48.31173},
        {'price': 64.64466094067258, 'action': 1, 'proportion': 5.833191},
        {'price': 74.99999999999993, 'action': 0, 'proportion': 91.958084},
        {'price': 87.05904774487387, 'action': 1, 'proportion': 40.9082},
        {'price': 99.99999999999997, 'action': 0, 'proportion': 1.0},
        {'price': 112.940952255126, 'action': 0, 'proportion': 46.729683}
    ]

def main():
    config = {
        "type": "train",
        "period": 10,
        "window_size": 30,
        "min_periods": 30,
        "max_allowed_loss": 1,
        "trading_days": 121
    }

    env: TradingEnv = create_env(config)

    trading_simulations = []
    trading_simulations.append(test_1())
    for simulation in trading_simulations:
        for row in simulation:
            action = row['action']
            proportion = row['proportion']
            actions = [action, [proportion]]
            env.step(actions)
    print("done")

main()