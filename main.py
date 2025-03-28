from __future__ import annotations

import asyncio
import discord
import logging
import logging.handlers
import toml
import pathlib

from dotenv import load_dotenv

from utils.config import Config
from utils.bot import Bot

def configure_logging():
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
    logging.getLogger().addHandler(stream_handler)

def load_config():
    data = toml.load(pathlib.Path(__file__).parent / 'data/config.toml')
    config = Config(data)
    checked_properties = {
        'bot': {'discord_token', 'guild_id', 'embed_info_color', 'embed_success_color', 'embed_error_color', 'log_channel_id'},
        'database': {'supabase_url', 'supabase_key'}
    }

    for section, required_keys in checked_properties.items():
        for key in required_keys:
            if key not in config[section] or not config[section][key]:
                raise ValueError(f"Missing required key '{key}' in section '{section}' of config.toml")

    return config

async def main():
    load_dotenv()
    configure_logging()
    config = load_config()

    async with Bot(config) as bot:
        await bot.start(config.bot.discord_token)

asyncio.run(main())
