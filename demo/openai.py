import os
from typing import Union, List, Dict, Generator, Any

import openai
from openai.openai_object import OpenAIObject

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
) -> Union[Generator[Union[list, OpenAIObject, dict], Any, None], list, OpenAIObject, dict]:
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
