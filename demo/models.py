from typing import List, Union
import json
from django.db import models
# https://www.webforefront.com/django/modeldatatypesandvalidation.html
from demo.types import LogText


class Scenario(models.Model):

    class ScenarioManager(models.Manager):
        def get_by_natural_key(self, title):
            return self.get(title=title)

    objects = ScenarioManager()

    title = models.CharField(max_length=50, default='Title')
    title_en = models.CharField(max_length=50, default='English_title')
    # scenario description
    duration = models.IntegerField()
    # duration of the conversation in min
    level = models.IntegerField()
    """
    1 初心者
    2 中級者
    3 上級者
    """

    information = models.CharField(max_length=1000, default='')
    information_en = models.CharField(max_length=1000, default='')

    category = models.CharField(max_length=100, default='Roll Play')
    """
        Exercise: エクササイズ
        Chat: 雑談
        Discussion: ディスカッション
        Roll Play: ロールプレイ
    """

    controller_type = models.CharField(max_length=100, default='simple')
    """
    simple: default controlleer
    q_exercise: question exercise controller
    """

    controller_variables = models.CharField(max_length=1000)
    # json that contain variables used in the controllers(not implemented)

    # Initial prompt, similar to narration:
    # The following is a conversation of two {poeple}  talking about {Proper noun}, {category}. They {feeling} {Proper noun}.
    ai_name = models.CharField(max_length=20, default='AI')
    human_name = models.CharField(max_length=20, default='Human')
    info = models.CharField(max_length=100, default='')
    # info about scenario:
    # place: cafe, mission: buy coffee

    options = models.CharField(max_length=200, default='{}') # Not used
    # JSON (not dict converted to str) of options:
    # {"people": ["highschool studnets", "university students", "adults"], "feeling": ["like", "hate"] ...}

    # GPT-3 Settings
    response_length = models.IntegerField(default=150)  # ai response length
    temperature = models.DecimalField(max_digits=4, decimal_places=3, default=0.4)
    top_p = models.DecimalField(max_digits=4, decimal_places=3, default=1)
    frequency_penalty = models.DecimalField(max_digits=4, decimal_places=3, default=0.5)
    presence_penalty = models.DecimalField(max_digits=4, decimal_places=3, default=0)

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
        return self.title

    def to_dict(self) -> dict:
        return {
            'title': self.title,
            'initial_prompt': self.initial_prompt,
            'ai_name': self.ai_name,
            'human_name': self.human_name,
            'summarize_token': self.summarize_token,
            'info': self.info,
            'description': self.description,
            'response_length': self.response_length,
            'temperature': self.temperature,
            'top_p': self.top_p,
            'frequency_penalty': self.frequency_penalty,
            'presence_penalty': self.presence_penalty,
            'duration': self.duration,
            'level': self.level,
        }


class Conversation(models.Model):
    scenario = models.ForeignKey(Scenario, on_delete=models.CASCADE)
    scenario_options = models.CharField(max_length=100)
    active = models.BooleanField(default=True)
    temp_for_conv_controller = models.TextField(blank=True, null=True, default="{}")
    created_at = models.DateTimeField(auto_now_add=True)

    def prepare(self) -> LogText:
        logtext = ''
        for log_item in self.logitem_set.all():
            if log_item.send == True:
                logtext += str(log_item) + '\n'

        logtext += f'{self.scenario.ai_name}:'

        return LogText(logtext)

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
    # class Type(models.IntegerChoices):
    #     # https://docs.djangoproject.com/en/3.0/ref/models/fields/#enumeration-types
    #     INITIAL_PROMPT = 1
    #     NARRATION = 2
    #     AI = 3
    #     HUMAN = 4
    created_at = models.DateTimeField(auto_now_add=True)

    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, blank=True, null=True)
    scenario = models.ForeignKey(Scenario, on_delete=models.CASCADE, blank=True, null=True)

    type = models.CharField(max_length=40)
    #Initial prompt
    #Narration
    #AI
    #User
    name = models.CharField(max_length=50, blank=True)
    text = models.CharField(max_length=1000)
    visible = models.BooleanField(default=True)
    editable = models.BooleanField(default=True)
    send = models.BooleanField(default=True)
    include_name = models.BooleanField(default=True)

    log_number = models.IntegerField()
    safety = models.IntegerField(default=0)
    # 0 safe 1 sensitive 2 unsafe

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['log_number', 'conversation'], name='Conversation contraint'),
            models.UniqueConstraint(fields=['log_number', 'scenario'], name='Scenario contraint')
        ]

    def __str__(self) -> str:
        if self.include_name == True:
            return f'{self.name}: {self.text}'
        else:
            return f'{self.text}'
