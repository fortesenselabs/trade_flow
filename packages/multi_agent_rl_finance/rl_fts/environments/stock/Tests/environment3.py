from rl_fts.environments.stock.NFLX.environment3 import generate_env
from rl_fts.environments.sinewave.data import SineWaveDataGenerator

def test_price_movement():
    data_generator = SineWaveDataGenerator(x_sample=100)
    training_data = data_generator.train()
    # create a pandas dataframe with price data in the ['Close'] column
    training_data.columns = ['Close']
    for time_step in range(50):
        print(training_data['Close'].values[time_step])

def test_proportional_short_hold_environment():
    # create the dummy data (sinewave)
    data_generator = SineWaveDataGenerator(x_sample=100)
    training_data = data_generator.train()
    training_data.columns = ['Close']
    print('printing training data')
    print(training_data['Close'].values)
    print()

    # create the trading environment
    config = {
        "type": "train",
        "window_size": 30,
        "min_periods": 30,
        "max_allowed_loss": 1,
        "horizon": 30,
        "id": "NFLX_SH_NWC"
    }
    environment = generate_env(training_data, config)
    print('evironment has a window size of 30')
    print()

    print(f'curent price: {environment.action_scheme.exchange_pair.price}')
    # reward information
    print(f'current cash balance: {environment.action_scheme.cash.balance}')
    print(f'current short balance: {environment.action_scheme.borrow_asset.convert(environment.action_scheme.exchange_pair)}')
    print(f'current deposit balance: {environment.action_scheme.deposit_margin.balance}')
    print(f'current net worth: {environment.reward_scheme.previous_net_worth}')
    print()

    # run the environment
    for _ in range(len(training_data) - 30):
        # price before action
        # short and hold
        print(f'action: {[0,10]}')
        environment.step(action=[0,10])
        print(f'curent price: {environment.action_scheme.exchange_pair.price}')
        # reward information
        print(f'current cash balance: {environment.action_scheme.cash.balance}')
        print(f'current short balance: {environment.action_scheme.borrow_asset.convert(environment.action_scheme.exchange_pair)}')
        print(f'current deposit balance: {environment.action_scheme.deposit_margin.balance}')
        print(f'current net worth: {environment.reward_scheme.previous_net_worth}')

        print(f'reward -> proportional networth change: {environment.reward_scheme.reward_history[-1]}')
        print()

def main():
    test_proportional_short_hold_environment()
    # test_price_movement()

main()