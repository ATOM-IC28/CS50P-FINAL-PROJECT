import pytest
from project import Portfolio


def test_add_stocks():
    portfolio = Portfolio()
    portfolio.check_main_portfolio("AAPL", 10, 150.0, "stocks/funds")
    portfolio.check_main_portfolio("GOOGL", 5, 2800.0, "stocks/funds")
    assert len(portfolio.main_portfolio) == 2
    assert portfolio.main_portfolio[0]["symbol"] == "AAPL"
    assert portfolio.main_portfolio[1]["symbol"] == "GOOGL"
    assert portfolio.main_portfolio[0]["quantity"] == 10
    assert portfolio.main_portfolio[1]["quantity"] == 5
    assert portfolio.main_portfolio[0]["price"] == 150.0
    assert portfolio.main_portfolio[1]["price"] == 2800.0
    assert portfolio.main_portfolio[0]["value(usd)"] == 1500.0
    assert portfolio.main_portfolio[1]["value(usd)"] == 14000.0

def test_add_crypto():
    portfolio = Portfolio()
    portfolio.check_main_portfolio("BTC", 10, 210, "crypto")
    portfolio.check_main_portfolio("ETH", 5, 1500, "crypto")
    assert len(portfolio.main_portfolio) == 2
    assert portfolio.main_portfolio[0]["symbol"] == "BTC"
    assert portfolio.main_portfolio[1]["symbol"] == "ETH"
    assert portfolio.main_portfolio[0]["quantity"] == 10
    assert portfolio.main_portfolio[1]["quantity"] == 5
    assert portfolio.main_portfolio[0]["price"] == 210
    assert portfolio.main_portfolio[1]["price"] == 1500
    assert portfolio.main_portfolio[0]["value(usd)"] == 2100
    assert portfolio.main_portfolio[1]["value(usd)"] == 7500

def test_add_currency():
    portfolio = Portfolio()
    portfolio.check_main_portfolio("USD", 100, 1.0, "currency")
    portfolio.check_main_portfolio("EUR", 50, 1.14, "currency")
    assert len(portfolio.main_portfolio) == 2
    assert portfolio.main_portfolio[0]["symbol"] == "USD"
    assert portfolio.main_portfolio[1]["symbol"] == "EUR"
    assert portfolio.main_portfolio[0]["quantity"] == 100
    assert portfolio.main_portfolio[1]["quantity"] == 50
    assert portfolio.main_portfolio[0]["price"] == 1.0
    assert portfolio.main_portfolio[1]["price"] == 1.14
    assert portfolio.main_portfolio[0]["value(usd)"] == 100.0
    assert portfolio.main_portfolio[1]["value(usd)"] == 57.0

def test_update_existing_asset():
    portfolio = Portfolio()
    portfolio.check_main_portfolio("AAPL", 10, 150.0, "stocks/funds")
    portfolio.check_main_portfolio("AAPL", 5, 160.0, "stocks/funds")
    assert len(portfolio.main_portfolio) == 1
    assert portfolio.main_portfolio[0]["quantity"] == 15
    assert portfolio.main_portfolio[0]["price"] == 160.0
    assert portfolio.main_portfolio[0]["value(usd)"] == round(10*150 + 5*160, 3)

def test_total_value():
    portfolio = Portfolio()
    portfolio.check_main_portfolio("BTC", 1, 30000, "crypto")
    portfolio.check_main_portfolio("AAPL", 2, 150, "stocks/funds")
    assert portfolio.total_value() == 30000 + 2*150

def test_total_value_crypto():
    portfolio = Portfolio()
    portfolio.check_main_portfolio("BTC", 1, 30000, "crypto")
    assert portfolio.total_value_crypto() == 30000
    assert portfolio.total_value_stocks() == 0

def test_total_value_stocks():
    portfolio = Portfolio()
    portfolio.check_main_portfolio("AAPL", 10, 150.0, "stocks/funds")
    assert portfolio.total_value_stocks() == 1500.0
    assert portfolio.total_value_crypto() == 0

def test_remove_existing_asset():
    portfolio = Portfolio()
    portfolio.check_main_portfolio("BTC", 1, 30000, "crypto")
    portfolio.remove_from_portfolio("BTC")
    assert len(portfolio.main_portfolio) == 0

def test_remove_non_existing_asset():
    portfolio = Portfolio()
    portfolio.check_main_portfolio("BTC", 1, 30000, "crypto")
    portfolio.remove_from_portfolio("ETH")
    assert len(portfolio.main_portfolio) == 1
    assert portfolio.main_portfolio[0]["symbol"] == "BTC"

def test_update_portfolio_existing_asset():
    portfolio = Portfolio()
    portfolio.check_main_portfolio("BTC", 1, 30000, "crypto")

    for row in portfolio.main_portfolio:
        if row["symbol"] == "BTC":
            row["price"] = 30000
    portfolio.get_new_quantity = lambda: 2
    portfolio.update_portfolio("BTC")
    assert portfolio.main_portfolio[0]["quantity"] == 2
    assert portfolio.main_portfolio[0]["value(usd)"] == 60000

def test_update_portfolio_non_existing_asset():
    portfolio = Portfolio()
    portfolio.check_main_portfolio("BTC", 1, 30000, "crypto")
    portfolio.get_new_quantity = lambda: 2
    portfolio.update_portfolio("ETH")
    assert portfolio.main_portfolio[0]["quantity"] == 1

def test_total_values_with_empty_portfolio():
    portfolio = Portfolio()
    assert portfolio.total_value() == 0
    assert portfolio.total_value_crypto() == 0
    assert portfolio.total_value_stocks() == 0


