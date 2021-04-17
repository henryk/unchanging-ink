import time
import logging

logger = logging.getLogger(__name__)


def main():
    from .create_tables import main as create_tables_main

    logger.info("Creating tables")
    create_tables_main()

    logger.info("Worker ready")
    while True:
        time.sleep(1)


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    main()
