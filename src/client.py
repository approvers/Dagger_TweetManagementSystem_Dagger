import os
import asyncio

import discord

TOKEN = os.getenv("TOKEN")


class MainClient(discord.Client):
    def __init__(self):
        super().__init__()

    def run(self):
        super().run(TOKEN)

    async def on_ready(self):
        pass

    async def on_message(self, message: discord.Message):
        pass

    async def on_raw_reaction_add(self, payload):
        pass

    async def on_raw_reaction_remove(self, payload, user):
        pass

    async def on_raw_reaction_clear(self, payload):
        pass
