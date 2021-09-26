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
import difflib


def combine_lists(dictionary):
    combined_list = []
    for key in dictionary:
        combined_list += dictionary[key]
    return combined_list

class ConvController:
   MAX_REGENERATE = 2

   def __init__(self, conversation: Conversation):
        self.conversation = conversation
        self.scenario = conversation.scenario
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

        log_text = self.conversation.prepare()


        for i in range(ConvController.MAX_REGENERATE):
            if self.scenario_options.get("example") == False:
                stop_sequence = "\n"
                response, safety = self.create_response(log_text=log_text, stop=[stop_sequence])
                example_response = "Unavailable"

            else:
                stop_sequence = "\n" + self.scenario.ai_name
                output, safety = self.create_response(log_text=log_text, stop=[stop_sequence])
                print(f'the pure response from gpt3: {output}')
                try:
                    response, example_response = re.split("\n" + self.scenario.human_name + ": ", output)
                except:
                    response = output
                    example_response = "Unavailabe"

            if self.conversation.logitem_set.get(log_number=self.conversation.current_log_number()-1).text not in response:
                break



        if response[0] == " ":
            response = response[1:]
        if "\n" in response:
            response = response[:response.index("\n")]

        logitem_ai = LogItem.objects.create(text=response, name=self.scenario.ai_name, type="AI",
                                            log_number=self.conversation.current_log_number() + 1, conversation=self.conversation, safety=safety)


        logitem_ai.save()
        good_english = self.generate_correct_english()

        return serialize([logitem_ai]), example_response, good_english, self.conversation_is_done()

   def create_response(self, log_text, retry: int = 3, allow_max: int = 0, stop: List[str] = None) -> str:
        #print(f"GPT3 request: \n {log_text}")
        re = completion(prompt_=log_text, stop=stop, temperature = float(self.scenario.temperature), presence_penalty = float(self.scenario.presence_penalty), frequency_penalty = float(self.scenario.frequency_penalty), top_p = float(self.scenario.top_p))
        safety = int(gpt3.content_filter(re))
        ok = safety <= allow_max
        if not ok and retry <= 0:
            # return f'The AI response included content deemed as sensitive or unsafe, so it was hidden.\n{re}'
            return re, safety
        if not ok:
            return self.create_response(log_text, retry - 1)
        return re, safety

   def initialise(self):
        initial_prompts = self.scenario.logitem_set.all()

        messages = []

        initial_prompts = self.scenario.logitem_set.all()

        for initial_prompt in initial_prompts:

            initial_prompt.log_number = self.conversation.current_log_number() + 1
            initial_prompt.pk = None
            initial_prompt.scenario = None
            initial_prompt.conversation = self.conversation
            initial_prompt.save()

            if initial_prompt.visible == True:
                messages.append(initial_prompt)

        return serialize(messages)

    #json.dumps(self.temp_data)
   def generate_correct_english(self):
        def correction_insignificant(correction):
            for i in correction:
                if i != '+ .' and i != '+ ?' and i != '+ ,' and i != '+ !':
                    return False
            return True

        broken_english = self.conversation.logitem_set.get(log_number=self.conversation.current_log_number()-1).text

        if self.scenario_options.get("context_for_correction") == False:
            correct_english = self.correct_english(broken_english)

        else: # 文脈判断オン
            if len(broken_english.split()) <= 2:
                return broken_english
            elif '?' in broken_english:
                correct_english = self.correct_english(broken_english)
            else:
                context = self.conversation.logitem_set.get(log_number=self.conversation.current_log_number()-2).text
                correct_english =  self.correct_english(broken_english, context)

                if correct_english == context: #バグが発生した場合
                    return broken_english

        corrections = [li for li in difflib.ndiff(broken_english, correct_english) if li[0] != ' ']

        if correction_insignificant(corrections):
            return broken_english
        else:
            return correct_english


   def correct_english(self, broken_english, context=None) -> str:
        # move the examples to somewhere easily editable.　#https://www.eibunkousei.net/%E6%97%A5%E6%9C%AC%E4%BA%BA%E3%81%AE%E8%8B%B1%E8%AA%9E%E3%81%AB%E3%82%88%E3%81%8F%E3%81%82%E3%82%8B%E9%96%93%E9%81%95%E3%81%84/
        examples =  """BrokenEnglish: Its like that i'm chat with a really person not robot.
GoodEnglish: It feels like chatting with a real person, and not a robot.

BrokenEnglish: I want to make reservation with doctor after one hour.
GoodEnglish: I would like to make an appointment with the doctor in an hour.

BrokenEnglish: I'm interesting math. because it's fun.
GoodEnglish: I'm interested in math, because it's fun.

BrokenEnglish: let's eat morning meal tomorrow to fun.
GoodEnglish: Let's have breakfast together tomorrow.

BrokenEnglish: """
        examples_context = """What is your favorite color?
BrokenEnglish: Blue. It color of sky.
GoodEnglish: Blue. It is the color of the sky.

Do you play any sports?
BrokenEnglish: Soccer. I am good at it.
GoodEnglish: I play soccer. I am good at it.

How may I help you?
BrokenEnglish: I want to make reservation with doctor after one hour.
GoodEnglish: I want to make an appointment with the doctor in an hour.

What should we do tomorrow?
BrokenEnglish: let's eat morning meal tomorrow.
GoodEnglish: Let's have breakfast together tomorrow.

"""
        if context == None or "":
            prompt = examples + broken_english + '\nGoodEnglish:'
        else:
            prompt = examples_context + context + "\nBrokenEnglish: " + broken_english + '\nGoodEnglish:'

        good_english = completion(engine='curie', prompt_=prompt,
        temperature = 0,
        max_tokens = 172,
        top_p = 1,
        frequency_penalty = 0,
        presence_penalty = 0)

        if good_english[0] == " ":
            return good_english[1:]
        else:
            return good_english

   def conversation_is_done(self):
       end_sequence = self.scenario_options.get("end sequence")

       if end_sequence == None:
           return False

       for word in self.scenario_options['end sequence']:
           if word in self.conversation.logitem_set.get(log_number=self.conversation.current_log_number()).text:
               return True
       return False





class QConvController(ConvController):

    ai_name_question = "Question"
    user_name = "Answer"
    ai_name_followup = "Question"
    ai_name_second_followup = "Question"
    ai_name_last_comment = "Comment"

    temperature = 0.3
    frequency_penalty = 0.5
    presence_penalty = 0.5

    #https://beta.openai.com/playground/p/PfMXPerz7HVSvNv19xm6tLiD?model=davinci
    first_followup_prompt = """I am a polite friendly intelligent AI English teacher.

Question: What is your hobby?
Answer: I like playing the piano.
Comment and Follow-up question: Playing the piano seems very difficult. How long have you been practicing playing the piano?
--
Question: What are your plans for the weekends?
Answer: I will go to the gym.
Comment and Follow-up question: You are so healthy and disciplined! How often do you go to the gym?
--
Question: What is your favorite movie?
Answer: My favorite movie is The Lord of the Rings.
Comment and Follow-up question: My favorite character is Legolas. He is mischievous, has a sense of humour! What is your favorite character?
--
"""

    second_followup_prompt = """I am a polite friendly intelligent AI English teacher.

Question: What sport do you play?
Answer: I like playing soccer!
Comment and Follow-up question: Soccer is pretty hard. Why do you like soccer?
Answer: I used to watch soccer players on TV. I admired them so much. I wanted to be like them one day.
Comment and Follow-up question: Yes you can be like them! Who is your favorite soccer player?
--
Question: What is your hobby?
Answer: I like playing the piano.
Comment and Follow-up question: Playing piano seems very difficult. How long have you been practicing playing the piano?
Answer: More than an hour everyday!
Comment and Follow-up question: You are very hard working! Which piano song are you practicing right now?
--
"""

    final_comment_prompt = """I am a polite friendly intelligent AI English teacher.

Question: What sport do you play?
Answer: I like playing soccer!
Comment and Follow-up question: Soccer is pretty hard. Why do you like soccer?
Answer: I used to watch soccer players on TV. I admired them so much. I wanted to be like them one day.
Comment: Yes you can be like them!
--
Question: What did you do last month?
Answer: I went to Japan last month.
Comment and Follow-up question: Sounds fun! What did you do there?
Answer: I saw a lot of temples.
Comment: Cool! I wish I can go to Japan someday.
--
"""


    questions_dic = {
        'what-if': ['If you could have lunch with anyone in the world, who would you choose?', 'If money was not a problem, where would you like to travel?', 'If you were given five minutes to address the entire world, what would you say?', 'What would you do differently if there were 30 hours in a day?', 'Would you like to travel in space?', 'If an alien came to Earth, where would you show them around?'],
        'learning-english': ['Do you enjoy speaking English?', 'What is the best way to improve your speaking?', 'What is the most difficult part of learning English?', 'Why do you want to learn English?'],
        'motivational': ['Which person in your life has motivated you the most?', 'Who do you admire the most?', 'What is your favorite saying?'],
        'likes-dislikes': ['What phobias do you have?', 'What is your favorite song?', 'What is the best modern invention?', 'Which is more important: love, money, or health?', 'Are you a pet lover?', 'Who is your favorite celebrity?', 'What is your favorite time of the day?', 'What makes you angry?', 'What is your favorite food?'],
        'other': ['What are your plans for the weekends?', 'What is your country famous for?', 'What did you do yesterday?', 'What are your plans for tomorrow?', 'What did you eat this morning?', 'What is your hobby?', 'What do you hate the most?', 'What is your dream?', 'How is the weather today?', 'Tell me something about you', 'What do you do in your free time?', 'What have you been up to lately?', 'How much sleep do you usually get?', 'Tell me about your best friend'],
        'AI generated': ['Where do you live?', 'How many people live in your family?', 'What do you usually do on your days off?', 'What do you do in your free time?', 'How do you spend your free time?', 'What is your dream?', 'Which country have you been to?',  'What makes you happy?', 'Describe where you live', 'What do you plan to do today?',  'What is your favorite movie?', 'What is your favorite sport?', 'What is your favorite show?', 'What is your favorite song?', 'What is your favorite movie?', 'What is your favorite book?', "What's your favorite toy as a child?", 'Which celebrity would you like to meet?', 'What do you like the most about winter?', 'What do you think is the best season?']
    }
    #http://www.roadtogrammar.com/dl/warmers.pdf
    questions = combine_lists(questions_dic)

    def initialise(self):
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

        self.conversation.temp_for_conv_controller = json.dumps({'status': 2, 'question': first_question, 'first_answer': "", 'followup': "", 'second_answer': "", 'second_followup': ""})
        self.conversation.save()

        return serialize([first_log])

    def create_response(self, log_text, retry: int = 1, check_question = False) -> str:
        #print(f"GPT3 request: \n {log_text}")

        re = completion(prompt_=log_text, temperature = QConvController.temperature, presence_penalty = QConvController.presence_penalty, frequency_penalty = QConvController.frequency_penalty)
        #safety = int(gpt3.content_filter(re))
        safety = 0
        if check_question == True:
            if not re.endswith('?'):
                if retry <= 0:
                    return re, safety
                else:
                    return self.create_response(log_text, retry - 1)

        return re, safety

    def chat(self, message):


        logitem_human = LogItem.objects.create(text=message, name=QConvController.user_name, type="User",
                                               log_number=self.conversation.current_log_number() + 1, conversation=self.conversation)
        logitem_human.save()


        status = self.temp_data['status']

        log_items = []



        if status == 1: #final comment and Question
            log_text = QConvController.final_comment_prompt + "Question: " + self.temp_data['question'] + "\nAnswer: " + self.temp_data['first_answer']  + "\nComment and Follow-up question: " + self.temp_data['followup'] + "\nAnswer: " + self.temp_data['second_answer'] + "\nComment and Follow-up question:" + self.temp_data['second_followup'] + "\nAnswer: " + message + "\nComment: "

            response, safety =  self.create_response(log_text=log_text)

            logitem_ai = LogItem.objects.create(text=response, name=QConvController.ai_name_question, type="AI",
                                                log_number=self.conversation.current_log_number() + 1, conversation=self.conversation, safety=safety)
            logitem_ai.save()

            good_english = self.generate_correct_english()

            if self.conversation_is_done():
                log_items = [logitem_ai]
            else:
                # if the conversation still continues generate next question
                question = self.choose_question()

                logitem_ai2 = LogItem.objects.create(text=question, name=QConvController.ai_name_question, type="AI",
                                                    log_number=self.conversation.current_log_number() + 1, conversation=self.conversation, safety=safety)
                logitem_ai2.save()
                log_items = [logitem_ai, logitem_ai2]

                self.temp_data['question'] = question


        elif status == 2: #followup question
            log_text = QConvController.first_followup_prompt + "Question: " + self.temp_data['question'] + "\nAnswer: " + message  + "\nComment and Follow-up question:"
            response, safety =  self.create_response(log_text=log_text, check_question=True)
            logitem_ai = LogItem.objects.create(text=response, name=QConvController.ai_name_followup, type="AI",
                                                log_number=self.conversation.current_log_number() + 1, conversation=self.conversation, safety=safety)
            logitem_ai.save()

            good_english = self.generate_correct_english()

            log_items = [logitem_ai]
            self.temp_data['first_answer'] = message
            self.temp_data['followup'] = response

        elif status == 3: #followup question 2
            log_text = QConvController.second_followup_prompt + "Question: " + self.temp_data['question'] + "\nAnswer: " + self.temp_data['first_answer']  + "\nComment and Follow-up question: " + self.temp_data['followup'] + "\nAnswer: " + message + "\nComment and Follow-up question:"
            response, safety =  self.create_response(log_text=log_text, check_question=True)
            logitem_ai = LogItem.objects.create(text=response, name=QConvController.ai_name_second_followup, type="AI",
                                                log_number=self.conversation.current_log_number() + 1, conversation=self.conversation, safety=safety)
            logitem_ai.save()

            good_english = self.generate_correct_english()

            log_items = [logitem_ai]
            self.temp_data['second_answer'] = message
            self.temp_data['second_followup'] = response

        conv_done = self.conversation_is_done()



        if self.temp_data['status'] == 1 or self.temp_data['status'] == 2:
            self.temp_data['status'] = self.temp_data['status'] + 1
        elif self.temp_data['status'] == 3:
            self.temp_data['status'] = 1
        else:
            print("status error")
            self.temp_data['status'] = 1
        print("-------status" + str(self.temp_data['status']))

        self.conversation.temp_for_conv_controller = json.dumps(self.temp_data)
        self.conversation.save()

        # don't add anything here. status already changed.

        return serialize(log_items), "Unavailabe", good_english, conv_done # response, exmample response, correct english, conversation done?


    def choose_question(self):
        return random.choice(QConvController.questions)

class AIbouConvController(QConvController):
     AI_TEACHER_PROMPT= """The following is a conversation with an AI assistant. The AI assistant is helpful, creative, clever, talkative, and very friendly.

Human: Hello, who are you?
AI: I am AI. I will be your friend. Let's chat!
Human: """



     temperature = 0.4
     frequency_penalty = 0
     presence_penalty = 0.6

     MAX_REGENERATE = 2

     def initialise(self):
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

         self.conversation.temp_for_conv_controller = json.dumps({'status': 2, 'question': first_question, 'first_user_answer_modified': ""})
         self.conversation.save()

         return serialize([first_log])

     def chat(self, message):

        logitem_human = LogItem.objects.create(text=message, name="Human", type="User",
                                               log_number=self.conversation.current_log_number() + 1, conversation=self.conversation)
        logitem_human.save()

        log_items = [] # put response from AI here.

        status = self.temp_data['status']
        if status == 1: #final comment and Question
            prompt = self.generate_prompt_for_aibou(7)

            # Can't be a qeustion. 話題が次にうつるので質問はNG
            for i in range(AIbouConvController.MAX_REGENERATE):
                response = completion(prompt_=prompt, temperature = AIbouConvController.temperature, presence_penalty = AIbouConvController.presence_penalty, frequency_penalty = AIbouConvController.frequency_penalty)
                if '?' not in response:
                    break
                if i == AIbouConvController.MAX_REGENERATE - 1:
                    response = "Interesting"


            logitem_ai = LogItem.objects.create(text=response, name="AI", type="AI",
                                                log_number=self.conversation.current_log_number() + 1, conversation=self.conversation, safety=0)
            logitem_ai.save()

            good_english = self.generate_correct_english()


            question = self.choose_question()

            logitem_ai2 = LogItem.objects.create(text=question, name="AI", type="AI",
                                                log_number=self.conversation.current_log_number() + 1, conversation=self.conversation, safety=0)
            logitem_ai2.save()
            log_items = [logitem_ai, logitem_ai2]

            self.temp_data['question'] = question

        if status == 2:

            prompt = QConvController.first_followup_prompt + "Question: " + self.temp_data['question'] + "\nAnswer: " + message  + "\nComment and Follow-up question:"

            response = completion(prompt_=prompt, temperature = AIbouConvController.temperature, presence_penalty = AIbouConvController.presence_penalty, frequency_penalty = AIbouConvController.frequency_penalty)
            logitem_ai = LogItem.objects.create(text=response, name="AI", type="AI",
                                                log_number=self.conversation.current_log_number() + 1, conversation=self.conversation, safety=0)
            logitem_ai.save()

            self.temp_data['first_user_answer_modified'] = gpthelpers.conver_question_answer_to_full_sentence(self.temp_data['question'], message)

            good_english = self.generate_correct_english()

            log_items = [logitem_ai]

        elif 3 <= status and status <= 4:


            number_of_messages_to_include = (status-1)*2 - 1
            prompt = self.generate_prompt_for_aibou(number_of_messages_to_include)

            response = completion(prompt_=prompt, temperature = AIbouConvController.temperature, presence_penalty = AIbouConvController.presence_penalty, frequency_penalty = AIbouConvController.frequency_penalty)

            logitem_ai = LogItem.objects.create(text=response, name="AI", type="AI",
                                                log_number=self.conversation.current_log_number() + 1, conversation=self.conversation, safety=0)
            logitem_ai.save()

            good_english = self.generate_correct_english()

            log_items = [logitem_ai]
            self.temp_data['first_answer'] = message
            self.temp_data['followup'] = response


        conv_done = self.conversation_is_done()

        status = self.temp_data['status']

        if 1 <= self.temp_data['status'] == 2 or self.temp_data['status'] <= 3:
            self.temp_data['status'] = self.temp_data['status'] + 1
        elif self.temp_data['status'] == 4:
            self.temp_data['status'] = 1
        else:
            print("status error")
            self.temp_data['status'] = 1
        print("-------status" + str(self.temp_data['status']))

        self.conversation.temp_for_conv_controller = json.dumps(self.temp_data)
        self.conversation.save()

        # don't add anything here. status already changed.

        return serialize(log_items), "Unavailabe", good_english, conv_done # response, exmample response, correct english, conversation done?

     def generate_prompt_for_aibou(self, number_of_messages_to_include):

        prompt = AIbouConvController.AI_TEACHER_PROMPT
        prompt += self.temp_data['first_user_answer_modified']
        number_of_messages_to_include = number_of_messages_to_include - 1
        for i in range(number_of_messages_to_include):
            message_index = self.conversation.current_log_number() - number_of_messages_to_include + i + 1
            if self.conversation.logitem_set.get(log_number=message_index).type == "AI":
                prompt += "\nAI: " + self.conversation.logitem_set.get(log_number=message_index).text
            elif self.conversation.logitem_set.get(log_number=message_index).type == "User":
                prompt += "\nHuman: " + self.conversation.logitem_set.get(log_number=message_index).text
        prompt += "\nAI:"
        return prompt

class ArticleDiscussionConvController(QConvController):
    # new temp data added: question_number
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

        self.conversation.temp_for_conv_controller = json.dumps({'status': 2, 'question': first_question, 'first_answer': "", 'followup': "", 'second_answer': "", 'second_followup': "", 'question_number': 1})
        self.conversation.save()

        return serialize([first_log])

    def choose_question(self):
        questions = self.scenario_options.get("questions")
        question = questions[self.temp_data["question_number"]]
        self.temp_data["question_number"] = self.temp_data["question_number"] + 1 # refactor someday
        return question

    def conversation_is_done(self): # call after choose_question()
        return self.temp_data["status"] == 1 and self.temp_data["question_number"] == len(self.scenario_options.get("questions"))
        # disable the conversation


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

         good_english = self.correct_english(message)


         self.temp_data["question_number"] =  self.temp_data["question_number"] + 1
         self.conversation.temp_for_conv_controller = json.dumps(self.temp_data)
         self.conversation.save()

         return serialize(logitems_ai), "Unavailabe", good_english, conv_done
