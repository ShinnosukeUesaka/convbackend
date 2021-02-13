import os
import warnings
from typing import Union, List, Dict, Generator, Any

import openai
import requests

try:
    from local_gpt3 import api_key, organization

    print('local')
    openai.organization = organization
    openai.api_key = api_key
except ImportError:
    print('non local')
    openai.organization = os.environ.get("OPENAI_ORG")
    openai.api_key = os.environ.get("OPENAI_API_KEY")

default_engine = 'davinci'  # only using davinci anyway, it's fine for now


def completion(
        prompt: str,
        engine: str = default_engine,
        max_tokens: int = 16,
        temperature: float = 1,
        top_p: float = 1,
        n: int = 1,
        stream: bool = False,
        logprobs: Union[bool, None] = None,
        echo: bool = False,
        stop: Union[str, List, None] = None,
        presence_penalty: float = 0,
        frequency_penalty: float = 0,
        best_of: int = 1,
        logit_bias: Union[Dict[str, float], None] = None,
):
    return ["test"]
    # return openai.Completion.create(
    #     engine=engine,
    #     prompt=prompt,
    #     max_tokens=max_tokens,
    #     temperature=temperature,
    #     top_p=top_p,
    #     n=n,
    #     stream=stream,
    #     logprobs=logprobs,
    #     echo=echo,
    #     stop=stop,
    #     presence_penalty=presence_penalty,
    #     frequency_penalty=frequency_penalty,
    #     best_of=best_of,
    #     logit_bias=logit_bias
    # )


class ContentFilterSafety(int):
    def __str__(self) -> str:
        if self == 0:
            return 'safe'
        elif self == 1:
            return 'sensitive'
        elif self == 2:
            return 'unsafe'
        else:
            return str(self)


def content_filter(
        text: str,
        engine: str = default_engine,
) -> ContentFilterSafety:
    r = requests.post(
        url='https://api.openai.com/v1/engines/content-filter-alpha-c4/completions',
        json={
            'prompt': f'<|endoftext|>{text}\n--\nLabel:',
            'temperature': 0.0,
            'max_tokens': 1,
            'top_p': 0,
        },
        headers={
            'Authorization': f'Bearer {openai.api_key}',
            'Content-Type': 'application/json',
        },
    )
    if r.status_code != 200:
        warnings.warn(RuntimeWarning(f'POST request for OpenAI API failed: status code is {r.status_code}'))
        return ContentFilterSafety(-1)
    return ContentFilterSafety(r.json()['choices'][0]['text'])
    # try:
    #     re_raw = openai.Completion.create(
    #         prompt=f'<|endoftext|>{text}\n--\nLabel:',
    #         engine=engine,
    #         temperature=0.0,
    #         top_p=0,
    #         max_tokens=1,
    #     )
    #     print(re_raw)
    #     re = int(re_raw['choices'][0]['text'])
    # except Exception as err:
    #     warnings.warn(RuntimeWarning(str(err)))
    #     return -1
    # return re


if __name__ == '__main__':
    prompts = [
        'OpenAI is a company.',
        'Donald Trump should be impeached.',
    ]
    for prompt in prompts:
        print(f'{prompt}: {content_filter(prompt)}')
