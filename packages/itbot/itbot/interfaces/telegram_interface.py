from typing import List, Callable
from telethon import TelegramClient, events
from trade_flow.common.logging import Logger


class TelegramInterface:
    """
    This class is used to handle both sending messages to Telegram channels
    and listening for new messages.

    This class can be used to send messages to specified channels and users, as well as
    listen for incoming messages in specified channels, triggering defined handlers.

    Attributes:
        api_id (str): Telegram API ID required for authentication.
        api_hash (str): Telegram API Hash required for authentication.
        phone_number (str): Phone number associated with the Telegram account.
        logger (Logger): Custom logger instance for tracking events, errors, and messages.
        client (TelegramClient): The primary client for connecting to Telegram.

    Methods:
        start_client(): Starts the Telegram client and initiates the session.
        send_message(recipient: str, message: str): Sends a message to a specified user or channel.
        add_message_handler(channel_entities: List[str], handler: Callable[[events.NewMessage], None]):
            Adds a handler to process new messages in specified channels.
        run(): Keeps the client running to listen for new messages until manually stopped.
    """

    def __init__(self, phone_number: str, api_id: str, api_hash: str, logger: Logger):
        """
        Initialize the Telegram interface with the given credentials and logger.

        Args:
            phone_number (str): Phone number associated with the Telegram account.
            api_id (str): API ID for the Telegram client.
            api_hash (str): API hash for the Telegram client.
            logger (Logger): Logger instance for logging messages and errors.
        """
        self.phone_number = phone_number
        self.api_id = api_id
        self.api_hash = api_hash
        self.logger = logger

        # Initialize Telegram client with the given session name and credentials
        self.client = TelegramClient("it_bot_session", self.api_id, self.api_hash)

    def start_client(self) -> None:
        """
        Start the Telegram client session.

        This method initializes the Telegram client with the provided phone number,
        authenticates, and prepares the client for sending and receiving messages.

        Raises:
            ConnectionError: If the client fails to start or authenticate.
        """
        try:
            self.client.start(phone=self.phone_number)
            self.logger.info("Telegram client started successfully.")
        except Exception as e:
            self.logger.error(f"Failed to start Telegram client: {e}")
            raise ConnectionError(f"Could not start Telegram client: {e}")

    async def send_message(self, recipient: str, message: str) -> None:
        """
        Send a message to the specified recipient (user or channel).

        Args:
            recipient (str): The recipient's Telegram username, channel link, or user ID.
            message (str): The message content to send.

        Example:
            >>> await bot.send_message("@example_user", "Hello, this is a test message!")

        Raises:
            ValueError: If the message is empty or recipient is not valid.
        """
        if not message:
            raise ValueError("Message content cannot be empty.")

        try:
            await self.client.send_message(recipient, message)
            self.logger.info(f"Message sent to {recipient}: {message}")
        except Exception as e:
            self.logger.error(f"Failed to send message to {recipient}: {e}")
            raise

    def add_message_handler(
        self, channel_entities: List[str], handler: Callable[[events.NewMessage.Event], None]
    ) -> None:
        """
        Add a handler to process new messages in the specified Telegram channels.

        This method sets up an event listener for new messages in the given
        channels and calls the provided handler function whenever a new message
        event is detected.

        Args:
            channel_entities (List[str]): List of Telegram channel usernames or links.
            handler (Callable[[events.NewMessage.Event], None]): Callback function to process each new message event.

        Example:
            >>> def message_handler(event):
            ...     print(f"New message from {event.chat.username}: {event.message.text}")
            >>> bot.add_message_handler(["@example_channel"], message_handler)
        """

        @self.client.on(events.NewMessage(chats=channel_entities))
        async def event_listener(event):
            try:
                await handler(event)
                self.logger.info(f"Message handled from {event.chat_id}: {event.message.message}")
            except Exception as e:
                self.logger.error(f"Error handling message: {e}")

    def run(self) -> None:
        """
        Run the Telegram client and keep listening for new messages indefinitely.

        This method enters a blocking loop, which continues to run until the client is
        manually disconnected or an unexpected error occurs.

        Raises:
            RuntimeError: If the client fails to run or disconnects unexpectedly.
        """
        try:
            with self.client:
                self.logger.info("Telegram client is running and listening for messages...")
                self.client.run_until_disconnected()
        except Exception as e:
            self.logger.error(f"Telegram client encountered an issue: {e}")
            raise RuntimeError(f"Client run error: {e}")
