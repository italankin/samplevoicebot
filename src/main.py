import logging
import os

from bot import Bot
from config import Config


def main():
    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        level=logging.DEBUG if os.getenv('DEBUG') == "1" else logging.INFO
    )

    aps_logger = logging.getLogger('apscheduler')
    aps_logger.setLevel(logging.WARNING)

    bot = Bot(Config())
    bot.run()


if __name__ == '__main__':
    main()
