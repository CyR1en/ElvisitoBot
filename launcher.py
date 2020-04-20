import contextlib
import logging

from bot import Bot


@contextlib.contextmanager
def setup_logging():
    try:
        # __enter__
        logging.getLogger('discord').setLevel(logging.DEBUG)

        log = logging.getLogger()
        log.setLevel(logging.DEBUG)
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


if __name__ == '__main__':
    with setup_logging():
        Bot()
