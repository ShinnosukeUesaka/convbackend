from django.http import JsonResponse, HttpRequest, HttpResponseBadRequest, HttpResponse, HttpResponseForbidden
from django.core import serializers
from .models import Conversation, Scenario, LogItem
from . import gpt3
from .gpt3 import completion, content_filter_profanity, ContentSafetyPresets
from . import gpthelpers
import json
from restless.models import serialize

from typing import List
import re
import random

from . import sessions


class Controller:
    def __init__(self, conversation: Conversation):
        self.conversation = conversation
        self.scenario = conversation.scenario

        try:
            self.conversation_status = json.loads(conversation.temp_for_conv_controller)
        except:
            self.conversation_status = {}

        # settings shouldn't be edited from conversation controller.
        try:

            self.scenario_settings = json.loads(self.scenario.options)
        except:
            self.scenario_settings = {}
        print(json.loads(self.scenario.options))

        self.responses = [] # ここにAIからのリスポンスを入れる
        self.example_response = "Unavailable"
        self.good_english = "Unavailable" # 文法修正

        # AI用のパラメーター
        self.gpt_parameters = {"temperature": self.scenario.temperature, "presence_penalty": self.scenario.presence_penalty, "frequency_penalty": self.scenario.frequency_penalty, "top_p": self.scenario.top_p, "max_tokens": self.scenario.max_tokens}


    def initialise(self):
        self.conversation_status["chat_sent"] = 0
        self.conversation_status["session_number"] = 0
        self.conversation_status["session_start_log_number"] = 0
        self.conversation_status["conversation_is_done"] = False

        self.create_first_messages()

        self.start_new_session()

        self.save_conversation_status()

        print(self.responses)

        return serialize(self.responses)

    def chat(self, message):

        self.conversation_status["chat_sent"] += 1

        self.session = self.choose_session()
        print(self.session.session_status)

        self.example_response, self.good_english = self.session.chat(message)
        self.responses += self.save_session_logitems()

        if self.session.session_status["session_is_done"] == True:
            self.end_session()

        # save everything into database


        self.conversation_status["conversation_is_done"] = self.assess_conversation_is_done()

        if self.conversation_status["conversation_is_done"]:
            self.end_conversation()




        self.responses = self.responses[1:] # omit user message

        self.save_conversation_status()

        print(self.conversation_status)
        output = serialize(self.responses), self.example_response, self.good_english, self.conversation_status["conversation_is_done"]
        return output

    def choose_session(self):
        # must be implemented with child class
        pass

    def start_new_session(self):
        # must be implemented with child class
        pass

    def end_conversation(self):
        self.conversation.active = False
        self.create_last_messages()

    def end_session(self):
        pass

    def create_first_messages(self):
        logitems = []
        if self.scenario.first_logitems.all().count() != 0:
            first_logitems = self.scenario.first_logitems.all().order_by('log_number')
            for first_logitems in first_logitems:

                first_logitems.log_number = self.conversation.current_log_number() + 1
                first_logitems.pk = None
                first_logitems.scenario_first = None
                first_logitems.scenario_last = None
                first_logitems.conversation = self.conversation
                first_logitems.save()

                if first_logitems.visible == True:
                    logitems.append(first_logitems)

        self.responses += logitems

        return logitems

    def create_last_messages(self):
        logitems = []

        if self.scenario.last_logitems.all().count() != 0:
            last_logitems = self.scenario.last_logitems.all().order_by('log_number')

            for last_logitem in last_logitems:
                last_logitem.log_number = self.conversation.current_log_number() + 1
                last_logitem.pk = None
                last_logitem.scenario_first = None
                last_logitem.scenario_last = None
                last_logitem.conversation = self.conversation
                last_logitem.save()

                if last_logitem.visible == True:
                    logitems.append(last_logitem)

        self.responses += logitems

        return logitems

    def assess_conversation_is_done(self):
        if self.scenario.message_limit:
            if self.scenario.message_limit <= self.conversation_status["chat_sent"]:
                return True
        return False

    def save_conversation_status(self):
        # 会話のステータスデータをデータベースに保存
        self.conversation_status["session_status"] = self.session.session_status

        self.conversation.temp_for_conv_controller = json.dumps(self.conversation_status)
        self.conversation.save()

    def save_session_logitems(self):
        logitems = []
        for logitem in self.session.new_logitems:
            logitem = LogItem.objects.create(text=logitem["text"], corrected_text=logitem["corrected_text"], name=logitem["name"], type=logitem["type"], log_number=self.conversation.current_log_number() + 1, conversation=self.conversation, visible=logitem["visible"], send=logitem["send"], include_name=logitem["include_name"], safety=logitem["safety"])
            logitem.save()
            logitems.append(logitem)
        return logitems


    def save_list_of_logitems(self, logitems_list):
        logitems = []
        for logitem_list in logitems_list:
            logitem = LogItem.objects.create(text=logitem_list["text"], corrected_text=logitem_list["corrected_text"], name=logitem_list["name"], type=logitem_list["type"], log_number=self.conversation.current_log_number() + 1, conversation=self.conversation, visible=logitem_list["visible"], send=logitem_list["send"], include_name=logitem_list["include_name"], safety=logitem_list["safety"])
            logitem.save()
            logitems.append(logitem)
        return logitems


class Simple(Controller):

    def choose_session(self):
        logitems = self.conversation.logitem_set.all()[self.conversation_status["session_start_log_number"]:]

        session = sessions.SimpleChat(logitems=logitems,
                                      session_status=self.conversation_status["session_status"],
                                      gpt_parameters=self.gpt_parameters,
                                      ai_name=self.scenario.ai_name,
                                      human_name=self.scenario.human_name,
                                      off_topic_keywords=self.scenario_settings["end sequence"] if "end sequence" in self.scenario_settings else [],
                                      session_message_limit=self.scenario.message_limit)
        return session

    def start_new_session(self):
        self.conversation_status["session_number"] += 1

        session_logitems = self.conversation.logitem_set.all()[self.conversation_status["session_start_log_number"]:]

        self.conversation_status["session_status"] = {}

        self.session = sessions.SimpleChat(logitems=session_logitems,
                                      session_status=self.conversation_status["session_status"],
                                      gpt_parameters=self.gpt_parameters,
                                      ai_name=self.scenario.ai_name,
                                      human_name=self.scenario.human_name,
                                      off_topic_keywords=self.scenario_settings["end sequence"] if "end sequence" in self.scenario_settings else [],
                                      session_message_limit=self.scenario.message_limit)

        self.session.start_session()
        self.responses += self.save_session_logitems()

        return self.session


    def assess_conversation_is_done(self):
        if super().assess_conversation_is_done():
            return True
        if self.session.session_status["session_is_done"] == True:#session が一つしかない場合、sessionが終わり次第conversationも終わる。
            return True
        return False

class Question(Controller):
    def choose_session(self):
        session_logitems = self.conversation.logitem_set.all()[self.conversation_status["session_start_log_number"]-1:]

        self.session = sessions.AskingQuestions(logitems=session_logitems,
                                      session_status=self.conversation_status["session_status"],
                                      gpt_parameters=self.gpt_parameters)

        print(self.session.session_status)
        return self.session

    def start_new_session(self):
        self.conversation_status["session_number"] += 1

        self.conversation_status["session_start_log_number"] = self.conversation.current_log_number() + 1

        session_logitems = []

        # reset session_status
        self.conversation_status["session_status"] = {}

        self.session = sessions.AskingQuestions(logitems=session_logitems,
                                      session_status=self.conversation_status["session_status"],
                                      gpt_parameters=self.gpt_parameters)
        print(self.scenario_settings)
        print(self.scenario.options)

        question = self.choose_question() # list of questions such as "What is your favorite food?"
        self.session.start_session(question)
        self.responses += self.save_session_logitems()

        return self.session

    def end_session(self):
        if not self.assess_conversation_is_done():
            self.start_new_session()

    def choose_question(self):
        question_index = self.conversation_status["session_number"] - 1
        return self.scenario_settings["questions"][question_index]

    def assess_conversation_is_done(self):
        if super().assess_conversation_is_done():
            return True
        if self.session.session_status["session_is_done"] and self.conversation_status["session_number"] == len(self.scenario_settings["questions"]):
            return True
        else:
            return False



class Aibou(Question):
    def initialise(self):
        self.conversation_status["current_session"] = "Welcome"
        return super().initialise()

    def choose_question(self):
        question_index = self.conversation_status["chat_sent"] % len(self.scenario_settings["questions"])
        return self.scenario_settings["questions"][question_index]

    def choose_session(self):
        session_logitems = self.conversation.logitem_set.all()[self.conversation_status["session_start_log_number"]-1:]


        if self.conversation_status["current_session"] == "AskingQuestions":

            self.session = sessions.AskingQuestions(logitems=session_logitems,
                                          session_status=self.conversation_status["session_status"],
                                          gpt_parameters=self.gpt_parameters)

        elif self.conversation_status["current_session"] == "Welcome":
            self.session = sessions.Welcome(logitems=session_logitems,
                                          session_status=self.conversation_status["session_status"],
                                          gpt_parameters=self.gpt_parameters)
        else:
            print("error session not found")

        print(self.session.session_status)
        return self.session

    def start_new_session(self):
        self.conversation_status["session_number"] += 1

        self.conversation_status["session_start_log_number"] = self.conversation.current_log_number() + 1

        # reset session_status
        self.conversation_status["session_status"] = {}

        if self.conversation_status["session_number"] == 1:
            self.conversation_status["current_session"] = "Welcome"
            self.session = sessions.Welcome(logitems=[],
                                          session_status=self.conversation_status["session_status"],
                                          gpt_parameters=self.gpt_parameters)
            self.session.start_session()
            print(self.session.new_logitems)
            self.responses += self.save_session_logitems()
            print(self.responses)
        else:
            self.conversation_status["current_session"] = "AskingQuestions"
            self.session = sessions.AskingQuestions(logitems=[],
                                          session_status=self.conversation_status["session_status"],
                                          gpt_parameters=self.gpt_parameters)

            question = self.choose_question() # list of questions such as "What is your favorite food?"
            self.session.start_session(question)
            self.responses += self.save_session_logitems()


        return self.session


    def assess_conversation_is_done(self):
        return False

class ConvController:
   MAX_REGENERATE = 2

   def __init__(self, conversation: Conversation):
        self.conversation = conversation
        self.scenario = conversation.scenario

        self.gpt_parameters = {"temperature": self.scenario.temperature, "presence_penalty": self.scenario.presence_penalty, "frequency_penalty": self.scenario.frequency_penalty, "top_p": self.scenario.top_p, "max_tokens": self.scenario.max_tokens}

        try:
            self.temp_data = json.loads(conversation.temp_for_conv_controller)
        except:
            self.temp_data = {}
        try:
            self.scenario_options = json.loads(self.scenario.options)
        except:
            self.scenario_options = {}


   def chat(self, message):
        logitem_human = LogItem.objects.create(text=message, name=self.scenario.human_name, type="User",
                                               log_number=self.conversation.current_log_number() + 1, conversation=self.conversation)
        logitem_human.save()

        prompt = self.conversation.prepare()


        for i in range(ConvController.MAX_REGENERATE):

            if self.scenario_options.get("example") == False: # 回答例機能　off の場合
                response = gpthelpers.generate_response_and_example_response(prompt=prompt, gpt_parameters = self.gpt_parameters)
                example_response = "Unavailable"

            else:
                response, example_response = gpthelpers.generate_response_and_example_response(prompt=prompt, gpt_parameters = self.gpt_parameters, ai_name = self.scenario.ai_name, user_name = self.scenario.human_name)

            if self.conversation.logitem_set.get(log_number=self.conversation.current_log_number()-1).text not in response: # 直前のリスポンスと同じだったら、生成し直し
                break

        logitem_ai = LogItem.objects.create(text=response, name=self.scenario.ai_name, type="AI",
                                            log_number=self.conversation.current_log_number() + 1, conversation=self.conversation, safety=0)


        logitem_ai.save()
        good_english = self.generate_correct_english()

        conversation_is_done = self.conversation_is_done()


        return serialize([logitem_ai]), example_response, good_english, self.conversation_is_done()


   def create_response(self, log_text, retry: int = 3, allow_max: int = 0, stop: List[str] = None) -> str:
        # Delete this function some day.
        re = completion(prompt_=log_text, stop=stop, temperature = self.scenario.temperature, presence_penalty = self.scenario.presence_penalty, frequency_penalty = self.scenario.frequency_penalty, top_p = self.scenario.top_p)
        safety = int(gpt3.content_filter(re))
        ok = safety <= allow_max
        if not ok and retry <= 0:
            # return f'The AI response included content deemed as sensitive or unsafe, so it was hidden.\n{re}'
            return re, safety
        if not ok:
            return self.create_response(log_text, retry - 1)
        return re, safety

   def initialise(self):
       #TODO: message 生成　と　variable 生成を関数分ける
        initial_prompts = self.scenario.first_logitems.all()

        messages = []

        initial_prompts = self.scenario.first_logitems.all()

        for initial_prompt in initial_prompts:

            initial_prompt.log_number = self.conversation.current_log_number() + 1

            initial_prompt.pk = None
            initial_prompt.scenario_first = None
            initial_prompt.conversation = self.conversation
            initial_prompt.save()

            if initial_prompt.visible == True:
                messages.append(initial_prompt)

        return serialize(messages)

   def generate_correct_english(self):

        broken_english = self.conversation.logitem_set.get(log_number=self.conversation.current_log_number()-1).text

        if len(broken_english.split()) <= 2: # Do not fix English if it is less than two words.
            return broken_english
        if self.scenario_options.get("context_for_correction") == False:
            correct_english = gpthelpers.correct_english(broken_english)
        else: # 文脈判断オン
            if '?' in broken_english:
                correct_english = gpthelpers.correct_english(broken_english)
            else:
                context = self.conversation.logitem_set.get(log_number=self.conversation.current_log_number()-2).text
                correct_english =  gpthelpers.correct_english(broken_english, context)

        return correct_english


   def conversation_is_done(self): # 会話終了判定
       end_sequence = self.scenario_options.get("end sequence")

       if end_sequence == None:
           return False

       for word in self.scenario_options['end sequence']:
           if word in self.conversation.logitem_set.get(log_number=self.conversation.current_log_number()).text:
               return True
       return False




class ArticleQuestionConvController(ConvController):
    def initialise(self):
        self.temp_data["question_number"] = 0

        first_question = self.choose_question()

        first_log = LogItem.objects.create(
            log_number = 1,
            scenario = None,
            conversation = self.conversation,
            type = "AI",
            name = "Question",
            text = first_question,
            visible = True,
            editable = True,
            send = True,
            include_name = True
        )

        first_log.save()

        self.conversation.temp_for_conv_controller = json.dumps({'question_number': 1})
        self.conversation.save()

        return serialize([first_log])

    def choose_question(self):
        questions = self.scenario_options.get("questions")
        question = questions[self.temp_data["question_number"]]
        return question

    def conversation_is_done(self): # call after choose_question()
        return self.temp_data["question_number"] == len(self.scenario_options.get("questions"))
        # disable the conversation


    def chat(self, message):
         logitems_ai = []
         logitem_human = LogItem.objects.create(text=message, name="Answer", type="User",
                                                log_number=self.conversation.current_log_number() + 1, conversation=self.conversation)
         logitem_human.save()

         questions = self.scenario_options.get("questions")
         question = questions[self.temp_data["question_number"]-1]
         answers = self.scenario_options.get("answers")
         answer = answers[self.temp_data["question_number"]-1]

         if gpthelpers.evaluate_answer(question, answer, message):
             response = "Correct::" + answer
         else:
             response = "Wrong::" + answer

         logitem_ai = LogItem.objects.create(text=response, name="Question", type="AI",
                                             log_number=self.conversation.current_log_number() + 1, conversation=self.conversation, safety=0)


         logitem_ai.save()

         conv_done = self.conversation_is_done()
         logitems_ai = [logitem_ai]
         if not conv_done:
             next_question = questions[self.temp_data["question_number"]]

             logitem_ai2 = LogItem.objects.create(text=next_question, name=self.scenario.ai_name, type="AI",
                                                 log_number=self.conversation.current_log_number() + 1, conversation=self.conversation, safety=0)
             logitem_ai2.save()
             logitems_ai = [logitem_ai, logitem_ai2]

         good_english = gpthelpers.correct_english(message)


         self.temp_data["question_number"] =  self.temp_data["question_number"] + 1
         self.conversation.temp_for_conv_controller = json.dumps(self.temp_data)
         self.conversation.save()

         return serialize(logitems_ai), "Unavailable", good_english, conv_done
