import os
from tradeflow.commons import logging
import openai._extras


def _log_loaded_unused_lib_factory(lib):
    logger = logging.Logger(name="openai_adapters")
    logger.debug(f"Disabling {lib} openai proxy")

    def _log_loaded_unused_lib(*_):
        logger.debug(
            f"Loading {lib} unavailable lib. Skipping call returning 'proxy_mock'."
        )
        return "proxy_mock"

    return _log_loaded_unused_lib


def _disable_openai_unused_libs_proxy():
    try:
        import pandas
    except ImportError:
        openai._extras.pandas_proxy.PandasProxy.__load__ = (
            _log_loaded_unused_lib_factory("pandas")
        )


def _set_openai_default_key():
    # prevent OpenAI Proxy to crash when used
    os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY", "")


def patch_openai_proxies():
    _disable_openai_unused_libs_proxy()
    _set_openai_default_key()
