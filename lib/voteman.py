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
    def __init__(self, vote_starter_message: discord.message):
        """
        投票の開始が必要なメッセージを検知した時につくられるインスタンス
        Parameters
        ----------
        message: discord.message
            該当のメッセージのオブジェクト
        """
        # 投票を開始した人のデータを保持する
        self.vote_starter_message = vote_starter_message
        self.vote_starter_member = vote_starter_message.author
        self.vote_starter_name = vote_starter_message.author.display_name
        self.vote_starter_dateime = datetime.datetime.now()

        # 参照元のメッセージのデータを保持する
        # いまのところ!tw <id>コマンドが実装されていないため投票開始者と同じデータが入ってます
        # tweet_body_textは警告文を送信する関係上、非同期で処理しなきゃいけないので別に処理します
        self.tweet_body_message = vote_starter_message
        self.tweet_body_member = vote_starter_message.author
        self.tweet_body_name = vote_starter_message.author.display_name
        self.tweet_body_text = None

        # 実際の投票先のメッセージの情報を保持する
        # send_vote_start_messageで初期化
        self.polling_station_message = None
        self.polling_station_message_id = None

        # 実際の投票関連のデータ
        # リストには賛成/反対者のIDが入る
        self.voted_citizen_ids = set()
        self.vote_result = {"AC": [], "WA": []}

    async def send_vote_start_message(self):
        self.tweet_body_text = await MessageManager.tweet_body_parser(self.tweet_body_message,
                                                                      self.vote_starter_message.channel,
                                                                      self.vote_starter_member.id)

        # twitter-botチャンネル以外で投票が始まったときのための通知
        if not self.vote_starter_message.channel.id == MessageManager.VOTE_CH.id:
            await self.vote_starter_message.channel.send("<@&711190816122470450>\n<#710877538309767211>で投票が開始されました！")

        s = VOTE_START_MESSAGE.format(self.vote_starter_name, self.tweet_body_text.replace("`", "'"),
                                      self.vote_starter_name, self.vote_starter_member.id,
                                      self.tweet_body_name, self.tweet_body_member.id)
        self.polling_station_message = await MessageManager.VOTE_CH.send(s)
        self.polling_station_message_id = self.polling_station_message.id

        # インスタンスを管理対象の辞書に代入
        MessageManager.MESSAGE_INSTANCES[self.polling_station_message_id] = self

        # 押しやすくするために最初に自分でリアクションを押しておく
        await self.polling_station_message.add_reaction(MessageManager.EMOJI_DICT["AC"])
        await self.polling_station_message.add_reaction(MessageManager.EMOJI_DICT["WA"])

        # デバッグ表示
        print("投票が作成されました:")
        print(self.polling_station_message_id)
        print("現在の投票の一覧:")
        print(list(MessageManager.MESSAGE_INSTANCES.keys()))

    @staticmethod
    async def tweet_body_parser(tweet_body_message: discord.message, respond_ch: discord.channel, vote_starter_id: int):
        """
        Parameters
        ----------
        tweet_body_message: discord.message
            ツイート本文のメッセージのチャンネル
        respond_ch: discord.channel
            voteが始められたチャンネルのオブジェクト
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
            s = "<@!{}>\nDiscord emoji が入っています！\n絵文字は無視されます！".format(vote_starter_id)
            await respond_ch.send(s)
            tmp = re.sub(ORIGINAL_EMOJI_REGEX, "", tmp)

        parsed_text = tmp

        return parsed_text

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
        print("ステータスチェンジを感知したわよ！")
        print(message_id, member_id, emoji_type, status)


    @staticmethod
    def static_init(twitter_vote_ch_obj: discord.TextChannel, citizen_list, emoji_dict: dict):
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
        print("MessageManagerの初期化が完了しました")
