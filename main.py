"""
地味に作るのめんどくさかったです、はい
"""
import asyncio
import os
import traceback

import discord

from lib.util import Singleton
from lib.voteman import MessageManager


class MainClient(discord.Client, Singleton):
    """
    Discordクライアント(多重起動防止機構付き)
    """

    __ready = False

    def __init__(self, token: str, citizen_permission_id: int, twitter_vote_ch_id: int):
        """
        クライアントを起動する前の処理
        Parameters
        ----------
        token: str
            discordのBotのトークン
        twitter_vote_ch_id: int
            実際に投票を行うチャンネルのid
        citizen_permission_id: int
            参政権のID
        """
        super(MainClient, self).__init__()
        self.token = token

        self.twitter_vote_ch_id = twitter_vote_ch_id
        self.citizen_permission_id = citizen_permission_id

        self.emoji_id_dict = {693007620159832124: "AC", 693007620201775174: "WA"}

    async def on_ready(self):
        """
        Clientの情報をもとにした初期化
        """
        if (MainClient.__ready):
            return

        MainClient.__ready = True

        # ギルドチェック
        if len(self.guilds) > 1:
            pass
            # TODO ここに複数のギルドにbotが属している場合の処理
        if not self.guilds[0].id == 683939861539192860:
            pass
            # TODO ここにギルドが限界開発鯖ではない場合の処理

        self.guild = self.guilds[0]

        self.citizen_permission_obj = self.guild.get_role(self.citizen_permission_id)
        self.vote_ch_obj = self.guild.get_channel(self.twitter_vote_ch_id)

        self.citizen_list = self.citizen_permission_obj.members
        self.citizen_id_list = list(map((lambda x: x.id), self.citizen_list))

        self.emoji_dict = {"AC":self.get_emoji(693007620159832124), "WA":self.get_emoji(693007620201775174)}

        MessageManager.static_init(self.vote_ch_obj, self.citizen_list, self.emoji_dict)

    def launch(self):
        """
        clientの起動
        """
        self.run(self.token)

    async def on_message(self, message: discord.Message):
        """
        BOT以外がメッセージを送信したときに関数に処理をさせる
        Parameters
        ----------
        message: discord.Message
            受け取ったメッセージのデータ
        """
        if message.content.startswith("!tw") and not message.author.bot:
            tmp = MessageManager(message)
            await tmp.send_vote_start_message()
            return
        if message.channel.id == MessageManager.VOTE_CH.id and not message.author.id == self.user.id:
            await message.delete(delay=None)

    async def on_message_edit(self, before, after):
        pass
        # TODO:該当のメッセージが編集された場合の処理は必至

    async def on_message_delete(self, message: discord.Message):
        # TODO:上に同じ
        pass

    async def on_raw_reaction_add(self, payload):
        emoji = payload.emoji
        polling_station_ids = MessageManager.MESSAGE_INSTANCES.keys()

        # そもそも、リアクションをつけたメッセージが管理対象ではない場合
        if not payload.message_id in polling_station_ids:
            return

        target_message = MessageManager.MESSAGE_INSTANCES[payload.message_id].polling_station_message

        # リアクションをつけたユーザーに参政権がない(なおかつ発言者はこのbotでない)場合
        if not payload.user_id in self.citizen_id_list and not payload.user_id == self.user.id:
            await target_message.remove_reaction(payload.emoji, self.guild.get_member(payload.member.id))
            return

        # リアクションをつけたユーザーがbotであるとき
        if payload.user_id == self.user.id:
            return

        # つけられたリアクションがAC、WA以外の場合
        if not emoji.id in self.emoji_id_dict.keys():
            await target_message.remove_reaction(payload.emoji, self.guild.get_member(payload.member.id))
            return

        await MessageManager.status_changer(payload.message_id, payload.user_id, self.emoji_id_dict[payload.emoji.id], "add")


    async def on_raw_reaction_remove(self, payload):
        emoji = payload.emoji
        polling_station_ids = MessageManager.MESSAGE_INSTANCES.keys()

        # リアクションを消されたメッセージが管理対象ではない場合
        if not payload.message_id in polling_station_ids:
            return

        # 消されたリアクションがAC、WA以外の場合
        if not emoji.id in self.emoji_id_dict.keys():
            return

        await MessageManager.status_changer(payload.message_id, payload.user_id, self.emoji_id_dict[payload.emoji.id], "rem")


    async def on_raw_reaction_clear(self, payload):
        polling_station_ids = MessageManager.MESSAGE_INSTANCES.keys()

        # そもそも、リアクションをクリアされたメッセージが管理対象ではない場合
        if not payload.message_id in polling_station_ids:
            return

        await MessageManager.status_changer(payload.message_id, payload.user_id, self.emoji_id_dict[payload.emoji.id], "clr")

if __name__ == "__main__":
    TOKEN = os.environ["TOKEN"]

    # デバッグ表示
    print("起動しています...")

    MAIN = MainClient(TOKEN, citizen_permission_id=711190816122470450, twitter_vote_ch_id=710877538309767211)
    MAIN.launch()
