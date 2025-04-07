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
        if len(description) > 150:
            await interaction.followup.send(embed=self.bot.error_embed(
                title="Description Too Long",
                description="Your profile description cannot exceed 150 characters."
            ))
            return

        await self.bot.database.update_user_about(interaction.user, description)
        embed = self.bot.info_embed(
            title="Profile Updated",
            description=f"Your profile description has been updated to: {description}"
        )
        await interaction.followup.send(embed=embed)
        await self.bot.log_message(f"{interaction.user.mention} updated their profile description to: {description}")

    @app_commands.command(name='view')
    async def view(self, interaction: discord.Interaction, member: discord.Member | None = None):
        """View your profile or someone else's profile."""
        if member is None:
            member = cast(discord.Member, interaction.user)

        await interaction.response.defer(thinking=True)

        registration = await self.bot.get_or_fetch_user_registration(member)
        if registration is None:
            embed = self.bot.error_embed(
                title="Profile Not Found",
                description=f"{member} is not registered."
            )
            await interaction.followup.send(embed=embed)
            return

        user_data = await self.bot.database.fetch_user(member)
        if user_data is None:
            embed = self.bot.error_embed(
                title="Profile Not Found",
                description=f"{member} is not registered."
            )
            await interaction.followup.send(embed=embed)
            return

        about = user_data["about"] if user_data else None
        team = await self.bot.database.fetch_team_by_member_id(member.id)
        if team:
            team_name = team['name']
        else:
            team_name = "No team set"

        embed = discord.Embed(
            title=f"{member}'s Profile",
            description=f'{member.mention}\n\n',
            color=self.bot.config.embeds.info_color
        )
        embed.add_field(name="About", value=about or "No description set.", inline=False)
        embed.add_field(name="Full Name", value=user_data["full_name"], inline=True)
        embed.add_field(name="Grade", value=user_data["grade"], inline=True)
        embed.add_field(name="School", value=user_data["school"], inline=True)
        embed.add_field(name="Team", value=team_name, inline=True)
        embed.add_field(name="SHSM Sector", value=user_data["shsm_sector"], inline=True)
        await interaction.followup.send(embed=embed)

async def setup(bot: Bot) -> None:
    await bot.add_cog(Profile(bot), guilds=[discord.Object(bot.config.bot.guild_id)])
