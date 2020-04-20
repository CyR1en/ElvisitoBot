import contextlib
import logging
import sys

from bot import Bot
from configuration import ConfigFile, ConfigNode

logger = logging.getLogger(__name__)


@contextlib.contextmanager
def setup_logging():
    try:
        # __enter__
        logging.getLogger('discord').setLevel(logging.INFO)

        log = logging.getLogger()
        log.setLevel(logging.INFO)
        handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
        fmt = logging.Formatter('[%(levelname)s][%(asctime)s][%(name)s]: %(message)s')
        s_handler = logging.StreamHandler()
        s_handler.setFormatter(fmt)
        handler.setFormatter(fmt)
        log.addHandler(handler)
        log.addHandler(s_handler)

        yield
    finally:
        # __exit__
        for handler in log.handlers[:]:
            handler.close()
            log.removeHandler(handler)


def check_token(configuration):
    token = configuration.get(ConfigNode.TOKEN)
    if token == ConfigNode.TOKEN.get_value():
        logger.warning("The config file is either newly generated or the token was left to its default value. \n"
                       "Please enter your bot's token:")
        try:
            token = input()
            configuration.set(ConfigNode.TOKEN, token)
        except KeyboardInterrupt:
            logger.error("Interrupted token input")
            sys.exit()


if __name__ == '__main__':
    with setup_logging():
        config = ConfigFile("config")
        check_token(config)
        Bot(config).start_bot()


