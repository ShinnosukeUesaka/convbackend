# Type Annotations
import json
import os
from typing import Dict, Tuple

# Responses
from django.core.exceptions import ObjectDoesNotExist
from django.http import JsonResponse, HttpRequest, HttpResponseBadRequest, HttpResponse, HttpResponseForbidden, \
    HttpResponseNotFound
# CSRF Workaround (API, no tUI)
from django.views.decorators.csrf import csrf_exempt
# Rate Limiting
from ratelimit.decorators import ratelimit
# Data Serialization
from restless.models import serialize

# GPT-3 Things
from . import gpt3, tts
from .gpt3 import completion
# DB Models & Types
from .models import Conversation, Scenario, LogItem
from .types import LogText


def make_error(id_: str, msg: str, **kwargs) -> Dict:
    return {
        'type': id_,
        'msg': msg,
        **kwargs,
    }


def make_must_post() -> JsonResponse:
    return JsonResponse(make_error('error.http.must_be_post', 'must be POST'))


def make_must_get() -> JsonResponse:
    return JsonResponse(make_error('error.http.must_be_get', 'must be GET'))


def check_pass(password: str) -> bool:
    correct = os.environ.get('CONVBACKEND_PASSWORD', None)
    if correct is None or correct == '':
        return False
    return password == correct


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


@ratelimit(key='ip', rate='60/h')
@csrf_exempt  # REST-like API anyway, who cares lol
def chat(request: HttpRequest) -> HttpResponse:
    if not request.method == 'POST':
        return HttpResponseBadRequest(make_must_post())
    data = json.loads(request.body)
    err, ok = assert_keys(data, {
        'conversation_id': int,
        'user_input': str,
        'password': str,
    })
    if not ok:
        return HttpResponseBadRequest(err)
    if not check_pass(data['password']):
        return HttpResponseForbidden('incorrect password')

    conv: Conversation = Conversation()

    if data['conversation_id'] == -1:
        conv = Conversation.objects.create(scenario=Scenario.objects.get(pk=1))  # for testing
    else:

        conv = Conversation.objects.get(pk=data['conversation_id'])
    scenario = conv.scenario
    current_log_number = conv.current_log_number()

    print(f'user: {data}')
    logitem_human = LogItem.objects.create(text=data['user_input'], name=scenario.human_name, type=LogItem.Type.HUMAN, log_number=current_log_number+1, conversation=conv)
    logitem_human.save()
    conv.save()

    log_text = conv.prepare()
    response = gpt(log_text)
    print(f'response: {response}')
    logitem_ai = LogItem.objects.create(text=response, name=scenario.ai_name, type=LogItem.Type.AI, log_number=current_log_number+2, conversation=conv)
    logitem_ai.save()
    conv.save()

    return JsonResponse({'response': serialize(logitem_ai)})


@ratelimit(key='ip', rate='60/h')
@csrf_exempt  # REST-like API anyway, who cares lol
def conversations_view(request: HttpRequest) -> HttpResponse:
    if not request.method == 'POST':
        return HttpResponseBadRequest(make_must_post())
    # create new conversation
    data = json.loads(request.body)
    err, ok = assert_keys(data, {
        'scenario_id': int,
        'password': str,
    })
    if not ok:
        return HttpResponseBadRequest(err)
    if not check_pass(data['password']):
        return HttpResponseForbidden('incorrect password')

    try:
        scenario = Scenario.objects.get(pk=data['scenario_id'])
    except ObjectDoesNotExist:
        return JsonResponse(make_error('error.scenario.nonexistent', 'scenario with given scenario ID is nonexistent.'))
    else:
        conversation = Conversation.objects.create(
            scenario=scenario,
        )

        first_log = LogItem.objects.create(type=LogItem.Type.INITIAL_PROMPT, text=scenario.initial_prompt, log_number=1, conversation=conversation, editable=False)
        conversation.save()
        first_log.save()
        return JsonResponse({'conversation_id': conversation.id, 'scenario_data': serialize(scenario)})


@ratelimit(key='ip', rate='60/h')
@csrf_exempt  # REST-like API anyway, who cares lol
def log_view(request: HttpRequest) -> HttpResponse:
    if not request.method == 'POST':
        return HttpResponseBadRequest(make_must_post())
    data = json.loads(request.body)
    err, ok = assert_keys(data, {
        'conversation_id': int,
        'password': str,
    })
    if not ok:
        return HttpResponseBadRequest(err)
    if not check_pass(data['password']):
        return HttpResponseForbidden('incorrect password')

    conversation_id = data['conversation_id']
    log_items = LogItem.objects.filter(conversation=Conversation.objects.get(pk=conversation_id)).filter(visible=True)
    return JsonResponse(serialize(log_items), safe=False)


@ratelimit(key='ip', rate='60/h')
@csrf_exempt  # REST-like API anyway, who cares lol
def scenario(request: HttpRequest) -> HttpResponse:
    if not request.method == 'GET':
        return HttpResponseBadRequest(make_must_get())

    data = json.loads(request.body)
    err, ok = assert_keys(data, {
        'scenario_id': int,
        'password': str,
    })
    if not ok:
        return HttpResponseBadRequest(err)
    if not check_pass(data['password']):
        return HttpResponseForbidden('incorrect password')

    scenario_id: int = data['scenario_id']
    if scenario_id == -1:
        return JsonResponse({'scenarios': list((s.to_dict() if s is not None else None) for s in Scenario.objects.all())})
    else:
        try:
            s = Scenario.objects.filter(pk=scenario_id).first()
        except ObjectDoesNotExist:
            return JsonResponse(make_error('error.db.not_found', 'Conversation with id not found.'))
        else:
            return JsonResponse({'scenario': s.to_dict()})


@ratelimit(key='ip', rate='60/h')
@csrf_exempt  # REST-like API anyway, who cares lol
def log_edit(request: HttpRequest) -> HttpResponse:
    if not request.method == 'POST':
        return HttpResponseBadRequest(make_must_post())
    data = json.loads(request.body)
    err, ok = assert_keys(data, {
        'conversation_id': int,
        'log_number': int,
        'name': str,
        'text': str,
        'password': str,
    })
    if not ok:
        return HttpResponseBadRequest(err)
    if not check_pass(data['password']):
        return HttpResponseForbidden('incorrect password')

    item: LogItem = LogItem.objects.filter(conversation=data['conversation_id']).get(log_number=data['log_number'])
    if item.editable:
        item.name = data['name']
        item.text = data['text']
        item.save()
        return JsonResponse(serialize(item))
    else:
        return HttpResponseBadRequest()


@ratelimit(key='ip', rate='60/h')
@csrf_exempt  # REST-like API anyway, who cares lol
def tts_req(request: HttpRequest) -> HttpResponse:
    if request.method != 'GET':
        return HttpResponseBadRequest(make_must_post())
    if request.body == '':
        return HttpResponseBadRequest(make_error('error.http.body.blank', 'body is blank'))
    data = json.loads(request.body)

    err, ok = assert_keys(data, {
        'text': str,
        'password': str,
    })
    if not ok:
        return HttpResponseBadRequest(err)
    if not check_pass(data['password']):
        return HttpResponseForbidden('incorrect password')

    data, content_type = tts.tts(data['text'], data.get('voice', None), data.get('format', None))

    return HttpResponse(data, content_type=content_type)


@csrf_exempt  # REST-like API anyway, who cares lol
def trigger_action(request: HttpRequest) -> HttpResponse:
    if not request.method == 'POST':
        return HttpResponseBadRequest(make_must_post())
    data = json.loads(request.body)
    err, ok = assert_keys(data, {
        'conversation_id': int,
        'log_number': int,
        'log_item_params': str,
        'password': str,
    })
    if not ok:
        return HttpResponseBadRequest(err)
    if not check_pass(data['password']):
        return HttpResponseForbidden('incorrect password')

    conversation=Conversation.objects.get(data['conversation_id'])
    action = conversation.scenario.action_set.get(action_number=data['action_number'])
    return action.user_execute(conversation, data['log_item_params'])



# 以降 tools
def gpt(log_texts: LogText, retry: int = 3) -> str:
    re = str(completion(prompt_=log_texts))
    print(f'gpt: {re}')
    ok = gpt_check_safety(re)
    if not ok and retry <= 0:
        # return f'The AI response included content deemed as sensitive or unsafe, so it was hidden.\n{re}'
        return f'unsafe_or_sensitive\n{re}'
    if not ok:
        return gpt(log_texts, retry - 1)
    return f'maybesafe\n{re}'


def gpt_check_safety(text: str, allow_max: int = 0) -> bool:
    safety = int(gpt3.content_filter(text))
    return safety > allow_max
