from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from typing import Optional

import typer
from dotenv import load_dotenv

from .agent import SocialMediaAgent
from .config import load_config

app = typer.Typer(help="Share new WordPress articles across social media platforms.")


def setup_logging(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(level=level, format="%(asctime)s | %(levelname)s | %(name)s | %(message)s")


def build_agent(config_path: Path) -> SocialMediaAgent:
    config = load_config(config_path)
    return SocialMediaAgent(config)


@app.command()
def run(
    config_path: Path = typer.Option("agent.config.yaml", help="YAML configuration file"),
    once: bool = typer.Option(False, "--once", help="Run a single polling iteration and exit"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable debug logging"),
    dotenv_path: Optional[Path] = typer.Option(None, help="Optional .env file with credentials"),
) -> None:
    """Run the agent using the provided configuration."""

    if dotenv_path:
        load_dotenv(dotenv_path)
    else:
        load_dotenv()
    setup_logging(verbose)
    agent = build_agent(config_path)
    if once:
        asyncio.run(agent.run_once())
    else:
        asyncio.run(agent.run_forever())


if __name__ == "__main__":  # pragma: no cover
    app()
