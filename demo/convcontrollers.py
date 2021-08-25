from django.http import JsonResponse, HttpRequest, HttpResponseBadRequest, HttpResponse, HttpResponseForbidden
from django.core import serializers
from .models import Conversation, Scenario, LogItem
from . import gpt3
from .gpt3 import completion, content_filter_profanity, ContentSafetyPresets
import json
from restless.models import serialize

class ConvController:

   def __init__(self, conversation: Conversation):
        self.conversation = conversation
        self.scenario = conversation.scenario
        #self.temp_data = json.loads(conversation.temp_for_conv_controller)

   def chat(self, message):
        current_log_number = self.conversation.current_log_number()
        logitem_human = LogItem.objects.create(text=message, name=self.scenario.human_name, type="User",
                                               log_number=current_log_number + 1, conversation=self.conversation)
        logitem_human.save()
        self.conversation.save()

        log_text = self.conversation.prepare()
        response, safety = self.create_response(log_text=log_text)

        print(f'response: {response}')
        logitem_ai = LogItem.objects.create(text=response, name=self.scenario.ai_name, type="AI",
                                            log_number=current_log_number + 2, conversation=self.conversation, safety=safety)

        logitem_ai.save()

        return serialize(logitem_ai)

   def create_response(self, log_text, retry: int = 3, allow_max: int = 0) -> str:
        print(f"gpt3 request: {log_text}")
        re = completion(prompt_=log_text)
        safety = int(gpt3.content_filter(re))
        ok = safety <= allow_max
        if not ok and retry <= 0:
            # return f'The AI response included content deemed as sensitive or unsafe, so it was hidden.\n{re}'
            return re, safety
        if not ok:
            return gpt(log_text, retry - 1)
        return re, safety


        #json.dumps(self.temp_data)
class QConvController(ConvController):
    pass
