import openai
import re
import json
import logging
from typing import Dict, Any, List


def is_trailing_comma_error(json_str: str, exception: Exception) -> bool:
    """
    Check if error in JSON parsing is because of trailing comma.
    """
    if "Expecting property name enclosed in double quotes" in str(exception):
        last_open_brace = json_str.rfind("{")
        last_close_brace = json_str.rfind("}")

        if last_open_brace < last_close_brace:
            snippet = json_str[last_open_brace : last_close_brace + 1]
            if snippet.rstrip().endswith(",\n}"):
                return True
    return False


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
    except json.decoder.JSONDecodeError as e:
        if is_trailing_comma_error(arguments_str, e):
            arguments_str = fix_trailing_commas(arguments_str)
            arguments = json.loads(arguments_str)
        else:
            logging.error(f"Error unpacking function call arguments: {arguments_str}")
            raise e
    return arguments


def generate_embedding(text: str) -> List[float]:
    response = openai.Embedding.create(input=text, model="text-embedding-ada-002")  # type: ignore
    embeddings = response["data"][0]["embedding"]  # type: ignore
    return embeddings  # type: ignore
