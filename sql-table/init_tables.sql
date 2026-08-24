USE StockPrices
GO

CREATE TABLE items(
	symbol         VARCHAR(10) PRIMARY KEY,
    exchange       VARCHAR(20),
    mic_code       VARCHAR(20),
    currency       VARCHAR(10),
    asset_type     NVARCHAR(50),
    company_name   NVARCHAR(200),
);

CREATE TABLE raw_prices (
    id             INT IDENTITY(1,1) PRIMARY KEY,
    symbol         VARCHAR(10)     NOT NULL,
    fetched_at     DATETIME2       NOT NULL DEFAULT SYSUTCDATETIME(),
    source_api     VARCHAR(50)     NOT NULL DEFAULT 'twelvedata',
    interval       VARCHAR(10)     NOT NULL,
    raw_json       NVARCHAR(MAX)   NOT NULL,
    CONSTRAINT FK_raw_prices_items FOREIGN KEY (symbol) REFERENCES items(symbol)
);


CREATE TABLE stg_prices (
    symbol         VARCHAR(10)     NOT NULL,
    price_datetime DATETIME2       NOT NULL,
    open_price     DECIMAL(12,6),
    high_price     DECIMAL(12,6),
    low_price      DECIMAL(12,6),
    close_price    DECIMAL(12,6),
    volume         BIGINT,
    ingested_at    DATETIME2       NOT NULL DEFAULT SYSUTCDATETIME(),
    CONSTRAINT PK_stg_prices PRIMARY KEY (symbol, price_datetime),
    CONSTRAINT FK_stg_prices_items FOREIGN KEY (symbol) REFERENCES items(symbol)
);


