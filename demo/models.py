from typing import List, Union
import json
from django.db import models
# https://www.webforefront.com/django/modeldatatypesandvalidation.html
from demo.types import LogText


from django.core.exceptions import ValidationError


class Scenario(models.Model):

    class ScenarioManager(models.Manager):
        def get_by_natural_key(self, title):
            return self.get(title=title)

    objects = ScenarioManager()

    title = models.CharField(max_length=50, default='Title')
    title_en = models.CharField(max_length=50, default='English title')
    title_cs = models.CharField(max_length=50, default='Simplified Chinese title')
    title_ct = models.CharField(max_length=50, default='Traditional Chinese title')
    title_ko = models.CharField(max_length=50, default='Korean Title')
    title_vi = models.CharField(max_length=50, default='Vietnamese Title')
    title_es = models.CharField(max_length=50, default='Spanish Title')
    title_ru = models.CharField(max_length=50, default='Russian Title')



    duration = models.IntegerField(default='3') # Not implemented in the frontend
    # duration of the conversation in min

    level = models.IntegerField(default='2') # Not implemented in the frontend
    """
    1 初心者
    2 中級者
    3 上級者
    """

    information = models.CharField(max_length=1000, default='Japanese info')
    information_en = models.CharField(max_length=1000, default='English info')
    information_cs = models.CharField(max_length=1000, default='Traditional Chinese info')
    information_ct = models.CharField(max_length=1000, default='Simplified Chinese info')
    information_ko = models.CharField(max_length=1000, default='Korean info')
    information_vi = models.CharField(max_length=1000, default='Vietnamese info')
    information_es = models.CharField(max_length=1000, default='Spanish info')
    information_ru = models.CharField(max_length=1000, default='Russian info')

    phrases = models.TextField(max_length=10000, default="[]", blank=True, null=True)
    # [["I like you", "あなたが好き"], ["I hate you", "あなたが嫌い"]]

    article = models.TextField(max_length=10000, default='', blank=True, null=True) # only used for discussion question


    category = models.CharField(max_length=100, default='Role Play')

    controller_type = models.CharField(max_length=100, default='simple')


    ai_name = models.CharField(max_length=20, default='AI')
    human_name = models.CharField(max_length=20, default='Human')


    options = models.TextField(max_length=10000, default='{}')

    first_example_response = models.CharField(max_length=100, default='Unavailable')






    message_limit = models.IntegerField(default='10', blank=True, null=True)

    # GPT-3 Settings
    max_tokens = models.IntegerField(default=150)  # ai response length
    temperature = models.FloatField(default=0.5)
    top_p = models.FloatField(default=1)
    frequency_penalty = models.FloatField(default=0)
    presence_penalty = models.FloatField(default=0.6)



    voice = models.CharField(max_length=200, default="en-US_AllisonV2Voice")

    """
    class Voice(models.TextChoices):
        # https://docs.djangoproject.com/en/3.0/ref/models/fields/#enumeration-types
        JAMESV3 = "en-GB_JamesV3Voice"
        AllisonV2 = "en-US_AllisonV2Voice"
        HenryV3 = "en-US_HenryV3Voice"
        EmilyV3 = "en-US_EmilyV3Voice"
        AllisonV3 = "en-US_AllisonV3Voice"
        LisaV3 = "en-US_LisaV3Voice"
        MichaelV3 = "en-US_MichaelV3Voice"
        KateV3 = "en-GB_KateV3Voice"
        CharlotteV3 = "en-GB_CharlotteV3Voice"
        KevinV3 = "en-US_KevinV3Voice"
        MichaelV2= "en-US_MichaelV2Voice"
        LisaV2 = "en-US_LisaV2Voice"
        OliviaV3 = "en-US_OliviaV3Voice"
        Michael = "en-US_MichaelVoice"
        Kate = "en-GB_KateVoice"
        Lisa = "en-US_LisaVoice"
        Allison = "en-US_AllisonVoice"
        Craig = "en-AU_CraigVoice"
        Madison = "en-AU_MadisonVoice"

    voice = models.CharField(
        choices=Voice.choices,
        default=Voice.JAMESV3,
    )
    """





    def __str__(self) -> str:
        return self.title_en

    def to_dict(self) -> dict:
        return {
            'title': self.title,
            'initial_prompt': self.initial_prompt,
            'ai_name': self.ai_name,
            'human_name': self.human_name,
            'summarize_token': self.summarize_token,
            #'info': self.info,
            'description': self.description,
            'duration': self.duration,
            'level': self.level,
            'article': self.article
        }


class Conversation(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)

    active = models.BooleanField(default=True)
    scenario = models.ForeignKey(Scenario, on_delete=models.CASCADE)

    context_for_correction = models.BooleanField(default=True) # 英文修正の際に文脈判断を行うかどうか
    example_response = models.BooleanField(default=True) #回答例機能

    scenario_options = models.CharField(max_length=100) #　将来的には消す Json
    temp_for_conv_controller = models.TextField(blank=True, null=True, default="{}") #　キャッシュ Json





    def prepare(self) -> LogText: # shoudn't be used anymore
        logtext = ''
        for log_item in self.logitem_set.all():
            if log_item.send == True:
                logtext += str(log_item) + '\n'

        logtext += f'{self.scenario.ai_name}:'

        return LogText(logtext)

    def most_recent_logitem(self, log_number_from_recent = 1):
        return self.logitem_set.order_by('log_number').last()

    def recent_logitems(self, number_of_logitems):
        return self.logitem_set.all().order_by('log_number')[-number_of_logitems:]

    def current_log_number(self) -> int:
        if self.logitem_set.exists() == False:
            return 0
        else:
            return self.logitem_set.all().order_by('log_number').last().log_number




    def __str__(self) -> str:
        return self.scenario.title

    def create_json(self):
        # implement
        return



class LogItem(models.Model):

    created_at = models.DateTimeField(auto_now_add=True)

    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, blank=True, null=True)
    scenario_first = models.ForeignKey(Scenario, on_delete=models.CASCADE, blank=True, null=True, related_name = "first_logitems")
    scenario_last = models.ForeignKey(Scenario, on_delete=models.CASCADE, blank=True, null=True, related_name = "last_logitems")

    type = models.CharField(max_length=40)
    #Initial prompt ... AIに読み込ませるテキスト。基本的にAIに読み込ませる
    #Narration      ... ユーザーに表示するメッセージ。基本的にAIには読み込ませない。
    #AI             ... AIからのリスポンス
    #User           ... ユーザーが送ったメッセージ。

    # class Type(models.IntegerChoices):
    #     # https://docs.djangoproject.com/en/3.0/ref/models/fields/#enumeration-types
    #     INITIAL_PROMPT = 1
    #     NARRATION = 2
    #     AI = 3
    #     HUMAN = 4


    name = models.CharField(max_length=50, blank=True)
    text = models.CharField(max_length=1000) # メッセージの内容
    corrected_text = models.CharField(max_length=1000, blank=True, null=True) # 文法修正後のメッセージ
    visible = models.BooleanField(default=True)
    editable = models.BooleanField(default=True)
    send = models.BooleanField(default=True)
    include_name = models.BooleanField(default=True)

    log_number = models.IntegerField() # メッセージの順番を管理。 Minus number if it is not decided yet.
    safety = models.IntegerField(default=0) # メッセージに不適切な単語などが含まれているか
    # 0 safe 1 sensitive 2 unsafe

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['log_number', 'conversation'], name='Conversation contraint'),
            models.UniqueConstraint(fields=['log_number', 'scenario_first'], name='Scenario(first) contraint'),
            models.UniqueConstraint(fields=['log_number', 'scenario_last'], name='Scenario(last) contraint')
        ]
        ordering = ['log_number']
        get_latest_by = 'log_number'

    def __str__(self) -> str:
        if self.include_name == True:
            return f'{self.name}: {self.text}'
        else:
            return f'{self.text}'

class Coupon(models.Model):
    def validate_digit_length(code):
        if not (len(str(code)) == 4):
            raise ValidationError('must be 4 digits', params={'code': code},)

    code = models.IntegerField(validators=[validate_digit_length], unique=True)
    amount = models.IntegerField(default=100)
    used = models.BooleanField(default=False)
    recipient = models.CharField(null=True, blank=True, max_length=100)



class Session(models.Model):
    message = models.CharField(max_length=50, blank=True)
    # the first question
    example_response = models.CharField(max_length=1000)
    number_of_ai_response = models.IntegerField(default=2)
    # 2 Question, Comment
    # 3 Question, follow-up, Comment
    # 4 Question, follow-up, second follow-up, Comment
    allow_user_comment = models.BooleanField(default=True)
    # Make it true if you want to allow user to say something after AI comments at the end.
