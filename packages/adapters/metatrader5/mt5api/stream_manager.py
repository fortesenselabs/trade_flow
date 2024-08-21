import asyncio
from typing import Dict, List, Callable
import logging
import threading


class StreamManager:
    def __init__(self):
        self.stream_tasks: Dict[str, asyncio.Task] = {}
        self.stream_thread = threading.Thread(target=self._run_streaming_loop, daemon=True)
        self.stream_thread.start()

        self.logger = logging.getLogger(__name__)

    def _run_streaming_loop(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_forever()

    async def _stream_symbol_data(self, symbol: str, interval: float, func: Callable, *args, **kwargs):
        while True:
            try:
                data = func(symbol, *args, **kwargs)
                # if data:
                #     print(f"Streaming data for {symbol}: {data}")
                await asyncio.sleep(interval)
            except asyncio.CancelledError:
                print(f"Streaming for {symbol} has been stopped.")
                break
            except Exception as e:
                print(f"Error while streaming data for {symbol}: {e}")
                break

    def create_streaming_task(self, symbols: List[str], interval: float, func: Callable, *args, **kwargs):
        for symbol in symbols:
            if symbol not in self.stream_tasks:
                task = asyncio.run_coroutine_threadsafe(
                    self._stream_symbol_data(symbol, interval, func, *args, **kwargs),
                    asyncio.get_event_loop()
                )
                self.stream_tasks[symbol] = task
                print(f"Started streaming for {symbol}")

    def stop_streaming_task(self, symbols: List[str]):
        for symbol in symbols:
            if symbol in self.stream_tasks:
                self.stream_tasks[symbol].cancel()
                del self.stream_tasks[symbol]
                print(f"Stopped streaming for {symbol}")
