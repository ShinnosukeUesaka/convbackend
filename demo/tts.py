import os
from typing import Tuple, Union

from ibm_watson import TextToSpeechV1
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator

url = os.environ.get("CONVBACKEND_IBM_CLOUD_URL")
api_key = os.environ.get("CONVBACKEND_IBM_CLOUD_API_KEY")
authenticator = IAMAuthenticator(api_key)
tts_api = TextToSpeechV1(
    authenticator=authenticator
)
tts_api.set_service_url(url)


def tts(text: str, voice: Union[str, None] = None, format: Union[str, None] = None) -> Tuple[bytes, str]:
    if voice is None:
        voice = 'en-US_AllisonV3Voice'
    if format is None:
        format = 'audio/flac'
    return tts_api.synthesize(
        text,
        voice=voice,
        accept=format,
    ).get_result().content, 'application/octet-stream'
