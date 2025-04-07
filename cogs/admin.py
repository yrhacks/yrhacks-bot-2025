from __future__ import annotations

import discord
import logging

from discord import app_commands
from discord.ext import commands

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from main import Bot

logger = logging.getLogger()

@app_commands.guild_only()
class Admin(commands.GroupCog, group_name='admin'):
    def __init__(self, bot: Bot) -> None:
        self.bot = bot

    @app_commands.command()
    @app_commands.checks.has_permissions(administrator=True)
    async def verify(self, interaction: discord.Interaction, member: discord.Member, full_name: str, grade: str, school: str, shsm_sector: str):
        """Verify a user."""
        await interaction.response.defer(thinking=True, ephemeral=True)
        await self.bot.database.create_user_if_not_exists({
            'discord_username': str(member),
            'full_name': full_name,
            'grade': grade,
            'school': school,
            'shsm_sector': shsm_sector,
        }, member)
        # TODO: Improve
        hacker_role = interaction.guild and interaction.guild.get_role(self.bot.config.bot.hacker_role_id)
        if hacker_role is None:
            embed = self.bot.error_embed(
                title="Role Not Found",
                description="The 'Hacker' role could not be found."
            )
            await interaction.followup.send(embed=embed)
            return
        await member.add_roles(hacker_role)
        unverified_role = interaction.guild and interaction.guild.get_role(self.bot.config.bot.unverified_role_id)
        if unverified_role is None:
            embed = self.bot.error_embed(
                title="Role Not Found",
                description="The 'Unverified' role could not be found."
            )
            await interaction.followup.send(embed=embed)
            return

        await member.remove_roles(unverified_role)
        await member.edit(nick=full_name)
        embed = self.bot.success_embed(
            title="User Verified",
            description=f"{member} has been verified."
        )
        await interaction.followup.send(embed=embed)
        await self.bot.log_message(f"{interaction.user.mention} verified {member.mention}.")

async def setup(bot: Bot) -> None:
    await bot.add_cog(Admin(bot), guilds=[discord.Object(bot.config.bot.guild_id)])
