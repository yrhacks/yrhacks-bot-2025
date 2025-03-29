from __future__ import annotations

from supabase._async.client import AsyncClient as Client
from supabase import PostgrestAPIError
import discord

# from async_lru import alru_cache

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from utils.models import Registration, TeamRecord, TeamRecordWithCounts

    UserType = discord.Member | discord.User

class Database:
    def __init__(self, supabase: Client) -> None:
        self.supabase = supabase

    async def create_user_if_not_exists(self, registration: Registration, member: UserType) -> None:
        try:
            await self.supabase.table('users').insert({
                'discord_id': member.id,
                'school': registration['school'],
                'grade': registration['grade'],
            }).execute()
        except PostgrestAPIError as e:
            if "duplicate key value violates unique constraint" in str(e):
                # Do nothing if the discord_id already exists
                pass
            else:
                raise

    async def fetch_user_about(self, member: UserType) -> str | None:
        response = await self.supabase.table('users').select('about').eq('discord_id', member.id).execute()
        if not response.data:
            return None
        return response.data[0]['about']

    async def update_user_about(self, member: UserType, about: str) -> None:
        await self.supabase.table('users').update({'about': about}).eq('discord_id', member.id).execute()

    async def fetch_team_members(self, team_id: int) -> list[discord.Object]:
        response = await self.supabase.table('users').select('discord_id').eq('team_id', team_id).execute()
        return [discord.Object(id=member['discord_id']) for member in response.data]

    async def create_team(self, name: str, member: UserType) -> bool:
        try:
            response = await self.supabase.table('teams').insert({
                'name': name,
                'owner_id': member.id,
            }).execute()
        except PostgrestAPIError as e:
            # Likely, there is already a team with that name
            return False

        team_id = response.data[0]['id']
        await self.supabase.table('users').update({'team_id': team_id}).eq('discord_id', member.id).execute()
        return True

    # # TODO: Experiment with the ttl. The goal is so that the teams aren't repeatedly fetched while one user is *using the same slash command*.
    # @alru_cache(maxsize=32, ttl=7)
    async def fetch_teams(self, user: UserType) -> list[TeamRecordWithCounts]:
        response = await self.supabase.rpc("fetch_teams_with_counts").execute()
        return response.data if response.data else []

    async def fetch_team_by_member_id(self, team_member_id: int) -> TeamRecord | None:
        response = await self.supabase.table('users').select('team_id').eq('discord_id', team_member_id).execute()
        team_id = response.data[0]['team_id']
        if team_id is None:
            return None
        team_response = await self.supabase.table('teams').select('*').eq('id', team_id).execute()
        return team_response.data[0]

    async def fetch_team_by_id(self, team_id: int) -> TeamRecord:
        response = await self.supabase.table('teams').select('*').eq('id', team_id).execute()
        return response.data[0]

    async def fetch_team_invites_for_member(self, member: UserType) -> list[TeamRecord]:
        response = await self.supabase.rpc("fetch_pending_invites", {"member_id": member.id}).execute()
        return response.data if response.data else []

    async def rename_team(self, owner_id, new_name: str) -> list[TeamRecord]:
        response = await self.supabase.table('teams').update({'name': new_name}).eq('owner_id', owner_id).execute()
        return response.data

    async def invite_to_team(self, inviter: UserType, member: UserType) -> bool:
        await self.supabase.rpc("invite_user_to_team", {
            "inviter_id": inviter.id,
            "invitee_id": member.id
        }).execute()
        return True

    async def kick_from_team(self, user: UserType) -> None:
        await self.supabase.table('users').update({'team_id': None}).eq('discord_id', user.id).execute()

    async def leave_team(self, user: UserType) -> list[TeamRecord]:
        response = await self.supabase.table('users').update({'team_id': None}).eq('discord_id', user.id).execute()
        return response.data
    
    async def delete_team(self, owner: UserType) -> list[TeamRecord]:
        response = await self.supabase.table('teams').delete().eq('owner_id', owner.id).execute()
        return response.data

    async def accept_team_invite(self, user: UserType, team_id: int) -> None:
        await self.supabase.table('users').update({'team_id': team_id}).eq('discord_id', user.id).execute()
        await self.supabase.table('team_invites').update({'status': 'accepted'}).eq('team_id', team_id).eq('user_id', user.id).execute()
        # await self.supabase.table('team_invites').delete().eq('team_id', team_id).eq('user_id', member.id).execute()

    async def decline_team_invite(self, user: UserType, team_id: int) -> None:
        await self.supabase.table('team_invites').update({'status': 'declined'}).eq('team_id', team_id).eq('user_id', user.id).execute()
