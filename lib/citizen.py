"""
市民権をもったユーザーを保持するためのクラス
"""
import asyncio

import discord

from lib.util import Singleton

class CitizensHolder(Singleton):
    def __init__(self, citizen_permission_obj: discord.role):
        """
        Parameters
        ----------
        citizen_permission_obj: discord.role
            参政権のロールオブジェクト
        """
        CITIZEN_OBJECT = citizen_permission_obj
        CITIZEN_MEMBERS = citizen_permission_obj.members

    @classmethod
    def static_init(cls):