USE master
GO


IF  EXISTS (
	SELECT name 
		FROM sys.databases 
		WHERE name = 'StockPrices'
)
DROP DATABASE StockPrices
GO

CREATE DATABASE StockPrices
GO