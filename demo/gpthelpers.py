from . import gpt3
from .gpt3 import completion

import re
import difflib

def evaluate_answer(question, correct_answer, student_answer):

    prompt = f"""Check if the student's answer is Correct or Incorrect. Mark Correct if the meaning is mostly the same.

{correct_answer}

Question: {question}
Student Answer: {student_answer}
Correct or Incorrect:"""
    response = completion(engine='davinci-instruct-beta', prompt_=prompt, temperature = 0, presence_penalty = 0, frequency_penalty = 0, stop=["\n"])
    if response[0] == " ":
        response = response[1:]
    print(response)
    if response == "Correct":
        return True
    elif response == "Incorrect":
        return False
    else:
        print("Error while evaluating quiz answer")
        return True

def correct_english(broken_english, context=None) -> str:
    # https://www.eibunkousei.net/%E6%97%A5%E6%9C%AC%E4%BA%BA%E3%81%AE%E8%8B%B1%E8%AA%9E%E3%81%AB%E3%82%88%E3%81%8F%E3%81%82%E3%82%8B%E9%96%93%E9%81%95%E3%81%84/
    examples =  """BrokenEnglish: Its like that i'm chat with a really person not robot!
GoodEnglish: It feels like chatting with a real person, and not a robot!

BrokenEnglish: I want to make reservation with doctor after one hour.
GoodEnglish: I want to make an appointment with the doctor in an hour.

BrokenEnglish: I'm interesting math.
GoodEnglish: I'm interested in math.

BrokenEnglish: let's eat morning meal tomorrow to fun.
GoodEnglish: Let's have breakfast together tomorrow.

BrokenEnglish: """
    examples_context = """What is your favorite color?
BrokenEnglish: Blue. It color of sky.
GoodEnglish: Blue. It is the color of the sky.

My favorite movie is Harry Potter.
BrokenEnglish: I like Harry Potter too. What you favorite character?
GoodEnglish: I like Harry Potter too. What is your favorite character?

How may I help you?
BrokenEnglish: I want to make reservation with doctor after one hour.
GoodEnglish: I want to make an appointment with the doctor in an hour.

What should we do tomorrow?
BrokenEnglish: let's eat morning meal tomorrow!
GoodEnglish: Let's have breakfast together tomorrow!

"""
    def correction_insignificant(broken_english, correct_english):
        corrections = [li for li in difflib.ndiff(broken_english, correct_english) if li[0] != ' ']

        for i in corrections:
            if i != '+ .' and i != '+ ?' and i != '+ ,' and i != '+ !' and i != '- .' and i != '- ?' and i != '- ,' and i != '- !':
                return False
        return True

    if context == None or "":
        prompt = examples + broken_english + '\nGoodEnglish:'
    else:
        prompt = examples_context + context + "\nBrokenEnglish: " + broken_english + '\nGoodEnglish:'

    correct_english = completion(engine='curie', prompt_=prompt,
    temperature = 0,
    max_tokens = 172,
    top_p = 1,
    frequency_penalty = 0,
    presence_penalty = 0)


    if correct_english[0] == " ":
        correct_english = correct_english[1:]

    if correct_english == context:
        correct_english = broken_english

    if correction_insignificant(broken_english, correct_english):
        return broken_english
    else:
        return correct_english

def define_word(word):

    PROMPT_CONVERT_TO_ORIGINAL_FORM = """word: were
Infinitive: Be

word: has
Infinitive: Have

word: """

    PROMPT_CLASSIFY = """Classify words in to Noun, Verb, Adjective, Adverb or Other.

Word: Sneaked
Class: Verb

Word: Tower
Class: Noun

Word: tries
Class: Verb

Word: """

    PROMPT = """Give Definition, Example Sentence, Synonyms of the word.

Word: Predict
Definition: Say or estimate that a specified thing will happen in the future.
Example Sentence: The scientists predicted that there would be an earthquake.
Synonyms: Forecast, Guess

Word: Civilization
Definition: The stage of human social and cultural development and organization that is considered most advanced.
Example Sentence: Some people think that nuclear war would mean the end of civilization.
Synonyms: Culture, Society

Word: Prejudice
Definition: Preconceived opinion that is not based on reason or actual experience.
Example Sentence: Prejudice against people from different backgrounds.
Synonyms: Bias, Favor

Word: """


    if word[0] == " ":
        word = word[1:]

    word = word.capitalize()

    # 品詞チェック
    prompt = PROMPT_CLASSIFY + word  + "\n" + "Class:"

    output =  completion(engine='curie',
    prompt_=prompt,
    temperature = 0,
    max_tokens = 50,
    top_p = 1,
    frequency_penalty = 0,
    presence_penalty = 0,
    stop=["\n"])

    if output == "Noun" or output == "Verb" or output == "Adjective" or output == "Adverb":
        type = output
    else:
        type = "Other"

    # 品詞が動詞であれば、原型に変換
    if type == "Verb":
        prompt = PROMPT_CONVERT_TO_ORIGINAL_FORM + word  + "\n" + "Infinitive:"

        output =  completion(engine='curie',
        prompt_=prompt,
        temperature = 0,
        max_tokens = 50,
        top_p = 1,
        frequency_penalty = 0,
        presence_penalty = 0,
        stop=["\n"])

        word = output

    #　意味、例文、類義語　生成
    prompt = PROMPT + word + "\n" + "Definition:"

    output =  completion(engine='curie',
    prompt_=prompt,
    temperature = 0,
    max_tokens = 120,
    top_p = 1,
    frequency_penalty = 0,
    presence_penalty = 0,
    stop=["\n\n"])

    if output[0] == " ":
        output =  output[1:]

    try:
        definition, example, synonym = re.split("\nExample Sentence: |\nSynonyms: ", output)
    except:
        definition, example, synonym = "error", "error", "error"

    if 3 <= len(synonym.split()):
        synonym = synonym.split()[0] + " "  + synonym.split()[1][:-1]


    return {
        'word': word,
        'type': type,
        'definition': definition,
        'example': example,
        'synonym': synonym
    }


def generate_response(prompt: str, gpt_parameters):
    # メッセージ生成
    # Todo: Check for safety.
    stop = "\n"
    response = completion(
        prompt_ = prompt,
        engine = 'davinci',
        stop = [stop],
        temperature = gpt_parameters["temperature"],
        top_p = gpt_parameters["top_p"],
        frequency_penalty = gpt_parameters["frequency_penalty"],
        presence_penalty = gpt_parameters["presence_penalty"]
    )
    if response[0] == " ":
        response = response[1:]
    return response


def generate_response_and_example_response(prompt, gpt_parameters, ai_name, user_name):
    # メッセージ生成。回答例も一緒に生成。

    stop_sequence = "\n" + ai_name
    output = completion(engine='davinci',
                                temperature = gpt_parameters["temperature"],
                                max_tokens = gpt_parameters["max_tokens"],
                                top_p = gpt_parameters["top_p"],
                                frequency_penalty = gpt_parameters["frequency_penalty"],
                                presence_penalty = gpt_parameters["presence_penalty"],
                                stop=[stop_sequence],
                                prompt_=prompt)
    try:
        response, example_response = re.split("\n" + user_name + ": ", output)
    except:
        response = output
        example_response = "Unavailable"

    if response[0] == " ":
        response = response[1:]
    if "\n" in response:
        response = response[:response.index("\n")]

    return response, example_response



def convert_questions_to_full_question(question, context) -> str:

    PROMPT = """I am studying mathematics at a university.
Why did you decide to majorar that?
Full Question: Why did you decide to major in mathematics at your university?

"""
    input = PROMPT + context + "\n" + question + "\n" + "Full Question:"

    output =  completion(engine='davinci', prompt_=input,
    temperature = 0,
    max_tokens = 300,
    top_p = 1,
    frequency_penalty = 0,
    presence_penalty = 0,
    stop=["\n"])

    if output[0] == " ":
        return output[1:]
    else:
        return output

    return output

def conver_question_answer_to_full_sentence(question, answer) -> str:
    PROMPT = """Why are you learning English?
I want to make foreign friends.
Full sentence: I am learning English, because I want to make foreign friends.

Are you a pet lover?
Yes. I have two dogs.
Full sentence: I am a pet lover. I have two dogs.

What is your dream?
I want to become a doctor
Full sentence: My dream is to become a doctor.

"""
    input = PROMPT + question + "\n" + answer + "\n" + "Full Sentence:"

    output =  completion(engine='davinci', prompt_=input,
    temperature = 0,
    max_tokens = 300,
    top_p = 1,
    frequency_penalty = 0,
    presence_penalty = 0,
    stop=["\n"])

    if output[0] == " ":
        return output[1:]
    else:
        return output

    return output
