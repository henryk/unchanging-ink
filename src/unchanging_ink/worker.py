import time
import logging

logger = logging.getLogger(__name__)


def main():
    logger.info("Upgrading database")
    import alembic.config
    alembicArgs = [
        '--raiseerr',
        'upgrade', 'head',
    ]
    alembic.config.main(argv=alembicArgs)

    logger.info("Worker ready")
    while True:
        time.sleep(1)


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    main()
