from typing import List

from django.db import models

# Create your models here.
# https://www.webforefront.com/django/modeldatatypesandvalidation.html
from demo.types import LogText


class Scenario(models.Model):
    title = models.CharField(max_length=50)
    initial_prompt = models.CharField(max_length=200) # The following is a conversation of two {poeple}  talking about {Proper noun}, {category}. They {feeling} {Proper noun}.
    ai_name = models.CharField(max_length=20)
    human_name = models.CharField(max_length=20)
    summarize_token = models.IntegerField()
    info = models.CharField(max_length=100)  # eg place: cafe, mission: buy coffee
    description = models.CharField(max_length=100)  # scenario description
    options = models.CharField(max_length=200) #dictionaryをstring(json) にconvertして保存。 Ex) {people: ['highschool studnets', 'university students', 'adults'], feeling: ['like', 'hate'] ......}

    # GPT-3 Settings
    response_length = models.IntegerField(default=150)  # ai response length
    temperature = models.DecimalField(max_digits=4, decimal_places=3, default=0.9)
    top_p = models.DecimalField(max_digits=4, decimal_places=3, default=1)
    frequency_penalty = models.DecimalField(max_digits=4, decimal_places=3, default=0)
    presence_penalty = models.DecimalField(max_digits=4, decimal_places=3, default=0.6)

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

    class Duration(models.IntegerChoices):
        # https://docs.djangoproject.com/en/3.0/ref/models/fields/#enumeration-types
        FIVE = 5, '5分'
        TEN = 0, '10分'
        TWENTY = 20, '20分'

    duration = models.IntegerField(choices=Duration.choices)

    class Level(models.IntegerChoices):
        # https://docs.djangoproject.com/en/3.0/ref/models/fields/#enumeration-types
        BEGINNER = 1, '初心者'
        INTERMEDIATE = 2, '中級者'
        ADVANCED = 3, '上級者'

    level = models.IntegerField(choices=Level.choices)

    def __str__(self):
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

    def prepare(self):
        logtext = ''
        for log_item in self.logitem_set.all():
            logtext += str(log_item) + '\n'

        logtext += f'{self.scenario.ai_name}: '

        return LogText(logtext)

    def current_log_number(self):
         return self.logitem_set.all().order_by('log_number').last().log_number

    def __str__(self):
        return self.scenario.title





class LogItem(models.Model):
    class Type(models.IntegerChoices):
        # https://docs.djangoproject.com/en/3.0/ref/models/fields/#enumeration-types
        INITIAL_PROMPT = 1
        NARRATION = 2
        AI = 3
        HUMAN = 4

    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE)

    name = models.CharField(max_length=20)
    text = models.CharField(max_length=200)
    visible = models.BooleanField(default=True)
    editable = models.BooleanField(default=True)
    type = models.IntegerField(choices=Type.choices)
    log_number = models.IntegerField()

    def __str__(self) -> str:
        if self.type in (LogItem.Type.AI, LogItem.Type.HUMAN):
            return f'{self.name}: {self.text}'
        elif self.type in (LogItem.Type.INITIAL_PROMPT, LogItem.Type.NARRATION):
            return f'{self.text}'
