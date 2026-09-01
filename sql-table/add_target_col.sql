

SELECT COUNT(*) FROM raw_prices;        -- should still be ~100 (one blob per symbol)
SELECT COUNT(*) FROM stg_prices;        -- should now be much bigger, ~100 × up to 5000
SELECT COUNT(*) FROM curated_features; 
-- slightly smaller than stg_prices (dropna warm-up), but still huge

SELECT TOP 10 symbol, price_datetime, daily_return, target_next_return
FROM curated_features
ORDER BY symbol, price_datetime;

ALTER TABLE curated_features ADD target_next_return DECIMAL(12,8);