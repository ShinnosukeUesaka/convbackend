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


def correct_english(bad_english):
    pass
