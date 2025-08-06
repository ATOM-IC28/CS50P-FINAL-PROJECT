from dotenv import load_dotenv
import os
import csv
from requests import Session
from requests.exceptions import ConnectionError, Timeout, TooManyRedirects
import tkinter as tk
from tkinter import filedialog as fd
from tkinter import TclError
from rich.console import Console
from rich.table import Table
from rich import box


class Portfolio:

    load_dotenv() #loading the api_keys

    def __init__(self):
        self.main_portfolio = [] #list of dictionaries to store all the informations
        self.__api_key_cmc = os.getenv("api_key_cmc")
        self.__api_key_alpha = os.getenv("api_key_alpha")
        self.__api_key_exchange_rate = os.getenv("api_key_exchange_rate")
        self.crypto_api = Crypto(self.__api_key_cmc)
        self.stocks_api = Stocks(self.__api_key_alpha)
        self.currency_api = Currency(self.__api_key_exchange_rate)
        self.console = Console()
        self.tk_root = tk.Tk()
        self.tk_root.withdraw() #Hiding the blank window tkinter makes


    def load_csv(self): #Force the user to choose a csv file

        initial_dir = os.path.expanduser("~") #Gets the home directory of the user
        Title = "Choose a file:"
        filetypes =[("csv Files","*.csv")]
        self.tk_root.deiconify() #Show the tkinter window so that filedialog can run
        self.tk_root.attributes('-topmost', True)  # Make the window pop up in front of the IDE
        try:
            file_name = fd.askopenfilename(initialdir=initial_dir, parent=self.tk_root, title=Title, filetypes=filetypes)

        except TclError:
                self.console.print("This IDE does not support this function.", style="bold")
                return

        self.tk_root.attributes('-topmost', False)
        self.tk_root.withdraw() #Hide the tkinter window again

        if file_name == "": #The empty string happens when the user cancels the selection of a file
            self.console.print("No file was selected.", style="bold red3")

        else:
             with open(file_name, "r", newline="") as f:
                #We dont use fieldnames here because we want to use the first line of the csv as the fieldnames
                reader = csv.DictReader(f)
                imported_portfolio = list(reader)

                return imported_portfolio


    def process_csv(self):
        imported_portfolio = self.load_csv()
        n = 0 #it will count the number of times the stocks API fails. (Only this one fails, because it has limited requests per hour)

        if not imported_portfolio:
            return

        for inv in imported_portfolio:
            symbol = inv["symbol"]
            quantity = float(inv["quantity"]) #because quantity comes as a string
            type = inv["type"]
            price = float(inv["price"])
            p_price = float(inv["p_price"])


            if type == "stocks/funds":
                if n == 0:
                    alpha = self.stocks_api
                    try:
                        asset, price = alpha.get_asset_price(symbol)

                    except TypeError: # I noticed that when the alpha vantage API isn't working it returns None for the dictionary with the values
                        self.console.print("The stocks/funds API isn't working.", style="bold red3")
                        self.console.print("Try Again later", style="bold red3")
                        self.console.print("The stocks will continue on your portfolio but with their old prices/values", style="bold red3")
                        n += 1

                asset = symbol
                self.check_main_portfolio(asset=asset,quantity=quantity, price=price, type=type, p_price=p_price)


            elif type == "crypto":
                cmc = self.crypto_api
                asset, price = cmc.get_crypto_price(symbol)
                self.check_main_portfolio(asset=asset,quantity=quantity, price=price, type=type, p_price=p_price)

            elif type == "currency":
                self.check_main_portfolio(asset=symbol,quantity=quantity, price=price, type=type, p_price=p_price)


    def save_portfolio(self):
        data = self.main_portfolio

        initial_dir = os.path.expanduser("~") #Gets the home directory of the user
        Title = "Save as csv:"
        filetypes =[("csv Files","*.csv")]
        self.tk_root.deiconify() #Show the tkinter window so that filedialog can run
        self.tk_root.attributes('-topmost', True)  # Make the window pop up in front of the IDE
        try:
            file_name = fd.asksaveasfilename(initialdir=initial_dir, parent=self.tk_root, title=Title, filetypes=filetypes, confirmoverwrite=True, defaultextension=".csv")
        except TclError:
                self.console.print("This IDE does not support this function.", style="bold")
                return
        self.tk_root.attributes('-topmost', False)
        self.tk_root.withdraw() #Hide the tkinter window again

        if file_name == "": #The empty string happens when the user cancels the selection of a file
            print("No file was selected.")

        else:
            with open(file_name, "w", newline="", encoding="utf-8") as f:
                fieldnames = ["symbol", "quantity", "price", "value(usd)", "type", "p_price", "profit"]
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(data)


    def check_main_portfolio(self, asset, quantity, price, type, p_price):

        value = round(price * quantity, 3)
        original_value = round(p_price * quantity, 3)
        profit = self.get_profit(value, original_value, type)

        if self.main_portfolio == []:
            self.main_portfolio.append({"symbol" : asset, "quantity" : quantity, "price" : price, "value(usd)" : value, "type" : type, "p_price" : p_price, "profit": profit})
            return

        for i in range(len(self.main_portfolio)):
            if self.main_portfolio[i]["symbol"] == asset:
                self.main_portfolio[i]["p_price"] = ((self.main_portfolio[i]["quantity"]/(self.main_portfolio[i]["quantity"] + quantity)) * self.main_portfolio[i]["p_price"]) + ((quantity/(self.main_portfolio[i]["quantity"] + quantity)) * p_price) #weighted average to get the medium purchase price
                self.main_portfolio[i]["price"] = price
                self.main_portfolio[i]["quantity"] += quantity
                self.main_portfolio[i]["value(usd)"] += value
                self.main_portfolio[i]["profit"] = value - original_value 
                return

        self.main_portfolio.append({"symbol" : asset, "quantity" : quantity, "price" : price, "value(usd)" : value, "type" : type, "p_price" : p_price, "profit" : profit})


    def get_amount_to_add(self):
         while True:
            try:
                amount_to_add = float(input("How many coins do you have? \nInsert number of coins: "))

            except ValueError:
                self.console.print("The value should be a number.", style="bold red3")

            else:
                return amount_to_add
            
    def get_p_price(self):
        while True:
            try:
                p_price = float(input("\nAt what price did you purchase them? \nInsert purchase price: "))

            except ValueError:
                self.console.print("The value should be a number.", style="bold red3")

            else:
                return p_price
            
    def get_profit(self, value, original_value, type):
        if type == "currency":
            profit = 0
        else:
            profit = value - original_value
        
        return profit

        

    def add_crypto_to_portfolio(self):
        cmc = self.crypto_api
        print()
        symbol = input("Which cryptocurrency would you like to add? \nInsert the symbol here(i.e. BTC): ").strip().upper()
        available_coins = cmc.all_coins.values()

        if symbol in available_coins:
            asset, price = cmc.get_crypto_price(symbol)
            self.check_main_portfolio(asset=asset,quantity=self.get_amount_to_add(), price=price, type="crypto", p_price=self.get_p_price())
            print()
            self.console.print("Asset successfully added!", style="bold green")
            print()


        elif isinstance(symbol, str):
            print()
            self.console.print("That symbol is not available or does not exist.", style="red3 bold")
            print()


        else:
            print()
            self.console.print("The input must be a string: (i.e. BTC)")
            print()


    def get_shares_to_add(self):
         while True:
            try:
                shares_to_add = float(input("How many shares would you like to add? \nInsert value here: "))

            except ValueError:
                self.console.print("The value should be a number.", style="bold red3")

            else:
                return shares_to_add


    def add_stock_to_portfolio(self):

        alpha = self.stocks_api
        print()

        ticker = input("Which stock/fund would you like to add? \nInsert the symbol here (i.e. AAPL): ").strip().upper()
        possible_tickers = alpha.get_possible_tickers(ticker)

        if possible_tickers == None: #For when the API isnt working
            return

        elif ticker in possible_tickers:
            asset, price = alpha.get_asset_price(ticker)
            self.check_main_portfolio(asset=asset,quantity=self.get_shares_to_add(), price=price, type="stocks/funds", p_price=self.get_p_price())
            print()
            self.console.print("Asset successfully added!", style="bold green")
            print()


        elif isinstance(ticker, str):
            print()
            self.console.print("That symbol is not available or does not exist.", style="red3 bold")
            print()

        else:
            self.console.print("The input must be a string: (i.e. AAPL)")

    def add_currency_to_portfolio(self):
        exchange_rate = self.currency_api
        available_currencies = exchange_rate.get_exchange_rate()
     
        asset = input("Which currency would you like to add? \nInsert the symbol here (i.e. USD): ").strip().upper()
        if asset not in available_currencies.keys():
            print()
            self.console.print("That currency is not available or does not exist.", style="red3 bold")
            print()
            return

        else:
            print()
            price = 1/available_currencies[asset] #because the API returns the value of the currency relative to one USD, and we want the value of one of the currency in USD
            self.check_main_portfolio(asset=asset,quantity=self.get_amount_to_add(), price=price, type="currency", p_price=price)
            print()
            self.console.print("Asset successfully added!", style="bold green")
            print()


    def remove_from_portfolio(self, asset):

        for row in self.main_portfolio:
            if asset.upper() == row["symbol"]:
                self.main_portfolio.remove(row)
                return

        print()
        self.console.print(f"{asset.upper()} is not on your Portfolio.", style="bold red3")
        self.console.print("""If you wish to add it to your Portfolio type "AS" for stocks/funds or "AC" for cryptocurrencies. """, style="bold red3")
        self.console.print("""If you want to see what is currently in your Portfolio type "D" """, style="bold red3")
        print()

    def get_new_quantity(self):
        while True:
            try:
                new_quantity = float(input("New quantity: "))

            except ValueError:
                self.console.print("The value should be a number.", style="bold red3")

            else:
                return new_quantity


    def total_value(self):
        total = 0

        for asset in self.main_portfolio:
            total += float(asset["value(usd)"])

        return total


    def total_value_stocks(self):
        total = 0

        for asset in self.main_portfolio:
            if asset["type"] == "stocks/funds":
                total += float(asset["value(usd)"])

        return total


    def total_value_crypto(self):
        total = 0

        for asset in self.main_portfolio:
            if asset["type"] == "crypto":
                total += float(asset["value(usd)"])

        return total

    def total_value_currency(self):
        total = 0

        for asset in self.main_portfolio:
            if asset["type"] == "currency":
                total += float(asset["value(usd)"])

        return total
    
    def total_profit(self):
        total = 0

        for asset in self.main_portfolio:
            total += float(asset["profit"])

        return total

    def display_portfolio(self):

        print()
        table = Table(title="📈 My Portfolio", box=box.HEAVY_HEAD, leading=1, show_lines=True)

        table.add_column("Symbol/Ticker", justify="center", style="cyan", no_wrap=True)
        table.add_column("Quantity", style="", justify="center")
        table.add_column("Price(USD)", justify="center", style = "magenta")
        table.add_column("Value(USD)", justify="center", style="blue")
        table.add_column("Medium Purchase Price(USD)", justify="center")
        table.add_column("Profit(USD)", justify="center", style="green")


        if  self.main_portfolio == []:
            print()
            self.console.print("Your Portfolio is still empty.", style="bold red3")
            self.console.print("""If you want to add cryptocurrencies type "AC" """, style="bold")
            self.console.print("""If you want to add stocks/funds type "AS" """, style="bold")
            print()

        else:
            for row in self.main_portfolio:
                table.add_row(row["symbol"], str(row["quantity"]), f"""${row["price"]:,.2f}""" , f"""${row["value(usd)"]:,.2f}""", f"""${row["p_price"]:,.2f}""", f"""${row["profit"]:,.2f}""" )

            self.console.print(table)
            print()


    def get_insights(self):
        total_value_dollars = self.total_value()
        total_value_crypto = self.total_value_crypto()
        total_value_stocks = self.total_value_stocks()
        total_value_currency = self.total_value_currency()
        total_profit_dollars = self.total_profit()

        exchange_rate = self.currency_api
        available_currencies = exchange_rate.get_exchange_rate()
        total_value_euros = total_value_dollars * [available_currencies["EUR"]][0] #The API returns a dictionary with the values of the currencies relative to one USD, so we multiply by the value of the euro
        total_profit_euros = total_profit_dollars * [available_currencies["EUR"]][0]

        table = Table(title="📈 My Portfolio --- Insights", box=box.HEAVY_HEAD, leading=1, show_lines=True)

        table.add_column("Asset", justify="center", style="cyan", no_wrap=True)
        table.add_column("Value", justify="center", style="green")

        if  self.main_portfolio == []:
            print()
            self.console.print("Your Portfolio is still empty.", style="bold red3")
            self.console.print("""If you want to add cryptocurrencies type "AC" """, style="bold")
            self.console.print("""If you want to add stocks/funds type "AS" """, style="bold")
            print()

        else:

            table.add_row("Crypto", f"""${total_value_crypto:,.2f}""")
            table.add_row("Stocks/Funds", f"""${total_value_stocks:,.2f}""")
            table.add_row("Currency", f"""${total_value_currency:,.2f}""")
            table.add_row("Total Value $", f"""${total_value_dollars:,.2f}""")
            table.add_row("Total Value", f"""€{total_value_euros:,.2f}""")
            table.add_row("Total Profit $", f"""€{total_profit_dollars:,.2f}""")
            table.add_row("Total Profit €", f"""€{total_profit_euros:,.2f}""")



            self.console.print(table)
            print()



"""
The user chooses a cryptocurrency and inputs the value which he holds.
We get the latest market value, and calculate how much money its worth (they will have to input how many coins they have).
Store the information in a list of dictionaries which will contain:[{"symbol" : "AVAX", "coins" : "20", "value(usd)": "1000"}]

"""
class Crypto:
    def __init__(self,private_key):
        self.private_key = private_key
        self.headers = {"Accepts" : "application/json", "X-CMC_PRO_API_KEY" :self.private_key}
        self._base_url = "https://pro-api.coinmarketcap.com"
        self.session = Session()
        self.session.headers.update(self.headers) #so we dont need to keep repeating the headers everytime we make a request
        self.all_coins = self.get_all_coins()
        self.console = Console()


    def symbol_search(self, search):
        possible_symbols = {}
        all_coins_names = self.get_all_coins()

        for coin in all_coins_names.keys():
            if coin.lower().startswith(search.lower()) or all_coins_names[coin].lower().startswith(search.lower()):
                possible_symbols[coin] = all_coins_names[coin]

        return possible_symbols



    #get a list of all the major coin symbols. Will be used for error checking the input
    #The program will only offer the first 5000 crytpocurrencies listed on CMC
    def get_all_coins(self):
        parameters = { "sort" : "cmc_rank",
                      "limit" : "5000"

        }

        available_coins = {}

        try:
            r = self.session.get(self._base_url + "/v1/cryptocurrency/map", params=parameters)


        except (ConnectionError, Timeout, TooManyRedirects) as error:
            print(error)


        else:
            data = r.json()["data"]
            for i in range(len(data)):
                available_coins[data[i]["name"]] = data[i]["symbol"]

            return available_coins


    #Get the crypto price
    def get_crypto_price(self, cryptocurrency):
        parameters = {"symbol" : cryptocurrency.upper(),
        }
        try:
            r = self.session.get(self._base_url + "/v1/cryptocurrency/quotes/latest", params=parameters)
            print()
            print("Processing request ...")
            self.console.print("Request accepted!", style="green bold")
            print()

        except (ConnectionError, Timeout, TooManyRedirects) as error:
            print(error)


        else:
            price = round(r.json()["data"][cryptocurrency.upper()]["quote"]["USD"]["price"], 3)
            return cryptocurrency, price



"""
The user chooses a stock/fund and inputs the value which he holds.
We get the latest market value, and calculate how much money its worth (they will have to input how many shares they have).
Store the information in a list of dictionaries which will contain:[{"symbol" : "AAPL", "quantity" : "20", "value(usd)": "1000"}]

"""

class Stocks:
    def __init__(self,private_key):
        self.private_key = private_key
        self._base_url = "https://www.alphavantage.co"
        self.session = Session()
        self.console = Console()

    def ticker_search(self, asset): #allow the user to search for their stock symbol if they are not sure what it is
        parameters = {"function" : "SYMBOL_SEARCH",
                      "keywords" : asset,
                      "apikey" : self.private_key
        }

        possible_tickers = []

        try:
            r = self.session.get(self._base_url + "/query", params=parameters)

        except (ConnectionError, Timeout, TooManyRedirects) as error:
            print(error)

        else:
            try:
                data = r.json()["bestMatches"]
                for i in range(len(data)):
                    possible_tickers.append(data[i]["1. symbol"])

                return possible_tickers

            except KeyError:
                print()
                self.console.print("API not working :(", style="bold red3")
                self.console.print("Try again later.", style="bold")
                print()



    def get_possible_tickers(self, asset): #gets the possible tickers that the user can input. Will be used for error checking the input
        parameters = {"function" : "SYMBOL_SEARCH",
                      "keywords" : asset,
                      "apikey" : self.private_key
        }

        possible_tickers = []

        try:
            r = self.session.get(self._base_url + "/query", params=parameters)

        except (ConnectionError, Timeout, TooManyRedirects) as error:
            print(error)

        else:
            try:
                data = r.json()["bestMatches"]
                for i in range(len(data)):
                    possible_tickers.append(data[i]["1. symbol"])

                return possible_tickers

            except KeyError:
                print()
                self.console.print("API not working :(", style="bold red3")
                self.console.print("Try again later.", style="bold")
                print()

    #Get the assets price
    def get_asset_price(self, asset):
        parameters = {"function" : "TIME_SERIES_DAILY",
                      "symbol" : asset,
                      "apikey" : self.private_key
        }
        try:
            r = self.session.get(self._base_url + "/query", params=parameters)

            print()
            print("Processing request ...")
            self.console.print("Request accepted!", style="green bold")
            print()

        except (ConnectionError, Timeout, TooManyRedirects) as error:
            print(error)

        else:
            try:
                data = r.json()["Time Series (Daily)"]
                most_recent_day = next(iter(data)) #gets the first iteration of the dictionary, which corresponds to the most recent day available
                last_value = float(data[most_recent_day]["4. close"])
                return asset, last_value

            except KeyError:
                print()
                self.console.print("API not working :(", style="bold red3")
                self.console.print("Try again later.", style="bold")
                print()
        
class Currency:
    def __init__(self,private_key):
        self.private_key = private_key
        self._base_url = "https://v6.exchangerate-api.com/v6"
        self.session = Session()
        self.console = Console()

    def get_exchange_rate(self):
        try:
            r = self.session.get(self._base_url + f"/{self.private_key}/latest/USD")

            print()
            print("Processing request ...")
            self.console.print("Request accepted!", style="green bold")
            print()

        except (ConnectionError, Timeout, TooManyRedirects) as error:
            print(error)

        else:
            data = r.json()["conversion_rates"]
            return data


class UI:

    def __init__(self):
        self.program_running = True #Initiating the loop that will be stoped only when the command "Q" is prompted
        self.portfolio = Portfolio()
        self.crypto_api = self.portfolio.crypto_api #just so I don't have to keep writing ".porfolio."
        self.stocks_api = self.portfolio.stocks_api
        self.currency_api = self.portfolio.currency_api
        self.console = Console()


    def welcome(self):
        welcome ="""
-------------------- Portfolio for All! --------------------
    Combine all your investments in one place,
    Import them as a csv,
    And much more!
"""
        warning = """
Please Note: If you are running the code in Github Codespaces the following actions will not work
- Import porfolio
- Save portfolio
If you wish to use them please switch to an IDE with tkinter support (VScode for example)
    """

        self.console.print(welcome, style="bold magenta")
        self.console.print(warning, style="bold red3 italic")
        self.console.print("""To see all available commands type "H". """, style="bold italic")
        print()


    def command_help(self):
        print()
        self.console.print(" Available commands ", style="bold dark_red")
        self.console.print("--------------------", style="bold dark_red")
        self.console.print("H - Help (see all available commands) ", style="green")
        self.console.print("SS - Search for Stocks ", style="green")
        self.console.print("SC - Search for Cryptocurrencies ", style="green")
        self.console.print("SAC - See Available Common Currencies ", style="green")
        self.console.print("AS - Add Stock/Fund to Portfolio ", style="green")
        self.console.print("AC - Add Cryptocurrency to Portfolio", style="green")
        self.console.print("ACC - Add Common currency to Portfolio (i.e. USD)", style="green")
        self.console.print("S - Save Portfolio as csv", style="green")
        self.console.print("I - Import Portfolio (csv) ", style="green")
        self.console.print("RM - Remove from Portfolio ", style="green")
        self.console.print("D - Display Portfolio ", style="green")
        self.console.print("GI - Get insights", style="green")
        self.console.print("Q - Quit ", style="green")
        print()


    def command_display_portfolio(self):
        self.portfolio.display_portfolio()

    def command_save_portfolio(self):
        if self.portfolio.main_portfolio == []:
            print()
            self.console.print("Your Portfolio is still empty.", style="bold red3")
            self.console.print("In order to save your Portfolio you have to add some assets first: ", style="bold red3")
            print()
            self.console.print("""If you want to add cryptocurrencies type "AC" """, style="bold")
            self.console.print("""If you want to add stocks/funds type "AS" """, style="bold")

            print()
            return

        self.portfolio.save_portfolio()

    def command_add_crypto_to_portfolio(self):
        self.portfolio.add_crypto_to_portfolio()

    def command_add_stock_to_portfolio(self):
        self.portfolio.add_stock_to_portfolio()

    def command_add_currency_to_portfolio(self):
        self.portfolio.add_currency_to_portfolio()

    def command_import_portfolio(self):
        print()
        self.console.print("Warning: Be mindful that you should only import portfolios that you have previously made in this program.", style="bold red3")
        self.console.print("If you import a portfolio that was not made in this program it will not work.", style="bold red3")
        print()
        answer = input("Do you wish to continue? [Y/n]: ").strip().lower()
        if answer == "yes" or answer == "y":
            self.portfolio.process_csv()
            self.console.print("Portfolio successfully imported!", style="bold green")
            print()
        elif answer == "no" or answer == "n":
            print()
            return
        else:
            self.console.print("That is not a valid input.", style="bold red3")
            return

    def command_remove_from_portfolio(self):

        if self.portfolio.main_portfolio == []:
            print()
            self.console.print("Your Portfolio is empty.", style="bold red3")
            print()
            return

        while True:
            try:
                asset = str(input("Asset you want to remove (i.e. META): ")).strip()
                self.portfolio.remove_from_portfolio(asset)
                break

            except ValueError:
                print()
                self.console.print("The input must be a string", style="bold red3")

    def command_search_crypto(self):
        possible_symbols = self.crypto_api.symbol_search(input("Search:"))
        print()

        if not possible_symbols:
            self.console.print("There are no cryptocurrencies with that name.",style= "bold red3")
            print()
            return

        for crypto in possible_symbols.keys():
            self.console.print(f"{crypto} - {possible_symbols[crypto]}", style="bold green")

        while True:
            answer = input("Do you wish to add something to your Portfolio? [Y/n]: ").strip().lower()
            if answer == "yes" or answer == "y":
                self.command_add_crypto_to_portfolio()
                return
            elif answer == "no" or answer == "n":
                return
            else:
                self.console.print("That is not a valid input.", style="bold red3")


    def command_search_stocks(self):
        possible_tickers = self.stocks_api.ticker_search(input("Search:"))
        print()

        if not possible_tickers:
            self.console.print("There are no stocks/funds with that name.", style="bold red3")
            print()
            return

        for stock in possible_tickers:
            self.console.print(f". {stock}", style="bold green")


        while True:
            answer = input("Do you wish to add something to your Portfolio? [Y/n]: ").strip().lower()
            if answer == "yes" or answer == "y":
                self.command_add_stock_to_portfolio()
                return
            elif answer == "no" or answer == "n":
                return
            else:
                self.console.print("That is not a valid input.", style="bold red3")


    def command_check_available_common_currency(self):
        available_currencies = self.currency_api.get_exchange_rate()

        print()

        self.console.print("AVAILABLE CURRENCIES:", style="bold cyan")
        for currency in available_currencies.keys():
            self.console.print(f" - {currency} ✓", style="bold green")
        
        self.console.print("AVAILABLE CURRENCIES (scroll up to see them all)", style="bold cyan")
        print()
        while True:
            answer = input("Do you wish to add something to your Portfolio? [Y/n]: ").strip().lower()
            if answer == "yes" or answer == "y":
                self.command_add_currency_to_portfolio()
                return
            elif answer == "no" or answer == "n":
                return
            else:
                self.console.print("That is not a valid input.", style="bold red3")

    def command_get_insights(self):
        self.portfolio.get_insights()

    def command_quit_program(self):
        print()
        self.console.print("Goodbye!", style="bold magenta")
        self.console.print("Hope you enjoyed using my program!", style="bold magenta")
        self.console.print("See you next time :)", style="bold magenta")
        print()
        self.program_running = False


    def get_input(self):
        available_commands = ["H","A","S","I","D","Q","AS","AC","SS","SC","RM","GI","ACC","SAC"]
        try:
            command = input("Input command: ").upper()
            if command not in available_commands:
                raise ValueError
            return command

        except ValueError:
            print()
            self.console.print("""Invalid command. (Perhaps you want help? Type "H" for help)""", style="red3 bold")
            print()


    def run(self):
        self.welcome()
        while self.program_running:
            command = self.get_input()

            if command == "Q":
                self.command_quit_program()

            elif command == "H":
                self.command_help()

            elif command == "D":
                self.command_display_portfolio()

            elif command == "GI":
                self.command_get_insights()

            elif command == "AC":
                self.command_add_crypto_to_portfolio()

            elif command == "AS":
                self.command_add_stock_to_portfolio()

            elif command == "ACC":
                self.command_add_currency_to_portfolio()

            elif command == "I":
                self.command_import_portfolio()

            elif command == "S":
                self.command_save_portfolio()

            elif command == "RM":
                self.command_remove_from_portfolio()

            elif command == "SS":
                self.command_search_stocks()

            elif command == "SC":
                self.command_search_crypto()

            elif command == "SAC":
                self.command_check_available_common_currency()



def main():
    """
    The main function initializes the UI class and starts the program loop.
    It serves as the entry point for the application.
    """
    ui = UI()
    ui.run()



if __name__ == "__main__":
    main()




