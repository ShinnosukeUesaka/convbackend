from django.db import models

# Create your models here.
#https://www.webforefront.com/django/modeldatatypesandvalidation.html

class Scenario(models.Model):
    title = models.CharField(max_length=50)
    initial_prompt = models.CharField(max_length=200)
    ai_name = models.CharField(max_length=20)
    human_name = models.CharField(max_length=20)
    summarize_token = models.IntegerField()
    info = models.CharField(max_length=100)
    description = models.CharField(max_length=100)

    class Duration(models.IntegerChoices):
        #https://docs.djangoproject.com/en/3.0/ref/models/fields/#enumeration-types
        Five = 5, '5分'
        TEN = 0,'10分'
        TWENTY = 20,'20分'

    duration = models.IntegerField(choices=Duration.choices)

    class Level(models.IntegerChoices):
        #https://docs.djangoproject.com/en/3.0/ref/models/fields/#enumeration-types
        BEGINNER = 1,'初心者'
        INTERMEDIATE = 2,'中級者'
        ADVANCED = 3,'上級者'

    level = models.IntegerField(choices=Level.choices)

    def __str__(self):
        return self.title


class Option(models.Model):
    scenario = models.ForeignKey(Scenario, on_delete=models.CASCADE)

    name = models.CharField(max_length=20)

    def __str__(self):
        return self.name

class OptioinItem(models.Model):
    option = models.ForeignKey(Option, on_delete=models.CASCADE)

    name = models.CharField(max_length=20)

    def __str__(self):
        return self.name

class Conversation(models.Model):
    scenario = models.ForeignKey(Scenario, on_delete=models.CASCADE)

    def __str__(self):
        return self.scenario.title

class Log(models.Model):
    conversation = models.OneToOneField(Conversation, on_delete=models.CASCADE, primary_key=True)

    def __str__(self):
        return self.conversation.scenario.title

class LogItem(models.Model):
    log = models.ForeignKey(Log, on_delete=models.CASCADE)

    name_text = models.CharField(max_length=20)

    text = models.CharField(max_length=200)
    is_hidden = models.BooleanField()

    class Type(models.IntegerChoices):
        #https://docs.djangoproject.com/en/3.0/ref/models/fields/#enumeration-types
        INITIAL_PROMPT = 1
        NARRATION = 2
        AI = 3
        HUMAN = 4

    type = models.IntegerField(choices=Type.choices)

    def __str__(self):
        return self.text
