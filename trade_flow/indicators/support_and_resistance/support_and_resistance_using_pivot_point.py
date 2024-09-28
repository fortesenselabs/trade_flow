import pandas as pd

def calculate_pivot_points(df):
    # Check if data is a DataFrame
    if not isinstance(df, pd.DataFrame):
        raise ValueError("Data is a DataFrame")
    else: 
    
        pivot_points = []
        support_resistance = []

        for i, row in df.iterrows():
            high = row['high']
            low = row['low']
            close = row['close']
        
            # Calculate Pivot Point (P)
            pivot = (high + low + close) / 3
        
            # Calculate Resistance 1 (R1), Support 1 (S1)
            resistance_1 = (2 * pivot) - low
            support_1 = (2 * pivot) - high
        
            # Calculate Resistance 2 (R2), Support 2 (S2)
            resistance_2 = pivot + (high - low)
            support_2 = pivot - (high - low)
        
            # Append to lists
            pivot_points.append(pivot)
            support_resistance.append({
                'Pivot': pivot,
                'Resistance_1': resistance_1,
                'Support_1': support_1,
                'Resistance_2': resistance_2,
                'Support_2': support_2
            })
        return pd.DataFrame(support_resistance)
