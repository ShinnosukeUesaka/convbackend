from . import gpt3
from .gpt3 import completion

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
    else: # error
        return True

def correct_english(broken_english, context=None) -> str:
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

def define_word(word):

    PROMPT = """Define the word and use the word in a sentence.

Word:  Population
Definition: The number of people in a particular area
Example: The population of India is 1.2 billion.

Word: """

    input = PROMPT + word + "\n" + "Definition:"

    output =  completion(engine='davinci', prompt_=input,
    temperature = 0,
    max_tokens = 300,
    top_p = 1,
    frequency_penalty = 0,
    presence_penalty = 0,
    stop=["\n\n"])

    output = output[1:]

    try:
        definition, example = re.split("\nExample: ", output)
    except:
        definition, example = "error", "error"

    return definition, example

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

    output = output[1:]

    return output
