from django.shortcuts import render
from django.http import JsonResponse

from restless.models import serialize
from .models import Conversation, Scenario, Log, LogItem

from django.views.decorators.csrf import csrf_exempt

import json

def chat(request, conversation_id):
    if request.method == 'post':
        data = json.loads(request.body)
        conversation = Conversation.objects.get(pk=conversation_id)
        log = conversation.log
        scenario = conversation.scenario

        logitem_human = LogItem.objects.create(log=human, text=data['user_input'], name_text=scenario.human_name)
        logitem_human.save()


        log_text = generate_log_text(conversation)
        response = gpt(log_text)


        logitem_ai = LogItem.objects.create(log=log, text=response, name_text=scenario.ai_name)
        logitem_ai.save()

        return JsonResponse({'response': response})

@csrf_exempt
def create_conversation(request):
    if request.method == 'POST':
        print(json.loads(request.body))
        #scenario = Scenario.objects.get(pk=request.POST.get('scenario_id'))
        scenario = Scenario.objects.get(pk=json.loads(request.body)['scenario_id'])
        conversation = Conversation.objects.create(scenario=scenario)
        log = Log.objects.create(conversation = conversation)
        conversation.save
        log.save
        return JsonResponse({'conversation_id': conversation.id, 'scenario_data': serialize(scenario)})
    #delete実装

def edit_log(request):
    return

def reload_ai(request):
    return


def gpt(log_texts):
    return 'hi'

def prepare_log_text(conversation):
    logtext = ""
    log_list = conversation.log.log_item.objects.all

    for log in log_list:
        logtype = log.type
        if logtype == LogItem.Type.AI or logtype == LogItem.Type.HUMAN:
            logtext += log.name_text + ": " + log.log_text + "\n"
        elif logtype == LogItem.Type.INITIAL_PROMPT or logtype == LogItem.Type.NARRATION:
            logtext += log.text  + "\n"
    logtext += log.name_text + ": "

    return logtext
