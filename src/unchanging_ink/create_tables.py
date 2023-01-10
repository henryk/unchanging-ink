import asyncio

from .models import metadata
from .server import engine


async def main_inner():
    await engine.run_sync(metadata.create_all)


def main():
    asyncio.run(main_inner())


if __name__ == "__main__":
    main()
