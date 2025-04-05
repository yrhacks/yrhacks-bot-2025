from __future__ import annotations

from discord import app_commands
from discord.ext import commands
import discord

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from main import Bot

from views.team_invite import TeamInviteView

def check_user_is_registrant(interaction: discord.Interaction[Bot]) -> bool:
    return interaction.client.check_user_is_registrant(interaction.user)

@app_commands.guild_only()
class Team(commands.GroupCog, group_name='team'):
    def __init__(self, bot: Bot) -> None:
        self.bot = bot

    async def team_autocomplete(self, interaction: discord.Interaction, current: str):
        teams = await self.bot.database.fetch_teams(interaction.user)
        return [
            app_commands.Choice(name=team['name'], value=team['id'])
            for team in teams if current.lower() in team['name'].lower()
        ]

    async def team_invite_autocomplete(self, interaction: discord.Interaction, current: str):
        teams = await self.bot.database.fetch_team_invites_for_member(interaction.user)
        return [
            app_commands.Choice(name=team['name'], value=team['id'])
            for team in teams if current.lower() in team['name'].lower()
        ]

    async def team_member_autocomplete(self, interaction: discord.Interaction, current: str):
        team = await self.bot.database.fetch_team_by_member_id(interaction.user.id)
        if not team:
            return []

        guild = interaction.guild
        if not guild:
            return []

        members = await self.bot.database.fetch_team_members(team['id'])
        return [
            app_commands.Choice(name=guild_member.display_name, value=member.id)  # type: ignore
            for member in members if current.lower() in (guild_member := guild.get_member(member.id)).display_name.lower()  # type: ignore
        ]

    @app_commands.command(name='remove')
    @app_commands.check(check_user_is_registrant)
    @app_commands.autocomplete(member=team_member_autocomplete)
    async def remove(self, interaction: discord.Interaction, member: int):
        """Remove a member from your team."""
        await interaction.response.defer(thinking=True)
        guild_member = interaction.guild.get_member(member)  # type: ignore
        if guild_member is None:
            await interaction.followup.send(embed=self.bot.error_embed("Member not found!"))
            return

        if guild_member == interaction.user:
            await interaction.followup.send(embed=self.bot.error_embed("You cannot remove yourself!"))
            return

        team = await self.bot.database.fetch_team_by_member_id(interaction.user.id)
        if not team:
            await interaction.followup.send(embed=self.bot.error_embed("You do not own a team!"))
            return

        members = await self.bot.database.fetch_team_members(team['id'])
        if guild_member not in members:
            await interaction.followup.send(embed=self.bot.error_embed(f"`{guild_member.display_name}` is not in your team!"))

        if not self.bot.check_user_is_registrant(guild_member):
            await interaction.followup.send(embed=self.bot.error_embed(f"`{guild_member.display_name}` is not registered."))
        await interaction.followup.send(embed=self.bot.success_embed(f"Removed `{guild_member.display_name}` from the team!"))

    @app_commands.command(name='accept')
    @app_commands.autocomplete(team=team_invite_autocomplete)
    async def accept(self, interaction: discord.Interaction, team: int):
        """Accept a team invitation."""
        await interaction.response.defer(thinking=True)

        team_record = await self.bot.database.fetch_team_by_id(team)
        if not team_record:
            await interaction.followup.send(embed=self.bot.error_embed("Team not found!"))
            return

        existing_team = await self.bot.database.fetch_team_by_member_id(interaction.user.id)
        if existing_team:
            await interaction.followup.send(embed=self.bot.error_embed("You must leave your existing team before accepting a new one!"))
            return

        if team_record['member_count'] >= 4:
            await interaction.followup.send(embed=self.bot.error_embed("This team is already full!"))
            return

        await self.bot.database.accept_team_invite(interaction.user, team)
        await interaction.followup.send(f"You have accepted the invitation to join the team `{team}`!")

    @app_commands.command(name='decline')
    @app_commands.autocomplete(team=team_invite_autocomplete)
    async def decline(self, interaction: discord.Interaction, team: int):
        """Decline a team invitation."""
        await interaction.response.defer(thinking=True)
        # validate team
        team_record = await self.bot.database.fetch_team_by_id(team)
        if not team_record:
            await interaction.followup.send(embed=self.bot.error_embed("Team not found!"))
            return

        await self.bot.database.decline_team_invite(interaction.user, team)
        await interaction.followup.send(f"You have declined the invitation to join the team `{team}`!")

    @app_commands.command(name='create')
    async def create(self, interaction: discord.Interaction, name: str):
        """Create a new team."""
        if len(name) > 20:
            await interaction.response.send_message(embed=self.bot.error_embed("Team name must be less than 20 characters."))
            return

        if len(name) < 3:
            await interaction.response.send_message(embed=self.bot.error_embed("Team name must be at least 3 characters."))
            return

        if not name.isalnum():
            await interaction.response.send_message(embed=self.bot.error_embed("Team name must be alphanumeric."))
            return

        await interaction.response.defer(thinking=True)

        existing_team = await self.bot.database.fetch_team_by_member_id(interaction.user.id)
        if existing_team:
            await interaction.followup.send(embed=self.bot.error_embed("You are already in a team!"))
            return

        success = await self.bot.database.create_team(name, interaction.user)
        if not success:
            await interaction.followup.send(embed=self.bot.error_embed(f"Team `{discord.utils.escape_markdown(name)}` already exists! Please try a different name."))
        else:
            await interaction.followup.send(embed=self.bot.success_embed(f"Team `{discord.utils.escape_markdown(name)}` has been created!"))

        await self.bot.log_message(f"{interaction.user.mention} has created a team `{discord.utils.escape_markdown(name)}`.")

    @app_commands.command(name='delete')
    async def delete(self, interaction: discord.Interaction):
        """Delete your team."""
        await interaction.response.defer(thinking=True)
        data = await self.bot.database.delete_team(interaction.user)
        if not data:
            await interaction.followup.send(embed=self.bot.error_embed("You do not own a team!"))
        else:
            await interaction.followup.send(embed=self.bot.success_embed(f"Team `{discord.utils.escape_markdown(data[0]['name'])}` has been deleted!"))

        await self.bot.log_message(f"{interaction.user.mention} has deleted the team `{discord.utils.escape_markdown(data[0]['name'])}`.")

    @app_commands.command(name='invite')
    async def invite(self, interaction: discord.Interaction, member: discord.Member):
        """Invite a member to your team."""
        await interaction.response.defer(thinking=True)

        inviter = interaction.user
        team_data = await self.bot.database.fetch_team_by_member_id(inviter.id)
        if team_data is None:
            await interaction.followup.send(embed=self.bot.error_embed("You do not own a team!"))
            return

        if member == interaction.user:
            await interaction.followup.send(embed=self.bot.error_embed("You cannot invite yourself!"))
            return

        if not self.bot.check_user_is_registrant(member):
            await interaction.followup.send(embed=self.bot.error_embed(f"{member.display_name} is not registered."))
            return

        existing_team = await self.bot.database.fetch_team_by_member_id(member.id)
        if existing_team:
            await interaction.followup.send(embed=self.bot.error_embed(f"{member.display_name} is already in a team!"))
            return

        try:
            # TODO: Show team members?
            view = TeamInviteView(self.bot, team_data['name'], inviter, team_data['id'])

            embed = self.bot.info_embed("🤝 Team Invitation")
            embed.add_field(name="Team", value=team_data['name'], inline=False)
            embed.add_field(name="Invited By", value=inviter.mention, inline=False)
            embed.set_footer(text="Click a button below to accept or decline.")

            await member.send(embed=embed, view=view)
            await interaction.followup.send(embed=self.bot.success_embed(f"Sent a team invite to {member.display_name}!"))
            await view.wait()
        except discord.Forbidden:
            await interaction.followup.send(embed=self.bot.error_embed(f"Unable to message {member.mention}."))

        await self.bot.log_message(f"{inviter.mention} invited {member.mention} to join `{discord.utils.escape_markdown(team_data['name'])}`.")

    @app_commands.command(name='kick')
    @app_commands.autocomplete(member=team_member_autocomplete)
    async def kick(self, interaction: discord.Interaction, member: int):
        """Kick a member from your team."""
        await interaction.response.defer(thinking=True)
        if member == interaction.user.id:
            await interaction.followup.send(embed=self.bot.error_embed("You cannot kick yourself!"))
            return

        team = await self.bot.database.fetch_team_by_member_id(interaction.user.id)
        if not team or team['owner_id'] != interaction.user.id:
            await interaction.followup.send(embed=self.bot.error_embed("You do not own a team!"))
            return

        guild_member: discord.Member = interaction.guild.get_member(member)  # type: ignore
        if not guild_member:
            await interaction.followup.send(embed=self.bot.error_embed("Member not found!"))
            return

        member_team = await self.bot.database.fetch_team_by_member_id(member)
        if not member_team or member_team['id'] != team['id']:
            await interaction.followup.send(embed=self.bot.error_embed(f"`{guild_member.display_name}` is not in your team!"))
            return

        await self.bot.database.kick_from_team(guild_member)
        await interaction.followup.send(embed=self.bot.success_embed(f"Removed `{guild_member.display_name}` from the team!"))
        await guild_member.send(embed=self.bot.info_embed(f"You have been removed from the team `{discord.utils.escape_markdown(team['name'])}`."))
        await self.bot.log_message(f"{interaction.user.mention} kicked {guild_member.display_name} from the team `{discord.utils.escape_markdown(team['name'])}`.")

    @app_commands.command(name='leave')
    async def leave(self, interaction: discord.Interaction):
        """Leave the current team."""
        await interaction.response.defer(thinking=True)
        existing_team = await self.bot.database.fetch_team_by_member_id(interaction.user.id)
        if not existing_team:
            await interaction.followup.send(embed=self.bot.error_embed("You are not in a team!"))
            return
        if existing_team['owner_id'] == interaction.user.id:
            await interaction.followup.send(embed=self.bot.error_embed("You cannot leave your own team! Please delete it instead."))
            return
        response = await self.bot.database.leave_team(interaction.user)
        if not response:
            await interaction.followup.send(embed=self.bot.error_embed("You are not in a team!"))
        else:
            await interaction.followup.send(embed=self.bot.success_embed(f"You have left the team `{discord.utils.escape_markdown(response[0]['name'])}`!"))

        await self.bot.log_message(f"{interaction.user.mention} has left the team `{discord.utils.escape_markdown(response[0]['name'])}`.")

    @app_commands.command(name='rename')
    async def rename(self, interaction: discord.Interaction, new_name: str):
        """Rename your team."""
        if len(new_name) > 20:
            await interaction.response.send_message(embed=self.bot.error_embed("Team name must be less than 20 characters."))
            return

        if len(new_name) < 3:
            await interaction.response.send_message(embed=self.bot.error_embed("Team name must be at least 3 characters."))
            return

        if not new_name.isalnum():
            await interaction.response.send_message(embed=self.bot.error_embed("Team name must be alphanumeric."))
            return

        await interaction.response.defer(thinking=True)

        response = await self.bot.database.rename_team(interaction.user.id, new_name)
        if not response:
            await interaction.followup.send(embed=self.bot.error_embed("You do not own a team!"))
            return

        await interaction.followup.send(embed=self.bot.success_embed(f"Team has been renamed to `{discord.utils.escape_markdown(new_name)}`!"))
        await self.bot.log_message(f"Team `{discord.utils.escape_markdown(new_name)}` has been renamed by {interaction.user.mention}.")

    @app_commands.command(name='view')
    @app_commands.autocomplete(team=team_autocomplete)
    async def view(self, interaction: discord.Interaction, team: int | None):
        """View the current team details."""
        await interaction.response.defer(thinking=True)
        if team is None:
            team_record = await self.bot.database.fetch_team_by_member_id(interaction.user.id)
            if not team_record:
                await interaction.followup.send(embed=self.bot.error_embed("Please specify a team!"))
                return
            team = team_record['id']
            team_name = team_record['name']
            owner = discord.Object(id=team_record['owner_id'])
        else:
            team_record = await self.bot.database.fetch_team_by_id(team)
            if not team_record:
                await interaction.followup.send(embed=self.bot.error_embed("Team not found!"))
                return
            team_name = team_record['name']
            owner = discord.Object(id=team_record['owner_id'])

        members = await self.bot.database.fetch_team_members(team)
        description = '**Members:**\n' + '\n'.join(
            [f"👑 <@{member.id}>" if member.id == owner.id else f"💻 <@{member.id}>" for member in members]
        )
        embed = discord.Embed(title=f"Team `{team_name}`", description=description)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name='viewall')
    async def viewall(self, interaction: discord.Interaction):
        """View all teams."""
        await interaction.response.defer(thinking=True)
        teams = await self.bot.database.fetch_teams(interaction.user)
        if not teams:
            await interaction.followup.send(embed=self.bot.error_embed("You do not own a team!"))
            return

        description = '\n'.join(
            [f"**{i}.** {team['name']} ({team['member_count']}/4)" for i, team in enumerate(teams, start=1)]
        )
        embed = discord.Embed(title="Teams", description=description)

        await interaction.followup.send(embed=embed)

async def setup(bot: Bot) -> None:
    await bot.add_cog(Team(bot), guilds=[discord.Object(bot.config.bot.guild_id)])
