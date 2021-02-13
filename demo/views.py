import json
from typing import Dict, Tuple

from django.http import JsonResponse, HttpRequest, HttpResponseBadRequest, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from restless.models import serialize

from .models import Conversation, Scenario, Log, LogItem
from .openai import completion


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

    conversation: Conversation = Conversation()
    if data['conversation_id'] == -1:
        conversation = Conversation.objects.create(scenario=Scenario.objects.get(pk=1))  # for testing
    else:
        conversation = Conversation.objects.get(pk=data['conversation_id'])
    log = conversation.log
    scenario = conversation.scenario

    logitem_human = LogItem.objects.create(log=log, text=data['user_input'], name_text=scenario.human_name)
    logitem_human.save()

    log_text = conversation.prepare()
    # log_text = prepare_log_text(conversation)
    response = gpt(log_text)

    logitem_ai = LogItem.objects.create(log=log, text=response, name_text=scenario.ai_name)
    logitem_ai.save()

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
    conversation = Conversation.objects.create(scenario=scenario)
    log = Log.objects.create(conversation=conversation)
    log_item = LogItem.objects.create(log=log, type=LogItem.Type.INITIAL_PROMPT, text=scenario.initial_prompt)
    conversation.save()
    log.save()
    log_item.save()
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


class LogText(str):
    pass


# 以降 tools

def gpt(log_texts: LogText) -> str:
    return str(completion(
        prompt=log_texts,
    ))


def gpt_check_coversation(log_texts: LogText) -> bool:
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
