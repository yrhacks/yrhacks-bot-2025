from __future__ import annotations

import asyncio
import discord
import logging
import logging.handlers
import os
import pathlib
import toml

from dotenv import load_dotenv
from supabase._async.client import create_client

from utils import Bot, Config, Database

logger = logging.getLogger()

def configure_logging() -> None:
    logging.getLogger('httpx').setLevel(logging.WARNING)

    discord.utils.setup_logging(
        level=logging.INFO,
        handler=logging.FileHandler('discord.log', encoding='utf-8'),
        root=True,
    )

    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.INFO)
    dt_fmt = '%Y-%m-%d %H:%M:%S'
    formatter = logging.Formatter('[{asctime}] [{levelname:<8}] {name}: {message}', dt_fmt, style='{')
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

def load_config() -> Config | None:
    data = toml.load(pathlib.Path(__file__).parent / 'data/config.toml')
    config = Config(data)
    checked_properties = {
        'bot': {'guild_id', 'log_channel_id', 'unverified_role_id', 'hacker_role_id', 'sync_guild_commands'},
        'embeds': {'info_color', 'success_color', 'error_color'},
    }

    for section, required_keys in checked_properties.items():
        for key in required_keys:
            if key not in config[section] or config[section][key] == '' or isinstance(config[section][key], int) and config[section][key] == 123:
                logger.error(f"Missing required key '{key}' in section '{section}' of config.toml")
                return None

    return config

async def main():
    configure_logging()
    config = load_config()
    if config is None:
        logger.error("Failed to load configuration. Exiting.")
        return

    load_dotenv()
    token = os.getenv('DISCORD_TOKEN')
    if not token:
        logger.error("DISCORD_TOKEN environment variable not set.")
        return

    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_KEY')
    if not supabase_url or not supabase_key:
        logger.error("SUPABASE_URL or SUPABASE_KEY environment variable not set.")
        return
    
    supabase = await create_client(supabase_url, supabase_key)
    logger.info("Connected to Supabase")
    database = Database(supabase)

    async with Bot(config, database) as bot:
        await bot.start(token)

asyncio.run(main())
