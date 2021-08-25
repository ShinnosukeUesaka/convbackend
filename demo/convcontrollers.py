from django.http import JsonResponse, HttpRequest, HttpResponseBadRequest, HttpResponse, HttpResponseForbidden
from django.core import serializers
import json

class ConvController:

   def __init__(self, conversation: Conversation):
        self.conversation = conversation
        self.scenario = conversation.scenario
        self.temp_data = json.loads(conversation.temp_for_conv_controller)

    def hello(self):
        print("hello")

    def chat(self, message: int) -> Tuple[JsonResponse, bool]:

        return JsonResponse({}), True

        #json.dumps(self.temp_data)
class QConvController(ConvController):
    pass
