from trade_flow.indicators.support_and_resistance import (
    OptimizedSupportResistanceIndicator,
    SupportResistanceIndicator,
)
from trade_flow.feed import Coinbase_BTCUSD_d

df = Coinbase_BTCUSD_d.copy()
df.index = df.index.set_names("timestamp")

print("Dataset:", df, "\n")

# Create an instance of SupportResistanceIndicator or OptimizedSupportResistanceIndicator
indicator = SupportResistanceIndicator(df)

# Calculate Pivot Points
pivot_points_df = indicator.calculate_pivot_points()
print("Pivot Points and Support/Resistance Levels:\n", pivot_points_df)

# Detect Local Min/Max
support, resistance = indicator.detect_local_min_max(window_size=2)
print("\nDetected Support Levels:", support)
print("Detected Resistance Levels:", resistance)

# Get all indicators
support_resistance_indicator = indicator.get_all_indicators(window_size=20)
print("\nSupport-Resistance Levels:", support_resistance_indicator)
