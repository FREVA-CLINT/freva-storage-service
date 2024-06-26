"""Command line interface (cli) for running the stats server."""

import os
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Callable, Dict, Optional, Union

import typer
import uvicorn
from rich.prompt import Prompt

from .logger import Logger

main = typer.Typer(help="Run the freva storage service API.")


@main.command()
def start(
    port: int = typer.Option(
        os.environ.get("API_PORT", 8080), help="The port the api is running on"
    ),
    reload: bool = typer.Option(
        False, help="Reload on code changes (development mode)."
    ),
    debug: bool = typer.Option(
        bool(int(os.environ.get("DEBUG", 0))), help="Turn on debug mode."
    ),
    workers: Optional[int] = typer.Option(
        int(os.environ.get("API_WORKER", "8")),
        help="Set the number of parallel processes serving the API.",
    ),
    mongo_username: str = typer.Option(
        os.environ.get("MONGO_USERNAME", "mongo"),
        help=(
            "Set the mongoDB username as fallback for the MONGO_USERNAME "
            "env variable."
        ),
    ),
    mongo_host: str = typer.Option(
        os.environ.get("MONGO_HOST", "localhost:27017"),
        help=(
            "Set the mongoDB host sever as fallback for the MONGO_HOST "
            "env variable."
        ),
    ),
    ask_mongo_password: bool = typer.Option(
        False,
        help=(
            "Set the mongoDB user password as fallback for the "
            "MONGO_PASSWORD env variable."
        ),
    ),
    api_username: str = typer.Option(
        os.environ.get("API_USERNAME", "stats"),
        help=(
            "Set the API admin username as fallback for the API_USERNAME "
            "env variable."
        ),
    ),
    ask_api_password: bool = typer.Option(
        False,
        help=(
            "Set the API admin user password as fallback for the "
            "API_PASSWORD env variable."
        ),
    ),
) -> None:
    """Command line interface for the freva storage API."""
    defaults: Dict[str, Union[str, int]] = {
        "DEBUG": int(debug),
        "MONGO_HOST": mongo_host,
        "MONGO_USERNAME": mongo_username,
        "API_USERNAME": api_username,
    }
    api_password: Callable[[str], str] = {
        False: lambda x: os.environ.get("API_PASSWORD", "secret"),
        True: lambda x: Prompt.ask(x, password=True),
    }[ask_api_password]
    mongo_password: Callable[[str], str] = {
        False: lambda x: os.environ.get("MONGO_PASSWORD", "secret"),
        True: lambda x: Prompt.ask(x, password=True),
    }[ask_mongo_password]
    defaults["MONGO_PASSWORD"] = mongo_password("Mongodb user password")
    defaults["API_PASSWORD"] = api_password("Api user admin password")
    logger = Logger(debug=debug)
    if reload:
        logger.debug("Running in development mode.")
        workers = None
    with NamedTemporaryFile(suffix=".conf", prefix="env") as temp_f:
        Path(temp_f.name).write_text(
            "\n".join(
                [f"{k}={os.environ.get(k, v)}" for (k, v) in defaults.items()]
            ),
            encoding="utf-8",
        )
        uvicorn.run(
            "freva_storage_service.run:app",
            host="0.0.0.0",
            port=port,
            reload=reload,
            log_level=logger.getEffectiveLevel(),
            workers=workers,
            env_file=temp_f.name,
        )


if __name__ == "__main__":
    main()
