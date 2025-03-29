from __future__ import annotations

import discord
import json
import logging
import os
import pathlib

from discord.ext import commands
from supabase._async.client import create_client
from utils.config import Config
from utils.database import Database

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from utils.models import Registration

logger = logging.getLogger()

class Bot(commands.Bot):
    def __init__(self, config: Config) -> None:
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        super().__init__(
            command_prefix="!",
            intents=intents,
            help_command=None,
            allowed_mentions=discord.AllowedMentions(
                roles=False,
                users=True,
                everyone=False
            )
        )

        self.config = config
        self.initial_extensions = ['jishaku', 'cogs.team', 'cogs.profile', 'cogs.admin']

        os.environ["JISHAKU_NO_DM_TRACEBACK"] = "False"
        os.environ["JISHAKU_HIDE"] = "True"
        os.environ["JISHAKU_NO_UNDERSCORE"] = "True"

        self.registrant_discord_mapping: dict[str, Registration] = {}

        with open(pathlib.Path(__file__).parent.parent / 'data/registrations.json', 'r') as file:
            registrations: list[Registration] = json.load(file)
            for registration in registrations:
                if registration['discord_username']:
                    self.registrant_discord_mapping[registration['discord_username']] = registration

    async def setup_hook(self) -> None:
        for extension in self.initial_extensions:
            await self.load_extension(extension)

        if guild_id := self.config.bot.guild_id:
            if self.config.bot.sync_guild_commands:
                guild = discord.Object(guild_id)
                await self.tree.sync(guild=guild)
        else:
            logging.warning("No guild id found in config.toml. Commands not synced.")

        self.supabase = supabase = await create_client(self.config.database.supabase_url, self.config.database.supabase_key)
        logger.info("Connected to Supabase")
        self.database = Database(supabase)

    async def on_ready(self) -> None:
        logger.info(f"Logged in as {self.user} (ID: {self.user and self.user.id})")

    def error_embed(self, title: str, description: str = '') -> discord.Embed:
        return discord.Embed(title=title, color=self.config.embeds.error_color, description=description)

    def success_embed(self, title: str, description: str = '') -> discord.Embed:
        return discord.Embed(title=title, color=self.config.embeds.success_color, description=description)

    def info_embed(self, title: str, description: str = '') -> discord.Embed:
        return discord.Embed(title=title, color=self.config.embeds.info_color, description=description)

    async def log_message(self, message: str) -> None:
        guild = self.get_guild(self.config.bot.guild_id)
        if guild is None:
            logger.warning("Guild not found")
            return

        channel: discord.TextChannel | None = guild.get_channel(self.config.bot.log_channel_id)  # type: ignore
        if channel is None:
            logger.warning("Log channel not found")
            return

        embed = self.info_embed("", message)
        await channel.send(embed=embed)

    def check_user_is_registrant(self, member: discord.Member | discord.User) -> bool:
        return str(member) in self.registrant_discord_mapping

    async def on_member_join(self, member: discord.Member) -> None:
        if member.guild.id != self.config.bot.guild_id:
            logger.warning(f"Member {member} joined a different server (ID: {member.guild.id}). Ignoring.")
            return

        if self.check_user_is_registrant(member):
            role = member.guild.get_role(self.config.bot.unverified_role_id)
            if role is None:
                logger.warning(f"Hacker role not found.")
                return

            await member.add_roles(role)
            await self.database.create_user_if_not_exists(self.registrant_discord_mapping[str(member)], member)
        else:
            # TODO: Set this in the config
            role = member.guild.get_role(self.config.bot.unverified_role_id)
            if role is None:
                logger.warning(f"Unverified role not found.")
                return
            await member.add_roles(role)
            try:
                await member.send(embed=self.info_embed(
                    f"🎉 Welcome to YRHacks 2025, {member.mention}! 🎉",
                    f"We couldn't verify your Discord username with any registration records. To gain access to the server, please email us at **yrhacks@gapps.yrdsb.ca** with your full name and Discord username (`{member}`)."
                ))
            except discord.Forbidden:
                ...
                # TODO: What should happen in this case?
                # unverified_channel: discord.TextChannel | None = member.guild.get_channel(self.bot.config.bot.unverified_channel_id)  # type: ignore
                # if unverified_channel is None:
                #     logger.warning(f"Unverified channel not found. User {member} cannot be notified.")
                #     return

                # await unverified_channel.send(f"Welcome {member.mention}! We were unable to verify your registration. Please use the `/user register` command to register.")
