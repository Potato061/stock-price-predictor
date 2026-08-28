from feature_engineering import *
print(features_df.shape)
print(features_df.head(10))
print(features_df.isna().sum())  # should all be 0