import json
from typing import Dict

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from restless.models import serialize

from .models import Conversation, Scenario, Log, LogItem


def make_error(id_: str, msg: str) -> Dict:
    return {
        'type': id_,
        'msg': msg,
    }


def make_must_post() -> Dict:
    return make_error('error.typing.must_be_post', 'must be POST')


@csrf_exempt  # REST-like API anyway, who cares lol
def chat(request, conversation_id):
    if request.method == 'post':
        data = json.loads(request.body)
        conversation = Conversation.objects.get(pk=conversation_id)
        log = conversation.log
        scenario = conversation.scenario

        logitem_human = LogItem.objects.create(log=human, text=data['user_input'], name_text=scenario.human_name)
        logitem_human.save()

        log_text = prepare_log_text(conversation)
        response = gpt(log_text)

        logitem_ai = LogItem.objects.create(log=log, text=response, name_text=scenario.ai_name)
        logitem_ai.save()

        return JsonResponse({'response': serialize(logitem_ai)})
    return JsonResponse(make_must_post()), 400


@csrf_exempt  # REST-like API anyway, who cares lol
def conversations_view(request):
    if request.method == 'POST':
        # create new conversation
        data = json.loads(request.body)
        if not isinstance(data['scenario_id'], int):
            return JsonResponse({
                'type': 'error.typing',
                'msg': 'scenario_id must be integer',
            }), 400
        scenario = Scenario.objects.get(pk=data['scenario_id'])
        conversation = Conversation.objects.create(scenario=scenario)
        log = Log.objects.create(conversation=conversation)
        log_item = LogItem.objects.create(log=log, type=LogItem.Type.INITIAL_PROMPT, text=scenario.initial_prompt)
        conversation.save()
        log.save()
        log_item.save()
        return JsonResponse({'conversation_id': conversation.id, 'scenario_data': serialize(scenario)})
    return JsonResponse(make_must_post()), 400


def log_view(request, conversation_id):
    log_items = LogItem.objects.filter(log__conversation__id=conversation_id).filter(is_visible=True)
    return serialize(log_items)


def edit_log(request):
    return


class LogText(str): pass


# 以降 tools

def gpt(log_texts: LogText) -> str:
    return 'hi'


def gpt_check_coversation(conversation: Conversation) -> bool:
    return True


def prepare_log_text(conversation: LogItem) -> LogText:
    logtext = ""
    log_list = conversation.log.log_item.objects.all

    for log in log_list:
        logtype = log.type
        if logtype == LogItem.Type.AI or logtype == LogItem.Type.HUMAN:
            logtext += log.name_text + ": " + log.log_text + "\n"
        elif logtype == LogItem.Type.INITIAL_PROMPT or logtype == LogItem.Type.NARRATION:
            logtext += log.text + "\n"

    logtext += conversation.scenario_id.ai_name + ": "

    return LogText(logtext)
