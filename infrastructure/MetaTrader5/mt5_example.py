import pandas as pd
from mt5linux import MetaTrader5

# connecto to the server
mt5 = MetaTrader5(
    # host = 'localhost' (default)
    # port = 18812       (default)
) 
# # use as you learned from: https://www.mql5.com/en/docs/integration/python_metatrader5/
mt5.initialize()
mt5.login(
   "30565290",                    # account number
   password="@Ssc21707232",      # password
   server="Deriv-Demo",          # server name as it is specified in the terminal
   timeout=120           # timeout
)

print("version: ", mt5.version())
print("terminal_info: ", mt5.terminal_info())
print("account_info: ", mt5.account_info())

rates = mt5.copy_rates_from_pos('Step Index',mt5.TIMEFRAME_M1,0,10000)
rates_df = pd.DataFrame(rates)
print(rates_df)

mt5.shutdown()


