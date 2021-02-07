
from django.http import HttpResponse
from .models import Question

from django.http import JsonResponse

def index(request):
    return HttpResponse("Hello, world. You're at the polls index.")

def api(request):
    polls = Question.objects.all()[:2]
    data = {"results": list(polls.values("question_text", "pub_date"))}
    return JsonResponse(data)
