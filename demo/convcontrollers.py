from django.http import JsonResponse, HttpRequest, HttpResponseBadRequest, HttpResponse, HttpResponseForbidden
from django.core import serializers
from .models import Conversation, Scenario, LogItem
from . import gpt3
from .gpt3 import completion, content_filter_profanity, ContentSafetyPresets
import json
from restless.models import serialize

import random



def combine_lists(dictionary):
    combined_list = []
    for key in dictionary:
        combined_list += dictionary[key]
    return combined_list

class ConvController:

   def __init__(self, conversation: Conversation):
        self.conversation = conversation
        self.scenario = conversation.scenario
        try:
            self.temp_data = json.loads(conversation.temp_for_conv_controller)
        except:
            self.temp_data = {}


   def chat(self, message):
        logitem_human = LogItem.objects.create(text=message, name=self.scenario.human_name, type="User",
                                               log_number=self.conversation.current_log_number() + 1, conversation=self.conversation)
        logitem_human.save()

        log_text = self.conversation.prepare()
        response, safety = self.create_response(log_text=log_text)

        print(f'response: {response}')
        logitem_ai = LogItem.objects.create(text=response, name=self.scenario.ai_name, type="AI",
                                            log_number=self.conversation.current_log_number() + 1, conversation=self.conversation, safety=safety)


        logitem_ai.save()

        return serialize([logitem_ai])

   def create_response(self, log_text, retry: int = 3, allow_max: int = 0) -> str:
        #print(f"GPT3 request: \n {log_text}")
        re = completion(prompt_=log_text)
        safety = int(gpt3.content_filter(re))
        ok = safety <= allow_max
        if not ok and retry <= 0:
            # return f'The AI response included content deemed as sensitive or unsafe, so it was hidden.\n{re}'
            return re, safety
        if not ok:
            return create_response(log_text, retry - 1)
        return re, safety

   def initialise(self):
        initial_prompts = self.scenario.logitem_set.all()

        messages = []

        initial_prompts = self.scenario.logitem_set.all()

        for initial_prompt in initial_prompts:

            initial_prompt.log_number = self.conversation.current_log_number() + 1
            print(self.conversation.current_log_number())
            initial_prompt.pk = None
            initial_prompt.scenario = None
            initial_prompt.conversation = self.conversation
            initial_prompt.save()

            if initial_prompt.visible == True:
                messages.append(initial_prompt)

        return serialize(messages)

        #json.dumps(self.temp_data)
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

Question: What sport do you play?
Answer: I like playing soccer!
Question: I am not good at soccer but I like watching people play! Who is your favorite soccer player?
--
Question: What did you last summer?
Answer: I went to Tokyo last month.
Question: Tokyo is such a beautiful city with rich culture! Did you eat sushi?
--
Question: What is your hobby.
Answer: My hobby is to do programing or coding.
Question: Solving problems is fun! Do you develop your own games?
--
"""

    second_followup_prompt = """I am a polite friendly intelligent AI English teacher.

Question: What sport do you play?
Answer: I like playing soccer!
Question: Soccer is pretty hard. Why do you like soccer?
Answer: I used to watch soccer players on TV. I admired them so much. I wanted to be like them one day.
Question: Yes you can be like them! Who is your favorite player?
--
Question: What did you do month?
Answer: I traveled to three different countries.
Question: Wow! Sounds exciting! Which countries did you visit?
Answer: Korea, Japan and the United states!
Question: I have never been to Korea. What was for favorite part of the trip?
--
"""

    final_comment_prompt = """I am a polite friendly intelligent AI English teacher.

Question: What sport do you play?
Answer: I like playing soccer!
Question: Soccer is pretty hard. Why do you like soccer?
Answer: I used to watch soccer players on TV. I admired them so much. I wanted to be like them one day.
Comment: Yes you can be like them!
--
Question: What did you do month?
Answer: I went to Los last month.
Question: Sounds fun! What did you do there?
Answer: I was relaxing in a hotel.
Comment: It is sometimes important to take a break!
--
"""

    questions_dic = {
        'what-if': ['If you could have lunch with anyone in the world, who would you choose?', 'If money was no problem, where would you like to travel on holiday?', 'If you could address the whole world, what would you say?', 'Would you rather be a big fish in a small pond or a small fish in a big pond?', 'What would you do if a genie gave you three wishes?', 'What would you do differently if there were 30 hours in a day?', 'Would you like to travel in space?', 'If an alien came to Earth, where would you show it around?'],
        'learning-english': ['Do you enjoy speaking English?', 'What is the best way to improve your speaking?', 'What is the most difficult part of learning English?', 'How is English different from your language?', 'Why do you want to learn English?'],
        'motivational': ['Which person in your life has motivated you the most?', 'Who do you admire the most?', 'What is your definition of happiness?', 'Name three things that make you happy.', 'What are your strengths?', 'Think up three ways to spice up your life and share them with your partner.', 'What is your favorite saying?'],
        'likes-dislikes': ['What phobias do you have?', 'What is your favorite song?', 'What is the best modern invention?', 'Which is more important: love, money or health?', 'Describe your ideal partner.', 'Are you a pet lover?', 'Would you like to be a celebrity?', 'Who is your favorite celebrity?', 'What was your favorite subject at school?', 'What is your favorite time of the day?', 'What gets you really angry?', 'What is your favorite food?'],
        'other': ['What are your plans for the weekends?', 'What is your country famous for?', 'What are your plans for the weekends?', 'What did you do yesterday?', 'What are your plans for tomorrow?', 'What did you eat this morning?', 'What is your hobby?', 'What do you hate the most?', 'What is your dream?', 'How is the weather today?', 'Tell me something about you', 'What do you do in your free time?', 'What is the weather like?', 'What have you been up to lately?', 'How much sleep do you usually get?', 'Tell me about your friend', '']
    }
    #http://www.roadtogrammar.com/dl/warmers.pdf
    questions = combine_lists(questions_dic)

    def create_response(self, log_text) -> str:
         #print(f"GPT3 request: \n {log_text}")
         print("HI!!!")
         re = completion(prompt_=log_text, temperature = QConvController.temperature, presence_penalty = QConvController.presence_penalty, frequency_penalty = QConvController.frequency_penalty)
         safety = int(gpt3.content_filter(re))
         return re, safety

    def chat(self, message):


        logitem_human = LogItem.objects.create(text=message, name=QConvController.user_name, type="User",
                                               log_number=self.conversation.current_log_number() + 1, conversation=self.conversation)
        logitem_human.save()


        status = self.temp_data['status']

        log_items = []

        print(status)
        if status == 1: #final comment and Question
            log_text = QConvController.final_comment_prompt + "Question: " + self.temp_data['question'] + "\nAnswer: " + self.temp_data['first_answer']  + "\nQuestion: " + self.temp_data['followup'] + "\nAnswer: " + self.temp_data['second_answer'] + "\nQuestion:" + self.temp_data['second_followup'] + "\nAnswer: " + message + "\nComment: "
            response, safety =  self.create_response(log_text=log_text)

            # generate next question.
            question = random.choice(QConvController.questions)

            logitem_ai = LogItem.objects.create(text=response, name=QConvController.ai_name_question, type="AI",
                                                log_number=self.conversation.current_log_number() + 1, conversation=self.conversation, safety=safety)
            logitem_ai.save()
            logitem_ai2 = LogItem.objects.create(text=question, name=QConvController.ai_name_question, type="AI",
                                                log_number=self.conversation.current_log_number() + 1, conversation=self.conversation, safety=safety)
            logitem_ai2.save()
            log_items = [logitem_ai, logitem_ai2]

            self.temp_data['question'] = question
            self.temp_data['status'] = 2

        elif status == 2: #followup question
            log_text = QConvController.first_followup_prompt + "Question: " + self.temp_data['question'] + "\nAnswer: " + message  + "\nQuestion:"
            response, safety =  self.create_response(log_text=log_text)
            logitem_ai = LogItem.objects.create(text=response, name=QConvController.ai_name_followup, type="AI",
                                                log_number=self.conversation.current_log_number() + 1, conversation=self.conversation, safety=safety)
            logitem_ai.save()
            log_items = [logitem_ai]
            self.temp_data['first_answer'] = message
            self.temp_data['followup'] = response
            self.temp_data['status'] = 3

        elif status == 3: #followup question 2
            log_text = QConvController.second_followup_prompt + "Question: " + self.temp_data['question'] + "\nAnswer: " + self.temp_data['first_answer']  + "\nQuestion: " + self.temp_data['followup'] + "\nAnswer: " + message + "\nQuestion:"
            response, safety =  self.create_response(log_text=log_text)
            logitem_ai = LogItem.objects.create(text=response, name=QConvController.ai_name_second_followup, type="AI",
                                                log_number=self.conversation.current_log_number() + 1, conversation=self.conversation, safety=safety)
            logitem_ai.save()
            log_items = [logitem_ai]
            self.temp_data['second_answer'] = message
            self.temp_data['second_followup'] = response
            self.temp_data['status'] = 1



        logitem_ai.save()

        self.conversation.temp_for_conv_controller = json.dumps(self.temp_data)
        self.conversation.save()

        return serialize(log_items)

    # create first question
    def initialise(self):
        first_question = random.choice(QConvController.questions)



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

        print( serialize(first_log))

        return serialize([first_log])
