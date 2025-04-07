from __future__ import annotations

import discord

from typing import TYPE_CHECKING, cast

if TYPE_CHECKING:
    from main import Bot

class TeamInviteView(discord.ui.View):
    def __init__(self, bot: Bot, team_name: str, inviter: discord.Member | discord.User, invitee: discord.Member | discord.User, team_id: int) -> None:
        super().__init__(timeout=None)
        self.bot = bot
        self.team_name = team_name
        self.inviter = inviter
        self.invitee = invitee
        self.team_id = team_id
        self.finished = False

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.invitee.id:
            await interaction.response.send_message("You cannot interact with this button.", ephemeral=True)
            return False
        return True

    async def submit(self, interaction: discord.Interaction, accepted: bool) -> None:
        await interaction.response.defer(thinking=True)
        if self.finished:
            return

        user = interaction.user
        if accepted:
            await self.bot.database.accept_team_invite(user, self.team_id)
        else:
            await self.bot.database.decline_team_invite(user, self.team_id)

        status = "accepted" if accepted else "declined"
        await interaction.followup.send(embed=self.bot.info_embed(f"You have __{status}__ the invite to join `{self.team_name}`."))

        # Notify inviter
        try:
            await self.inviter.send(embed=self.bot.info_embed(f"{user.mention} has __{status}__ your invite to join `{self.team_name}`."))
        except discord.Forbidden:
            pass  # Can't DM inviter

        for child in cast(list[discord.ui.Button], self.children):
            child.disabled = True

        self.stop()
        await interaction.response.edit_message(view=self)

    @discord.ui.button(label="Accept", style=discord.ButtonStyle.success)
    async def accept(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        await self.submit(interaction, accepted=True)
        self.finished = True

    @discord.ui.button(label="Decline", style=discord.ButtonStyle.danger)
    async def decline(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        await self.submit(interaction, accepted=False)
        self.finished = True

