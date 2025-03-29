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
        'bot': {'discord_token', 'guild_id', 'log_channel_id', 'unverified_role_id', 'hacker_role_id', 'sync_guild_commands'},
        'embeds': {'info_color', 'success_color', 'error_color'},
        'database': {'supabase_url', 'supabase_key'}
    }

    for section, required_keys in checked_properties.items():
        for key in required_keys:
            if key not in config[section] or config[section][key] == '' or isinstance(config[section][key], int) and config[section][key] == 123:
                raise ValueError(f"Missing required key '{key}' in section '{section}' of config.toml")

    return config

async def main():
    load_dotenv()
    configure_logging()
    config = load_config()

    async with Bot(config) as bot:
        await bot.start(config.bot.discord_token)

asyncio.run(main())
