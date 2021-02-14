import json
from typing import Dict, Tuple

from django.http import JsonResponse, HttpRequest, HttpResponseBadRequest, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from restless.models import serialize

from . import gpt3
from .models import Conversation, Scenario, LogItem
from .gpt3 import completion
from .types import LogText


def make_error(id_: str, msg: str, **kwargs) -> Dict:
    return {
        'type': id_,
        'msg': msg,
        **kwargs,
    }


def make_must_post() -> JsonResponse:
    return JsonResponse(make_error('error.http.must_be_post', 'must be POST'))


def assert_keys(data: Dict, keys: Dict[str, type]) -> Tuple[JsonResponse, bool]:
    for key, type_ in keys.items():
        scope = data
        for keyin in key.split('.'):
            if not isinstance(scope, Dict):
                return JsonResponse(make_error('error.body.typing', f'must be all dicts until the last {key}')), False
            if keyin in scope:
                scope = scope[keyin]
            else:
                return JsonResponse(make_error('error.body.key', f'must have {key}')), False
        if not isinstance(scope, type_):
            return JsonResponse(make_error('error.body.typing', f'must be {type_}, not {type(scope)}')), False
    return JsonResponse({}), True


@csrf_exempt  # REST-like API anyway, who cares lol
def chat(request: HttpRequest) -> HttpResponse:
    if not request.method == 'POST':
        return HttpResponseBadRequest(make_must_post())
    data = json.loads(request.body)
    err, ok = assert_keys(data, {
        'conversation_id': int,
        'user_input': str,
    })
    if not ok:
        return HttpResponseBadRequest(err)

    conv: Conversation = Conversation()
    if data['conversation_id'] == -1:
        conv = Conversation.objects.create(scenario=Scenario.objects.get(pk=1))  # for testing
    else:
        conv = Conversation.objects.get(pk=data['conversation_id'])
    scenario = conv.scenario

    logitem_human = LogItem.objects.create(text=data['user_input'], name=scenario.human_name, type=LogItem.Type.HUMAN)
    conv.log_items.add(logitem_human)
    logitem_human.save()
    conv.save()

    log_text = conv.prepare()
    response = gpt(log_text)

    raise RuntimeError(response)
    logitem_ai = LogItem.objects.create(text=response, name=scenario.ai_name, type=LogItem.Type.AI)
    conv.log_items.add(logitem_ai)
    logitem_ai.save()
    conv.save()

    return JsonResponse({'response': serialize(logitem_ai)})


@csrf_exempt  # REST-like API anyway, who cares lol
def conversations_view(request: HttpRequest) -> HttpResponse:
    if not request.method == 'POST':
        return HttpResponseBadRequest(make_must_post())
    # create new conversation
    data = json.loads(request.body)
    err, ok = assert_keys(data, {
        'conversation_id': int,
        'scenario_id': int,
    })
    if not ok:
        return HttpResponseBadRequest(err)
    scenario = Scenario.objects.get(pk=data['scenario_id'])
    conversation = Conversation.objects.create(
        scenario=scenario,
    )
    conversation.log_items.set([LogItem.objects.create(type=LogItem.Type.INITIAL_PROMPT, text=scenario.initial_prompt)])
    conversation.save()
    conversation.log_items.all()[0].save()
    return JsonResponse({'conversation_id': conversation.id, 'scenario_data': serialize(scenario)})


@csrf_exempt  # REST-like API anyway, who cares lol
def log_view(request: HttpRequest) -> HttpResponse:
    if not request.method == 'POST':
        return HttpResponseBadRequest(make_must_post())
    data = json.loads(request.body)
    err, ok = assert_keys(data, {
        'conversation_id': int,
    })
    if not ok:
        return HttpResponseBadRequest(err)
    conversation_id = data['conversation_id']
    log_items = LogItem.objects.filter(log__conversation__id=conversation_id).filter(is_visible=True)
    return serialize(log_items)


@csrf_exempt  # REST-like API anyway, who cares lol
def log_edit(request: HttpRequest) -> HttpResponse:
    if not request.method == 'POST':
        return HttpResponseBadRequest(make_must_post())
    data = json.loads(request.body)
    err, ok = assert_keys(data, {
        'log_item_id': int,
    })
    if not ok:
        return HttpResponseBadRequest(err)
    print(data['log_item_id'])
    return JsonResponse({})


# 以降 tools

def gpt(log_texts: LogText, retry: int = 3) -> str:
    re, ok = gpt_check_safety(str(completion(
        text=log_texts,
    )))
    if not ok and retry <= 0:
        return 'The AI response included content deemed as sensitive or unsafe, so it was hidden.'
    if not ok:
        return gpt(log_texts, retry-1)
    return re


def gpt_check_safety(text: str, allow_max: int = 0) -> Tuple[str, bool]:
    safety = int(gpt3.content_filter(text))
    if safety > allow_max:
        return '', False
    else:
        return text, True


def gpt_check_coversation(log_texts: LogText) -> bool:
    return True


def prepare_log_text(conversation: LogItem) -> LogText:
    logtext = ""
    log_list = conversation.log.log_item.objects.all

    for log in log_list:
        logtype = log.type
        if logtype == LogItem.Type.AI or logtype == LogItem.Type.HUMAN:
            logtext += log.name + ": " + log.log_text + "\n"
        elif logtype == LogItem.Type.INITIAL_PROMPT or logtype == LogItem.Type.NARRATION:
            logtext += log.text + "\n"

    logtext += conversation.scenario_id.ai_name + ": "

    return LogText(logtext)
