"""
実際に投票やメッセージの管理を行う
メッセージ一つにつきインスタンス一つ
"""
import datetime
import re

import discord

VOTE_START_MESSAGE = """\
***† Twitter Judgement System †***
<@&711190816122470450> 各位
***{}***さんがツイートの可否の投票を開始しました！
OK! → <:AC:693007620159832124>
NG! → <:WA:693007620201775174>

***<† 本文 †>***
```
{} 
```
***<† 情報 †>***
```
Vote Started By:†{} ({})†
Content By:†{} ({})†  
```
"""

ORIGINAL_EMOJI_REGEX = re.compile(r'<.*:\d*>')


class MessageManager:
    def __init__(self, vote_starter_message: discord.Message, tweet_body_message: discord.Message = None):
        """
        投票の開始が必要なメッセージを検知した時につくられるインスタンス
        Parameters
        ----------
        vote_starter_message: discord.message
            該当のメッセージのオブジェクト
        """
        # 投票を開始した人のデータを保持する
        # billは英語で法案という意味です
        self.bill_msg: discord.message = vote_starter_message

        # 参照元のメッセージのデータを保持する
        # いまのところ!tw <id>コマンドが実装されていないため投票開始者と同じデータが入ってます
        # tweet_body_textは、非同期で処理しなきゃいけないので別に処理します
        self.tweet_body_msg: discord.message = vote_starter_message if tweet_body_message is None else tweet_body_message
        self.tweet_body_text: str = None

        # 実際の投票先のメッセージの情報を保持する
        # send_vote_start_messageで初期化
        self.vote_target_msg: discord.message = None

        # リストには賛成/反対者のIDが入る
        self.vote_result: dict[str:set[int]] = {"AC": set(), "WA": set()}

    async def announce_voting(self):
        # twitter-botチャンネル以外で投票が始まったときのための通知
        if self.bill_msg.channel != MessageManager.VOTE_CH:
            await self.bill_msg.channel.send("<@&711190816122470450>\n<#710877538309767211>で投票が開始されます！")

        self.tweet_body_text = await MessageManager.tweet_body_parser(self.tweet_body_msg,
                                                                      self.bill_msg.channel,
                                                                      self.bill_msg.author.id)

        s = VOTE_START_MESSAGE.format(self.bill_msg.author.display_name, self.tweet_body_text.replace("`", "'"),
                                      self.bill_msg.author.display_name, self.bill_msg.author.id,
                                      self.tweet_body_msg.author.display_name, self.tweet_body_msg.author.id)
        self.vote_target_msg = await MessageManager.VOTE_CH.send(s)

        # インスタンスを管理対象の辞書に代入
        MessageManager.MESSAGE_INSTANCES[self.vote_target_msg.id] = self

        # 押しやすくするために最初に自分でリアクションを押しておく
        await self.vote_target_msg.add_reaction(MessageManager.EMOJI_DICT["AC"])
        await self.vote_target_msg.add_reaction(MessageManager.EMOJI_DICT["WA"])

        # デバッグ表示
        print("投票が作成されました:")
        print(self.vote_target_msg.id)
        print("現在の投票の一覧:")
        print(list(MessageManager.MESSAGE_INSTANCES.keys()))

    @staticmethod
    async def tweet_body_parser(tweet_body_message: discord.message, respond_ch: discord.channel, bill_author_id: int):
        """
        Parameters
        ----------
        tweet_body_message: discord.message
            ツイート本文のメッセージのチャンネル
        respond_ch: discord.channel
            voteが始められたチャンネルのオブジェクト
        bill_author_id: int
            法案の提出者のID
        Returns
        ----------
        parsed_text: str
            実際に加工されたあとのテキスト
        """
        tmp = tweet_body_message.content

        # コマンドのprefixとその後の空白(全角/半角)を消す
        if "!tw　" in tmp:
            tmp = tmp.replace("!tw　", "", 1)
        if "!tw " in tmp:
            tmp = tmp.replace("!tw ", "", 1)

        # Discord絵文字が入っている場合に警告して、更に取り除く
        if len(re.findall(ORIGINAL_EMOJI_REGEX, tmp)) >= 1:
            s = "<@!{}>\nDiscord emoji が入っています！\n絵文字は無視されます！".format(bill_author_id)
            await respond_ch.send(s)
            tmp = re.sub(ORIGINAL_EMOJI_REGEX, "", tmp)

        parsed_text = tmp

        return parsed_text

    async def status_changer(self, reaction_member: discord.member, emoji_type: str, status: str):
        """
        ステータスを変更するための関数
        Parameters
        ----------
        reaction_member: discord.member
            リアクションを行ったメンバーのオブジェクト
        emoji_type: str
            その絵文字がACなのかWAなのかが格納されている
        status: str
            Reactionがadd,rem,clrのいずれかが格納される
        """
        if status == "add":
            member_id = reaction_member.id
            # つけられた絵文字のほうじゃない絵文字が格納される
            complement_emoji = "AC" if emoji_type == "WA" else "WA"
            if member_id in self.vote_result[complement_emoji]:
                await self.vote_target_msg.remove_reaction(MessageManager.EMOJI_DICT[complement_emoji], reaction_member)
            self.vote_result[emoji_type].add(member_id)

        if status == "rem":
            member_id = reaction_member.id
            self.vote_result[emoji_type].remove(member_id)

        if status == "clr":
            await MessageManager.VOTE_CH.send("クリアすんなカス！！！！㊙すぞ！！！")
            self.vote_result = {"AC": set(), "WA": set()}

        print("現在の投票状況：")
        print(self.vote_result)

    @staticmethod
    async def status_changer_wrapper(status: str, message_id: int, member: discord.member = None, emoji_type: str = None):
        """
        ステータスを変更するための関数
        Parameters
        ----------
        message_id: int
            ステータスが変更されたメッセージのID
        member: discord.member
            リアクションを行ったメンバーのオブジェクト
        emoji_type: str
            その絵文字がACなのかWAなのかが格納されている
        status: str
            Reactionがadd,rem,clrのいずれかが格納される

        """
        o = MessageManager.MESSAGE_INSTANCES[message_id]
        await o.status_changer(member, emoji_type, status)

    @staticmethod
    def static_init(
            twitter_vote_ch_obj: discord.TextChannel, 
            citizen_list: list[discord.Member], 
            emoji_dict: dict[str:discord.Emoji]
    ):
        """
        s   t   a   t   i   c   オ   ヂ   サ   ン
        Parameters
        ----------
        twitter_vote_ch_obj: discord.TextChannel
            投票チャンネルのオブジェクト
        citizen_list: list[discord.member]オブジェクト
            参政権を持ったユーザーのリストが格納されている
        emoji_dict: dict{str:discord.emoji}
            ACとWAのemoji
        """
        MessageManager.MESSAGE_INSTANCES = {}
        MessageManager.VOTE_CH = twitter_vote_ch_obj
        MessageManager.CITIZEN_LIST = citizen_list
        MessageManager.CITIZEN_ID_LIST = list(map((lambda x: x.id), citizen_list))
        MessageManager.EMOJI_DICT = emoji_dict

        # デバッグ表示
        print("市民権IDリストを取得しました:")
        print(MessageManager.CITIZEN_ID_LIST)

        MessageManager.AC_EMOJI = emoji_dict["AC"]
        MessageManager.WA_EMOJI = emoji_dict["WA"]

        # デバッグ表示
        print("MessageManagerの初期化が完了しました")
