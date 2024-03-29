
from . import gpthelpers
from .models import LogItem
MAX_RETRY = 2


#
#
# Session では文字列処理のみ行う。（データベースは操作しない）
#
#


first_followup_prompt = """I am a polite friendly intelligent knowledgeable AI English teacher.

Question: What is your hobby?
Answer: I like playing the piano.
Comment and Follow-up question: Playing the piano seems very difficult. How long have you been practicing playing the piano?
--
Question: What are your plans for the weekends?
Answer: I will go to the gym.
Comment and Follow-up question: That is a great habit! How often do you go to the gym?
--
Question: What is your favorite movie?
Answer: My favorite movie is The Lord of the Rings.
Comment and Follow-up question: It is one of the best movies in the world! My favorite character is Legolas. He is mischievous, has a sense of humour! What do you like about the movie?
--
"""

second_followup_prompt = """I am a polite friendly intelligent knowledgeable AI English teacher.

Question: What sport do you play?
Answer: I like playing soccer!
Comment and Follow-up question: Soccer is pretty hard. Why do you like soccer?
Answer: I used to watch soccer players on TV. I admired them so much. I wanted to be like them one day.
Comment and Follow-up question: You can one day be like Messi! Who is your favorite soccer player?
--
Question: What is your favorite movie?
Answer: My favorite movie is The Lord of the Rings.
Comment and Follow-up question: It is one of the best movies in the world! My favorite character is Legolas. He is mischievous, has a sense of humour! What do you like about the movie?
--
"""

final_comment_prompt = """I am a polite friendly intelligent knowledgeable AI English teacher.

Question: What is your hobby?
Answer: I like playing the piano.
Comment and Follow-up question: Playing piano seems very difficult. How long have you been practicing playing the piano?
Answer: More than an hour everyday!
Comment and Follow-up question: You are hard working! It's important to make a constant effort.
--
Question: What did you do last month?
Answer: I went to Japan last month.
Comment and Follow-up question: Sounds fun! What did you do there?
Answer:I went to sure Itsukushima Shrine
Comment: Cool! I heard that Torii gate appears to almost float on the water during high tide like a mystical island. I want to go to Japan someday.
--
"""


questions_dic = {
    'what-if': ['If you could have lunch with anyone in the world, who would you choose?', 'If money was not a problem, where would you like to travel?', 'What would you do differently if there were 30 hours in a day?', 'Would you like to travel in space?'],
    'learning-english': ['What is the most difficult part of learning English?', 'Why do you want to learn English?'],
    'motivational': ['Which person in your life has motivated you the most?', 'Who do you admire the most?'],
    'likes-dislikes': ['What is your favorite song?', 'What is the best modern invention?', 'Which is more important: love, money, or health?', 'Are you a pet lover?', 'Who is your favorite celebrity?', 'What makes you angry?', 'What is your favorite food?'],
    'other': ['What are your plans for the weekends?', 'What is your country famous for?', 'What did you do yesterday?', 'What are your plans for tomorrow?', 'What is your hobby?', 'What do you hate the most?', 'What is your dream?', 'How is the weather today?', 'Tell me something about you', 'What do you do in your free time?', 'What have you been up to lately?', 'How much sleep do you usually get?', 'Tell me about your best friend'],
    'AI generated': ['Where do you live?', 'What do you usually do on your days off?', 'What do you do in your free time?', 'How do you spend your free time?', 'What is your dream?', 'Which country have you been to?',  'What makes you happy?', 'Describe where you live', 'What do you plan to do today?',  'What is your favorite movie?', 'What is your favorite sport?', 'What is your favorite show?', 'What is your favorite song?', 'What is your favorite movie?', 'What is your favorite book?', 'What is your favorite season?', 'What do you think is the best season?', 'What is your favorite place to go on the weekends', 'What do you buy if you had a lot of money?', 'What is your favorite food?', 'Do you like travelling?', 'Do you play any instruments?', 'What are your favorite summer activities?', 'What are your favorite winter activities?', 'What are you going to do tomorrow?']
}


def create_logitem_dictionary(text, type, name="", corrected_text=None, visible = True, send=True, include_name=True, safety=0):
    return {"text": text,
            "corrected_text": corrected_text,
            "name": name,
            "type": type,
            "visible": visible,
            "send": send,
            "include_name": include_name,
            "safety": safety
            }


class Session:

    def __init__(self, conversation_status, logitems, gpt_parameters, session_status):
        self.logitems = logitems # query set
        self.gpt_parameters = gpt_parameters
        self.session_status = session_status
        self.conversation_status = conversation_status

        self.new_logitems = [] # list (注意： not query set)

    def start_session(self):
        self.session_status["session_is_done"] = False
        self.session_status["session_chat_sent"] = 0

    def chat(message):
        # must be implemented by child class
        return "response from AI",  "exmample response", "good english", self.session_status


    def assess_session_is_done(self):
        return False


class SimpleChat(Session):

    def __init__(self,
                 ai_name,
                 human_name,
                 off_topic_keywords,
                 session_message_limit,
                 logitems,
                 gpt_parameters,
                 conversation_status,
                 session_status={},
                 force_question=True,
                 conversation_end=False,
                 last_message_generator=""):

        self.ai_name = ai_name
        self.human_name = human_name
        self.off_topic_keywords = off_topic_keywords
        self.session_message_limit = session_message_limit
        self.force_question = force_question
        self.conversation_end=conversation_end
        self.last_message_generator=last_message_generator

        super().__init__(conversation_status=conversation_status, session_status=session_status, logitems=logitems, gpt_parameters=gpt_parameters)

    def chat(self, message):
        self.session_status["session_chat_sent"] += 1

        if self.logitems[len(self.logitems)-1].type == "AI":
            corrected_text = gpthelpers.correct_english(message, self.logitems.latest().text)
        else:
            corrected_text = gpthelpers.correct_english(message)

        logitem_human = create_logitem_dictionary(text=message, corrected_text = corrected_text, name=self.human_name, type="User")
        self.new_logitems.append(logitem_human)


        if self.conversation_end and self.last_message_generator is not "":
            prompt = ''
            for log_item in self.logitems:
                if log_item.send == True:
                    prompt += str(log_item) + "\n"

            prompt += logitem_human['name'] + ": " +  logitem_human['text'] + "\n"
            prompt += self.last_message_generator + "\n"
            prompt += f'{self.ai_name}:'
            for i in range(MAX_RETRY):
                response, example_response = gpthelpers.generate_response_and_example_response(prompt=prompt, gpt_parameters = self.gpt_parameters, ai_name = self.ai_name, user_name = self.human_name)

                if self.logitems[len(self.logitems)-1].text not in response: # 前の（AIの）リスポンスと同じだったら、生成し直し
                    break
            logitem_ai = create_logitem_dictionary(text=response, name=self.ai_name, type="AI")
            self.new_logitems.append(logitem_ai)

        else:

            prompt = ''
            for log_item in self.logitems:
                if log_item.send == True:
                    prompt += str(log_item) + "\n"

            prompt += logitem_human['name'] + ": " +  logitem_human['text'] + "\n"
            prompt += f'{self.ai_name}:'

            for i in range(MAX_RETRY):
                response, example_response = gpthelpers.generate_response_and_example_response(prompt=prompt, gpt_parameters = self.gpt_parameters, ai_name = self.ai_name, user_name = self.human_name)

                if self.logitems[len(self.logitems)-1].text not in response: # 前の（AIの）リスポンスと同じだったら、生成し直し
                    break

            logitem_ai = create_logitem_dictionary(text=response, name=self.ai_name, type="AI")
            self.new_logitems.append(logitem_ai)



            # 3回連続で質問でない時は質問を強制的に生成する。
            if self.conversation_status["chat_sent"] >=2 and self.force_question and "?" not in logitem_ai["text"] and '?' not in self.logitems[len(self.logitems)-1].text:
                prompt = ''
                for log_item in self.logitems:
                    if log_item.send == True:
                        prompt += str(log_item) + "\n"

                prompt += logitem_human['name'] + ": " +  logitem_human['text'] + "\n"
                prompt += logitem_ai['name'] + ": " +  logitem_ai['text'] + "\n"
                prompt += logitem_ai['name'] + " asks a question.\n"
                prompt += f'{self.ai_name}:'

                for i in range(MAX_RETRY):
                    response, example_response = gpthelpers.generate_response_and_example_response(prompt=prompt, gpt_parameters = self.gpt_parameters, ai_name = self.ai_name, user_name = self.human_name)

                    if self.logitems[len(self.logitems)-1].text not in response: # 前の（AIの）リスポンスと同じだったら、生成し直し
                        break

                logitem_ai_question = create_logitem_dictionary(text=response, name=self.ai_name, type="AI")
                self.new_logitems.append(logitem_ai_question)


        self.session_status["session_is_done"] = self.assess_session_is_done()

        return example_response, corrected_text

    def assess_session_is_done(self):
        if self.off_topic_keywords:
            return any(keyword in self.new_logitems[-1]["text"] for keyword in self.off_topic_keywords)
        else:
            return False

class AskingQuestions(Session):
    #https://beta.openai.com/playground/p/PfMXPerz7HVSvNv19xm6tLiD?model=davinci


    def start_session(self, question):
        # generate promp from user message
        super().start_session()

        self.session_status["status_number"] = 1
        self.session_status["question"] = question

        logitem = create_logitem_dictionary(text=question, name="Question", type="AI")

        self.new_logitems.append(logitem)

        return [logitem]

    def chat(self, message):

        self.session_status["session_chat_sent"] += 1

        if self.logitems[len(self.logitems)-1].type == "AI":
            corrected_text = gpthelpers.correct_english(message, self.logitems[len(self.logitems)-1].text)
        else:
            corrected_text = gpthelpers.correct_english(message)

        logitem_human = create_logitem_dictionary(text=message, corrected_text = corrected_text, name="Answer", type="User")
        self.new_logitems.append(logitem_human)

        if self.session_status["status_number"] == 1: #final comment and Question

            prompt = first_followup_prompt + "Question: " + self.session_status['question'] + "\nAnswer: " + message  + "\nComment and Follow-up question:"

            response =  gpthelpers.generate_response(prompt=prompt, gpt_parameters=self.gpt_parameters)

            logitem_ai = create_logitem_dictionary(text=response, name="Question", type="AI")
            self.new_logitems.append(logitem_ai)

            self.session_status['first_answer'] = message
            self.session_status['followup'] = response

        elif self.session_status["status_number"] == 2: #followup question 2
            prompt = second_followup_prompt + "Question: " + self.session_status['question'] + "\nAnswer: " + self.session_status['first_answer']  + "\nComment and Follow-up question: " + self.session_status['followup'] + "\nAnswer: " + message + "\nComment and Follow-up question:"
            response =  gpthelpers.generate_response(prompt=prompt, gpt_parameters=self.gpt_parameters)
            logitem_ai = create_logitem_dictionary(text=response, name="Question", type="AI")
            self.new_logitems.append(logitem_ai)

            self.session_status['second_answer'] = message
            self.session_status['second_followup'] = response

        if self.session_status["status_number"] == 3: #final comment and Question
            prompt = final_comment_prompt + "Question: " + self.session_status['question'] + "\nAnswer: " + self.session_status['first_answer']  + "\nComment and Follow-up question: " + self.session_status['followup'] + "\nAnswer: " + self.session_status['second_answer'] + "\nComment and Follow-up question:" + self.session_status['second_followup'] + "\nAnswer: " + message + "\nComment:"

            response =  gpthelpers.generate_response(prompt=prompt, gpt_parameters=self.gpt_parameters)

            logitem_ai = create_logitem_dictionary(text=response, name="Comment", type="AI")

            self.new_logitems.append(logitem_ai)


        if 1 <= self.session_status["status_number"] and self.session_status["status_number"] <= 2:
            self.session_status["status_number"] += 1

        elif self.session_status["status_number"] == 3:
            self.session_status["session_is_done"] = True
        else:
            print("status error")
            self.session_status["status_number"] = 1

        example_response = "Unavailable"

        return example_response, corrected_text

    def assess_session_is_done(self):
        self.session_status["status_number"] == 3

class Welcome(Session):
    def start_session(self):
        super().start_session()
        logitem = create_logitem_dictionary(text="Hello! My name is AIbou. What is your name?", name="AI", type="AI")
        self.new_logitems.append(logitem)
        print(self.new_logitems)

    def chat(self, message):

        logitem_human = create_logitem_dictionary(text=message, corrected_text = message, name="Answer", type="User")
        self.new_logitems.append(logitem_human)

        self.session_status["session_chat_sent"] += 1

        if self.session_status["session_chat_sent"] == 1:
            first_name = gpthelpers.extract_first_name(message)
            text = "Nice to meet you, " + first_name + ". Let's learn English together!"

            logitem = create_logitem_dictionary(text=text, name="AI", type="AI")
            self.new_logitems.append(logitem)

            logitem = create_logitem_dictionary(text="メッセージをクッリクすると翻訳などメニューが表示されます！Enjoy!", name="Narration", type="Narration")
            self.new_logitems.append(logitem)


            self.session_status["session_is_done"] = True


            return "Unavailable", message
