# Type Annotations
import json
import os
from typing import Dict, Tuple

# conversation controllers
#from convcontrollers import ConvController

# Responses
from django.core.exceptions import ObjectDoesNotExist
from django.db import connection
from django.http import JsonResponse, HttpRequest, HttpResponseBadRequest, HttpResponse, HttpResponseForbidden
# CSRF Workaround (API, no tUI)
from django.views.decorators.csrf import csrf_exempt
# Rate Limiting
from ratelimit.decorators import ratelimit
# Data Serialization
from restless.models import serialize

# GPT-3 Things
from . import gpt3
from .gpt3 import completion, content_filter_profanity, ContentSafetyPresets

# DB Models & Types
from .models import Conversation, Scenario, LogItem, Coupon
from .types import LogText

from . import convcontrollers
from . import gpthelpers


MINIMUM_VERSION = "1.6.0"


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



def instantiate_controller(type: str, conv: Conversation):
    if conv.scenario.controller_type == "simple":
        return convcontrollers.Simple(conv)
    elif conv.scenario.controller_type == "article_discussion":
        return convcontrollers.Question(conv)
    elif conv.scenario.controller_type == "article_question":
        return convcontrollers.ArticleQuestionConvController(conv)
    elif conv.scenario.controller_type == "aibou":
        return convcontrollers.Aibou(conv)
    elif conv.scenario.controller_type == "test":
        return convcontrollers.Question(conv)
    return








@csrf_exempt  # REST-like API anyway, who cares lol
def scenarios(request: HttpRequest) -> HttpResponse:
    # if not request.method == 'GET':
    #     return HttpResponseBadRequest(make_must_get())

    data = json.loads(request.body)
    err, ok = assert_keys(data, {
        'password': str,
    })
    if not ok:
        return HttpResponseBadRequest(err)
    if not check_pass(data['password']):
        return HttpResponseForbidden('incorrect password')


    return JsonResponse(serialize(Scenario.objects.all()), safe=False)


#@ratelimit(key='ip', rate='60/h')
@csrf_exempt  # REST-like API anyway, who cares lol
def chat(request: HttpRequest) -> HttpResponse:
    # TODO:
    if not request.method == 'POST':
        return HttpResponseBadRequest(make_must_post())
    data = json.loads(request.body)
    err, ok = assert_keys(data, {
        'conversation_id': int,
        'user_input': str,
        'password': str,
    })
    print(data)
    if not ok:
        return HttpResponseBadRequest(err)
    if not check_pass(data['password']):
        return HttpResponseForbidden('incorrect password')

    if content_filter_profanity(data['user_input']) == ContentSafetyPresets.unsafe or content_filter_profanity(data['user_input']) ==  ContentSafetyPresets.sensitive:
        return JsonResponse(make_error('error.safety.user_input_unsafe', 'User input contains unsafe words'))


    conv = Conversation.objects.get(pk=data['conversation_id'])

    scenario = conv.scenario

    controller = instantiate_controller(scenario.controller_type, conv)

    user_input = data['user_input']

    if user_input[0] == " ":
        user_input = user_input[1:]
    if user_input[-1] == " ":
        user_input = user_input[:-1]

    response, example_response, good_english, end_conversation = controller.chat(user_input)

    # correct user english
    return JsonResponse({'response': response,
        'example_response': example_response,
        'english_correction': good_english,
        'end_conversation': end_conversation
    })

@csrf_exempt
def dictionary(request: HttpRequest) -> HttpResponse:
    if not request.method == 'POST':
        return HttpResponseBadRequest(make_must_get())

    data = json.loads(request.body)

    if not check_pass(data['password']):
        return HttpResponseForbidden('incorrect password')

    if "sentence" in data: # 文脈判断
        dictionary = gpthelpers.define_word(data['word'], data['sentence'])
    else:
        dictionary = gpthelpers.define_word(data['word'])


    return JsonResponse(dictionary)

@csrf_exempt
def rephrase(request: HttpRequest) -> HttpResponse:
    if not request.method == 'POST':
        return HttpResponseBadRequest(make_must_get())

    data = json.loads(request.body)

    if not check_pass(data['password']):
        return HttpResponseForbidden('incorrect password')

    sentences = gpthelpers.rephrase(data['sentence'])

    return JsonResponse(sentences, safe=False)



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
            active=True
        )
        conversation.save()
        controller = instantiate_controller(scenario.controller_type, conversation)
        print(type(controller))
        initial_messages = controller.initialise()


        return JsonResponse({'conversation_id': conversation.id, 'scenario_data': serialize(scenario), 'initial_messages': initial_messages})

@csrf_exempt  # REST-like API anyway, who cares lol
def check_coupon(request: HttpRequest):
    if not request.method == 'POST':
        return HttpResponseBadRequest(make_must_post())
    # create new conversation
    data = json.loads(request.body)
    err, ok = assert_keys(data, {
        'code': int,
        'password': str,
    })

    try:
        coupon = Coupon.objects.get(code=data['code'])
        valid = not coupon.used
        amount = coupon.amount
    except:
        valid =  False
        amount = 0

    return JsonResponse({
        'valid': valid,
        'amount': amount
    })




@csrf_exempt
def use_coupon(request: HttpRequest):
    if not request.method == 'POST':
        return HttpResponseBadRequest(make_must_post())
    # create new conversation
    data = json.loads(request.body)
    err, ok = assert_keys(data, {
        'code': int,
        'password': str,
    })

    try:
        coupon = Coupon.objects.get(code=data['code'])
        valid = not coupon.used
        amount = coupon.amount
    except:
        valid =  False
        amount = 0

    if valid:
        coupon.used = True
        coupon.save()



    return JsonResponse({
        'valid': valid,
        'amount': amount
    })


@csrf_exempt
def server_info(request: HttpRequest):
    if not request.method == 'POST':
        return HttpResponseBadRequest(make_must_post())
    # create new conversation
    data = json.loads(request.body)
    err, ok = assert_keys(data, {
        'password': str,
    })

    return JsonResponse({
        'minimum_version': MINIMUM_VERSION
    })














# Below not used.

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
        return JsonResponse(
            {'scenarios': list((s.to_dict() if s is not None else None) for s in Scenario.objects.all()), 'db_queries': len(connection.queries)})
    else:
        try:
            s = Scenario.objects.filter(pk=scenario_id).first()
        except ObjectDoesNotExist:
            return JsonResponse(make_error('error.db.not_found', 'Conversation with id not found.'))
        else:
            return JsonResponse({'scenario': s.to_dict(), 'db_queries': len(connection.queries)})





@ratelimit(key='ip', rate='60/h')
@csrf_exempt
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
