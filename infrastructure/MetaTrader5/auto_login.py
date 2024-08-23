"""
VNC Client for MetaTrader 5 Docker Login

## Resources:
    - https://github.com/sibson/vncdotool/blob/main/docs/library.rst
"""

import os
import time
from vncdotool import api
from dotenv import load_dotenv

class VNCMT5Client:
    """
    A client to automate MetaTrader 5 login using VNC.

    Attributes:
        client (api.VNCDoToolClient): The VNC client connection object.
    """
    def __init__(self, server_url, password=None, timeout=10):
        """
        Initialize the VNCMT5Client with the server URL and optional password.

        :param server_url: The VNC server URL to connect to.
        :param password: The password for the VNC server (default is None).
        :param timeout: Timeout for the VNC client connection (default is 10 seconds).
        """
        self.client = api.connect(server_url, password=password)
        self.client.timeout = timeout

    def clear_and_type_value(self, value, empty_field: bool = False, next_field_count: int = 1):
        """
        Clears a form field, enters a new value, and optionally moves to the next field.

        :param value: The string value to enter in the form field.
        :param empty_field: Whether to empty the field before entering the value (default is False).
        :param next_field_count: The number of times to press 'Tab' to move to the next field.
        """
        if not empty_field:
            # Select all text and delete it
            self.client.keyPress('ctrl-A')
            self.client.keyPress('del')
            time.sleep(0.1)

        # Enter the new value with a slight delay between each character
        for character in value:
            self.client.keyPress(character)
            time.sleep(0.1)

        # Optionally, press Tab to move to the next field
        for _ in range(next_field_count):
            self.client.keyPress('tab')
            time.sleep(0.1)
        
        time.sleep(2)

    def ping_mt_server(self, server):
        """
        Ping MetaTrader's server by searching for the broker server in the list of company servers available.
        
        :param server: The broker server name to search for.
        """
        # Click on the File tab
        self.client.mouseMove(20, 22)
        self.client.mousePress(1)
        time.sleep(0.5)

        # Click on Open an Account
        self.client.mouseMove(100, 310)
        self.client.mousePress(1)
        time.sleep(0.5)

        # Search for server in list of companies 
        self.client.mouseMove(350, 250)
        self.client.mousePress(1)
        time.sleep(0.5)

        self.clear_and_type_value(server, empty_field=True)
        self.client.keyPress('enter')
        time.sleep(2)

        # Close search Dialog 
        self.client.mouseMove(930, 630)
        self.client.mousePress(1)
        time.sleep(0.5)

    def login_to_mt5(self, login, password, server):
        """
        Logs in to the MetaTrader 5 account.

        :param login: The MetaTrader 5 account login number.
        :param password: The MetaTrader 5 account password.
        :param server: The MetaTrader 5 server name.
        """
        # Probe server
        self.ping_mt_server(server)
        time.sleep(5)

        # Click on the File tab
        self.client.mouseMove(20, 22)
        self.client.mousePress(1)
        time.sleep(0.5)

        # Click on Login to Trade Account
        self.client.mouseMove(100, 380)
        self.client.mousePress(1)

        # Fill the Login form
        self.clear_and_type_value(login)
        # Move to the next field
        self.clear_and_type_value(password, next_field_count=2)
        # Move to the next field
        self.clear_and_type_value(server, empty_field=True)

        time.sleep(0.2)
        self.client.keyPress('enter')
        time.sleep(10)

    def enable_algo_trading(self):
        """
        Enables algorithmic trading on the MetaTrader 5 platform.
        """
        # Enable Algo trading
        self.client.mouseMove(890, 50)
        self.client.mousePress(1)
        time.sleep(0.1)

    def open_journal_tab(self):
        """
        Tries to open the Journal tab on MetaTrader 5 (optional).
        """
        # Try to open Journal tab (optional)
        self.client.mouseMove(690, 760)
        self.client.mousePress(1)
        time.sleep(0.1)

    def capture_screenshot(self, file_name='screenshot.png'):
        """
        Captures a screenshot of the current VNC screen.

        :param file_name: The name of the file to save the screenshot (default is 'screenshot.png').
        """
        try:
            self.client.captureScreen(file_name)
        except TimeoutError:
            print('Timeout when capturing screen')

    def disconnect(self):
        """
        Disconnects the VNC client.
        """
        self.client.disconnect()


if __name__ == "__main__":
    load_dotenv()

    VNC_SERVER_URL = "localhost"
    VNC_SERVER_PASSWORD = None

    login = os.environ['MT5_ACCOUNT_NUMBER']
    password = os.environ['MT5_PASSWORD']
    server = os.environ['MT5_SERVER']

    # Create a VNCMT5Client instance
    vnc_mt5_client = VNCMT5Client(VNC_SERVER_URL, password=VNC_SERVER_PASSWORD)

    # Log in to MetaTrader 5
    vnc_mt5_client.login_to_mt5(login, password, server)

    # Enable algorithmic trading
    vnc_mt5_client.enable_algo_trading()

    # Optionally open the Journal tab
    vnc_mt5_client.open_journal_tab()

    # Capture a screenshot
    vnc_mt5_client.capture_screenshot()

    # Disconnect the VNC client
    vnc_mt5_client.disconnect()

    print('Login Attempt Done...')
