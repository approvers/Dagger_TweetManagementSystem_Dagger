"""
　　　　　　　　　　　　　/　iiii　i　ヽ､､
　　　　　　　　　　　 ／ゞ、i!llllliｉｉ川//ヽ、
　　　　　　　　　　 /ミ〃　　　　　　〃彡ヽ
　　　　　　　　　　lミミ　　　　　　　　彡彡｝
　　　　　　　　　　lミﾐ,ｒ‐-､　,,ｒ─､　彡彡ll|
　　　　　　　　　　ｉﾐﾐ ｨｪx　　 ,rｪt　　彳彡!
　　　　　　　　　　　',　　 .:　　　　　 　9｝"
　　　　　　　　　　 　! 　 ::,､,､　　　　l_丿
　　　　　　　　　　　 ',　 ＿,＿　　　/、
　　　　　　　　　　　 rゝ　 =　　　ノi!ヽﾄ、
　　　　　　　　　　-｛;ヽ` ー─ "　／;/: : ＼
　　　　　　　　／: : : |;;;＼ 　 　 ／;;;;/: : :/: :＼
　　　　　　／: : : : : :│;;;;;;＼／;;;;;;;;/: : :/: : : : :＼
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
        twitter_vote_ch: int
            実際に投票を行うチャンネルのid
        citizen_permission_id: int
            参政権のID
        """
        super(MainClient, self).__init__()
        self.token = token
        self.twitter_vote_ch_id = twitter_vote_ch_id
        self.citizen_permission_id = citizen_permission_id

    def launch(self):
        """
        clientの起動
        """
        self.run(self.token)

    async def on_ready(self):
        """
        Clientの情報をもとにした初期化
        """
        if (MainClient.__ready):
            return
        MainClient.__ready = True

        if len(self.guilds) > 1:
            try:
                raise Exception
            except:
                traceback.print_exc()

        self.guild = self.guilds[0]

        self.citizen_permission_obj = self.guild.get_role(self.citizen_permission_id)
        self.twitter_vote_ch_obj = self.guild.get_channel(self.twitter_vote_ch_id)

        self.citizen_members = self.citizen_permission_obj.members

        MessageManager.static_init(self.twitter_vote_ch_obj)



    # 以下イベントを処理するためのアレ

    async def on_message(self, message: discord.Message):
        """
        BOT以外がメッセージを送信したときに関数に処理をさせる
        Parameters
        ----------
        message: discord.Message
            受け取ったメッセージのデータ
        """
        if message.author.bot:
            return
        if message.content.lower().startswith("!tw"):
            m = MessageManager(message)
            await m.message_sender()


    async def on_message_edit(self, before, after):
        # TODO:該当のメッセージが編集された場合の処理は必至
        pass

    async def on_message_delete(self, message: discord.Message):
        # TODO:上に同じ
        pass

    async def on_reaction_add(reaction, user):
        pass


if __name__ == "__main__":
    TOKEN = os.environ["TOKEN"]
    MAIN = MainClient(TOKEN, citizen_permission_id=710876430073856000, twitter_vote_ch_id=710877538309767211)
    MAIN.launch()