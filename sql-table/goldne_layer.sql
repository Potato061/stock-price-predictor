--Create golden layer

CREATE TABLE curated_features (
    symbol         VARCHAR(10)     NOT NULL,
    price_datetime DATETIME2       NOT NULL,
    open_price     DECIMAL(12,6),
    high_price     DECIMAL(12,6),
    low_price      DECIMAL(12,6),
    close_price    DECIMAL(12,6),
    volume         BIGINT,
    prev_close     DECIMAL(12,6),
    daily_return   DECIMAL(12,8),
    ma_5           DECIMAL(12,6),
    ma_20          DECIMAL(12,6),
    volatility_10  DECIMAL(12,8),
    built_at       DATETIME2       NOT NULL DEFAULT SYSUTCDATETIME(),
    CONSTRAINT PK_curated_features PRIMARY KEY (symbol, price_datetime),
    CONSTRAINT FK_curated_features_items FOREIGN KEY (symbol) REFERENCES items(symbol)
);