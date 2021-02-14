import os
import warnings

import better_profanity
import requests
import openai

organization: str = os.environ.get("OPENAI_ORG", '')
api_key: str = os.environ.get("OPENAI_API_KEY", '')

openai.api_key = os.environ["OPENAI_API_KEY"]

default_engine: str = 'davinci'  # only using davinci anyway, it's fine for now
default_context: str = '''The following is a conversation with an AI assistant. The assistant is helpful, creative, clever, and very friendly.

Human: Hello, who are you?
AI: I am an AI created by OpenAI. How can I help you today?
Human: '''



try:
    from local_gpt3 import api_key as api_key_
    from local_gpt3 import organization as organization_

    print('local')
    organization = organization_
    api_key = api_key_
except ImportError as err:
    api_key_, organization_ = '', ''  # workaround for lint
    print(err)
    print('non local')


def make_header() -> dict:
    return {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json',
    }


def completion(
        prompt: str,
        engine: str = davinci,
        temperature: str = 0.9,
        max_tokens: str =172,
        top_p: str =1,
        frequency_penalty: str =0,
        presence_penalty: str =0.6,
        stop: list = ["\n"]
) -> str:
    # hardcode options
    '''
    r = requests.post(
        url=f'https://api.openai.com/v1/engines/{engine}/completions',
        json={
            'prompt': f'{text}',
        },
        headers=make_header(),
    )
    if r.status_code != 200:
        warnings.warn(RuntimeWarning(f'POST request for OpenAI API failed: status code is {r.status_code}'))
        return f'POST request for OpenAI API failed: status code is {r.status_code}: {r.text}'
    return r.json()['choices'][0]['text']
    '''
    response = openai.Completion.create(
    engine=engine,
    prompt=prompt,
    temperature=temperature,
    max_tokens=max_tokens,
    top_p=top_p,
    frequency_penalty=frequency_penalty,
    presence_penalty=presence_penalty,
    stop=stop
    )
    return response

# START content_filter
# Content Filter
# Used internally to filter GPT-3 generated content using GPT-3 (lol).


class ContentSafety(int):
    def __str__(self) -> str:
        if int(self) == 0:
            return 'safe'
        elif int(self) == 1:
            return 'sensitive'
        elif int(self) == 2:
            return 'unsafe'
        else:
            return str(int(self))


class ContentSafetyPresets:
    error = ContentSafety(-1)
    safe = ContentSafety(0)
    sensitive = ContentSafety(1)
    unsafe = ContentSafety(2)


def content_filter(text: str) -> ContentSafety:
    filters = [
        content_filter_profanity,  # faster bc not dependent on internet
        content_filter_openai,
    ]
    for filter_ in filters:
        current_cs = filter_(text)
        if ContentSafetyPresets.unsafe == current_cs:
            return ContentSafetyPresets.unsafe
        elif ContentSafetyPresets.sensitive == current_cs:
            return ContentSafetyPresets.sensitive
        elif ContentSafetyPresets.safe == current_cs:
            pass
        elif ContentSafetyPresets.error == current_cs:
            pass
    return ContentSafetyPresets.error


def content_filter_openai(text: str) -> ContentSafety:
    r = requests.post(
        url='https://api.openai.com/v1/engines/content-filter-alpha-c4/completions',
        json={
            'prompt': f'<|endoftext|>{text}\n--\nLabel:',
            'temperature': 0.0,
            'max_tokens': 1,
            'top_p': 0,
        },
        headers=make_header(),
    )
    if r.status_code != 200:
        warnings.warn(RuntimeWarning(f'POST request for OpenAI API failed: status code is {r.status_code}'))
        return ContentSafetyPresets.error
    return ContentSafety(r.json()['choices'][0]['text'])


def content_filter_profanity(text: str) -> ContentSafety:
    filename = './profane_words.txt'
    words = []
    if filename in os.listdir():
        with open(filename) as file:
            words = file.read().split('\n')
    better_profanity.profanity.load_censor_words(words)
    return {
        True: ContentSafetyPresets.unsafe,
        False: ContentSafetyPresets.safe,
    }[better_profanity.profanity.contains_profanity(text)]


# END content_filter


if __name__ == '__main__':
    prompts = [
        'OpenAI is a company.',
        'Donald Trump should be impeached.',
    ]
    for prompt in prompts:
        print(f'{prompt}: {content_filter(prompt)}')
    print(completion('What do you like?\nAI: '))
