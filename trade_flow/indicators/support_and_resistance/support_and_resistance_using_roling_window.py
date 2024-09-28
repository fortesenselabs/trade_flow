
import pandas as pd


# Detect Local Minima (Support) and Maxima (Resistance)
def detect_local_min_max(df, window_size=5):
    
    if not isinstance(df, pd.DataFrame):
        raise ValueError("Data is a DataFrame")
    else:
        support_levels = []
        resistance_levels = []

        # Rolling window to check local minima and maxima
        for i in range(window_size, len(df) - window_size):
        # Local low (support)
            if df['low'][i] == df['low'][i - window_size:i + window_size].min():
                support_levels.append((df['date'][i], df['low'][i]))
            # Local high (resistance)
            if df['high'][i] == df['high'][i - window_size:i + window_size].max():
                resistance_levels.append((df['date'][i], df['high'][i]))
        return support_levels,  resistance_levels


