import openai
import re
import json
from typing import Dict, Any, List


def fix_trailing_commas(json_str: str) -> str:
    """
    Remove trailing commas before a closing brace or bracket in a JSON string.
    """
    corrected_str = re.sub(r",\s*([}\]])", r"\1", json_str)
    return corrected_str


def unpack_function_call_arguments(response: Any) -> Dict[str, Any]:
    """
    Unpack function call arguments from a response object.
    """
    arguments_str = response["choices"][0]["message"]["function_call"]["arguments"]
    try:
        arguments = json.loads(arguments_str)
    except:
        # Try to fix trailing commas
        arguments_str = fix_trailing_commas(arguments_str)
        arguments = json.loads(arguments_str)

    return arguments


def generate_embedding(text: str) -> List[float]:
    response = openai.Embedding.create(input=text, model="text-embedding-ada-002")  # type: ignore
    embeddings = response["data"][0]["embedding"]  # type: ignore
    return embeddings  # type: ignore
