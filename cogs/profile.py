from __future__ import annotations

import discord
import logging

from discord import app_commands
from discord.ext import commands

from typing import TYPE_CHECKING, cast

if TYPE_CHECKING:
    from main import Bot

logger = logging.getLogger()

@app_commands.guild_only()
class Profile(commands.GroupCog, group_name='profile'):
    def __init__(self, bot: Bot) -> None:
        self.bot = bot

    @app_commands.command(name='set')
    async def set(self, interaction: discord.Interaction, description: str):
        """Set or view your profile description."""
        await interaction.response.defer(thinking=True)
        await self.bot.database.update_user_about(interaction.user, description)
        embed = self.bot.info_embed(
            title="Profile Updated",
            description=f"Your profile description has been updated to: {description}"
        )
        await interaction.followup.send(embed=embed)
        await self.bot.log_message(f"{interaction.user} updated their profile description to: {description}")

    @app_commands.command(name='view')
    async def view(self, interaction: discord.Interaction, member: discord.Member | None = None):
        """View your profile or someone else's profile."""
        if member is None:
            member = cast(discord.Member, interaction.user)

        if not self.bot.check_user_is_registrant(member):
            embed = self.bot.error_embed(
                title="Profile Not Found",
                description=f"{member} is not registered."
            )
            await interaction.response.send_message(embed=embed)
            return

        about = await self.bot.database.fetch_user_about(member)

        user_data = self.bot.registrant_discord_mapping.get(str(member))
        if user_data is None:
            embed = self.bot.error_embed(
                title="Profile Not Found",
                description=f"No data found for {member}."
            )
            await interaction.response.send_message(embed=embed)
            return

        embed = discord.Embed(
            title=f"{member}'s Profile",
            description=about or "No description set.",
            color=self.bot.config.bot.embed_info_color
        )
        embed.add_field(name="Full Name", value=user_data.get("full_name", "Not set"), inline=False)
        embed.add_field(name="School", value=user_data.get("school", "Not set"), inline=False)
        embed.add_field(name="Grade", value=user_data.get("grade", "Not set"), inline=False)
        embed.add_field(name="SHSM Sector", value=user_data.get("shsm_sector", "Not set"), inline=False)
        await interaction.response.send_message(embed=embed)

async def setup(bot: Bot) -> None:
    await bot.add_cog(Profile(bot), guilds=[discord.Object(bot.config.bot.guild_id)])
