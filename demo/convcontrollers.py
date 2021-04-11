from django.http import JsonResponse, HttpRequest, HttpResponseBadRequest, HttpResponse, HttpResponseForbidden


class ConvController:

   def __init__(self, conversation: Conversation):
        self.conversation = conversation
        self.scenario = conversation.scenario

    def hello(self):
        print("hello")

    def chat(self, message: int) -> Tuple[JsonResponse, bool]:

        return JsonResponse({}), True

    def action(self, action_number: int) -> HttpResponse:


class ConvController
