import asyncio
import click
from application.config.settings import Settings
from application.config.logger import AppLogger
from application.models.app_model import AppConfig
from application.app import App

logger = AppLogger(name=__name__)


@click.command()
@click.option(
    "--config_file", "-c", type=click.Path(), default="", help="Configuration file name"
)
def start_app(config_file):
    settings: Settings = Settings(config_file)
    logger.info(settings.model_dump())

    config: AppConfig = settings.get_app_config()
    asyncio.run(App.start(app_config=config))
    return 0


if __name__ == "__main__":
    start_app()
