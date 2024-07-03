# Docs

## Generating Binary Labels for Training Data using Future Information

This document describes a method for generating binary labels for training data in a financial context. These labels leverage future price movements compared to predefined thresholds. This approach can be valuable for tasks like price prediction using machine learning models.

### Key Concepts:

- **Thresholds:** Thresholds are reference values used to compare data points. The context determines whether the comparison involves being greater than or less than the threshold.
- **High/Low Columns:** Labels are generated based on relative deviations from the "close" price (the closing price of a security on a given day). "High" comparisons represent positive deviations, while "low" comparisons represent negative deviations.
- **Horizon:** The horizon defines the timeframe in the future used for label generation. For instance, a horizon of 60 might consider the next 60 data points (e.g., prices).
- **Label Conditions:** Labels are generated based on specific conditions within the defined horizon:
  - **All Values Meet:** All data points within the horizon must satisfy the condition (e.g., all prices exceeding a threshold).
  - **At Least One Value Meets:** At least one data point within the horizon must satisfy the condition (e.g., at least one price exceeding a threshold).

### Label Groups and Encoding:

The conditions for generating labels are grouped into four categories based on the comparison direction (high/low) and the threshold size (large/small):

1. **High >= large_threshold (e.g., 0.5, 1.0, 1.5):** This group checks if at least one value in the future window is greater than or equal to a larger threshold. The label encoding (e.g., "high_0.5") reflects this, indicating "high" (at least one value is larger) relative to a "large" threshold (0.5).
2. **High <= small_threshold (e.g., 0.1, 0.2, 0.3):** This group checks if all values in the future window are less than or equal to a smaller threshold. The label encoding (e.g., "high_0.2") signifies "high" (all values are less) compared to a "small" threshold (0.2).
3. **Low >= -small_threshold (e.g., 0.1, 0.2, 0.3):** This group checks if all values in the future window are greater than or equal to a smaller negative threshold. The label encoding (e.g., "low_0.2") indicates "low" (all values are greater) relative to a "small" negative threshold (-0.2).
4. **Low <= -large_threshold (e.g., 0.5, 1.0, 1.5):** This group checks if at least one value in the future window is less than or equal to a larger negative threshold. The label encoding (e.g., "low_1.0") signifies "low" (at least one value is less) compared to a "large" negative threshold (-1.0).

By using these labels during training, machine learning models can potentially learn to identify patterns in past data that predict future price movements relative to the defined thresholds and horizons.

**PS:**
For label_sets->config->thresholds:
you can use smaller thresholds e.g [0.01]
