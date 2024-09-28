import pandas as pd
from trade_flow.indicators.support_and_resistance import support_and_resistance_using_roling_window
from trade_flow.feed import Coinbase_BTCUSD_d, data # Import the correct feed

def main():
    # Step 1: Convert the Coinbase data to a DataFrame
    df = pd.read_csv('../trade_flow/feed/data/Coinbase_BTCUSD_d.csv')  # Assuming Coinbase_BTCUSD_d is structured data

    # Step 2: Detect support and resistance using the rolling window
    support_levels, resistance_levels = support_and_resistance_using_roling_window.detect_local_min_max(df)

    # Step 3: Output the results
    print("Support Levels:", support_levels)
    print("Resistance Levels:", resistance_levels)

# Run the main function
if __name__ == "__main__":
    main()
