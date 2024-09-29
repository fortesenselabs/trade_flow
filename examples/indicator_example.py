import pandas as pd
from trade_flow.indicators.support_and_resistance import support_and_resistance_using_roling_window, support_and_resistance_using_pivot_point
from trade_flow.feed import Coinbase_BTCUSD_d, data # Import the correct feed

def main():
    # Step 1: Convert the Coinbase data to a DataFrame
    df = pd.read_csv('../trade_flow/feed/data/Coinbase_BTCUSD_d.csv')  

  
    #support_levels, resistance_levels = support_and_resistance_using_roling_window.detect_local_min_max(df)
    # print("Support Levels:", support_levels)
    # print("Resistance Levels:", resistance_levels)
    
    support_resistance =  support_and_resistance_using_pivot_point.calculate_pivot_points(df)
    print(support_resistance)
    
    
    

    

# Run the main function
if __name__ == "__main__":
    main()
