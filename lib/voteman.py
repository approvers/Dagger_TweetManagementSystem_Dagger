"""
実際に投票やメッセージの管理を行う
メッセージ一つにつきインスタンス一つ
"""
from lib.util import Singleton
import datetime

import discord

VOTE_START_MESSAGE = """\
***† Twitter Judgement System †***
***{}***さんがツイートの可否の投票を開始しました！
OK! → <:AC:693007620159832124>
NG! → <:WA:693007620201775174>
わからん → <:WJ:693262811958083684>

***<† 本文 †>***
```
{}
```
***<† 情報 †>***
```
Vote Started By:†{} ({})†, Content By:†{} ({})†  
```
<@&710876430073856000> 各位
"""


class MessageManager(Singleton):
    def __init__(self, message: discord.message):
        """
        投票の開始が必要なメッセージを検知した時につくられるインスタンス
        Parameters
        ----------
        message: discord.message
            該当のメッセージのオブジェクト
        """
        self.message = message
        self.author = message.author

        self.vote_starter_name = message.author.display_name
        self.vote_starter_id = message.author.id

        # idでツイートする機能が実装されるときのための予備の変数
        self.tweet_body_author_name = message.author.display_name
        self.tweet_body_author_id = message.author.id

        self.created_time = datetime.datetime.now()

        self.command_msg_id = message.id
        self.source_meg_id = message.id

        self.vote_msg_id = None

        if "!tw　" in message.content:
            self.tweet_body = message.content.replace("!tw　", "", 1)
        if "!tw " in message.content:
            self.tweet_body = message.content.replace("!tw ", "", 1)

        self.voted_member_id = set()
        self.vote_result = {"AC":0, "WA":0}

        print(message.id)

    async def send_vote_start_message(self):
        if not self.message.channel.id == 710877538309767211:
            await self.message.channel.send("<@&710876430073856000>\n<#710877538309767211>で投票が開始されました！")
        s = VOTE_START_MESSAGE.format(self.vote_starter_name, self.tweet_body,
                                      self.vote_starter_name, self.vote_starter_id,
                                      self.tweet_body_author_name, self.tweet_body_author_id)
        self.vote_msg_obj = await MessageManager.VOTE_CH.send(s)
        self.vote_msg_id =self.vote_msg_obj.id
        MessageManager.MESSAGE_INSTANCES[self.vote_msg_id] = self
        print(MessageManager.MESSAGE_INSTANCES)  # デバッグ表示

    @staticmethod
    async def status_changer(message_id: int, member_id: int, emoji_type: str, status: str):
        """
        ステータスを変更するための関数
        Parameters
        ----------
        message_id: int
            ステータスが変更されたメッセージのID
        member_id: int
            リアクションの変更を行ったユーザーのID
        emoji_type: str
            その絵文字がACなのかWAなのかが格納されている
        status: str
            Reactionがadd,rem,clrのいずれかが格納される

        """
        if not member_id in MessageManager.CITIZEN_ID_LIST:
            return
        #try:
        #    manager_instance = MessageManager.MESSAGE_INSTANCES[message_id]
        #except ValueError:
        #    print("No message match")
        #except Exception as e:
        #    await MessageManager.VOTE_CH.send("不明な例外が発生しました\n内容は{}です".format(e))

        manager_instance = MessageManager.MESSAGE_INSTANCES[message_id]

        if status == "add":
            if emoji_type == "AC":
                manager_instance.voted_member_id.add(member_id)
                manager_instance.vote_result[emoji_type] += 1
                await MessageManager.VOTE_CH.send(manager_instance.voted_member_id)
                await MessageManager.VOTE_CH.send(manager_instance.vote_result)
                return
            manager_instance.voted_member_id.add(member_id)
            manager_instance.vote_result[emoji_type] += 1
            await MessageManager.VOTE_CH.send(manager_instance.voted_member_id)
            await MessageManager.VOTE_CH.send(manager_instance.vote_result)
        if status == "rem":
            if emoji_type == "AC":
                manager_instance.voted_member_id.add(member_id)
                manager_instance.vote_result[emoji_type] -= 1
                await MessageManager.VOTE_CH.send(manager_instance.voted_member_id)
                await MessageManager.VOTE_CH.send(manager_instance.vote_result)
                return
            manager_instance.voted_member_id.add(member_id)
            manager_instance.vote_result[emoji_type] -= 1
            await MessageManager.VOTE_CH.send(manager_instance.voted_member_id)
            await MessageManager.VOTE_CH.send(manager_instance.vote_result)
        if status == "clr":
            manager_instance.voted_member_id = set()
            manager_instance.vote_result = {"AC":0, "WA":0}
            await MessageManager.VOTE_CH.send(manager_instance.voted_member_id)
            await MessageManager.VOTE_CH.send(manager_instance.vote_result)
            return

    @staticmethod
    def static_init(twitter_vote_ch_obj: discord.TextChannel, citizen_list):
        """
        s   t   a   t   i   c   オ   ヂ   サ   ン
        Parameters
        ----------
        twitter_vote_ch_obj: discord.TextChannel
            投票チャンネルのオブジェクト
        CITIZEN_ID_LIST: list[discord.member]
        """
        MessageManager.MESSAGE_INSTANCES = {}
        MessageManager.VOTE_CH = twitter_vote_ch_obj
        MessageManager.CITIZEN_LIST = citizen_list
        MessageManager.CITIZEN_ID_LIST = list(map((lambda x: x.id), citizen_list))
        print(MessageManager.CITIZEN_ID_LIST)
