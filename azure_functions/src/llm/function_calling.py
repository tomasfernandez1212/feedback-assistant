import openai
from typing import Dict, Any, List, Optional
from src.data.llmCall import LLMCallLog
from src.llm.utils import unpack_function_call_arguments, LLMCallLogger


def make_function_call(
    model: str,
    messages: List[Dict[str, str]],
    functions: List[Dict[str, Any]],
    function_call: Dict[str, str],
    temperature: Optional[float] = None,
    logger: Optional[LLMCallLogger] = None,
) -> Dict[str, Any]:
    """
    Calls the OpenAI API to make a function call, unpacks the response, and optionally logs the call.
    """
    response = openai.ChatCompletion.create(  # type: ignore
        messages=messages,
        functions=functions,
        function_call=function_call,
        model=model,
        temperature=temperature,
    )
    response_properties = unpack_function_call_arguments(response)
    if logger:
        log_function_call(
            logger=logger,
            messages=messages,
            functions=functions,
            function_call=function_call,
            model=model,
            temperature=temperature,
            response_properties=response_properties,
        )

    return response_properties


def log_function_call(
    logger: LLMCallLogger,
    messages: List[Dict[str, str]],
    functions: List[Dict[str, str]],
    function_call: Dict[str, str],
    model: str,
    temperature: Optional[float],
    response_properties: Dict[str, Any],
):
    """
    Creates an instance of LLMCallLog for a function call and logs it using the logger.
    """
    llm_call_log = LLMCallLog(
        prompt=f"MESSAGES: {messages}\nFUNCTIONS: {functions}\nFUNCTION_CALL: {function_call}\n",
        response=response_properties.__str__(),
        prompt_tokens=response["usage"]["prompt_tokens"],  # type: ignore
        response_tokens=response["usage"]["response_tokens"],  # type: ignore
        total_tokens=response["usage"]["total_tokens"],  # type: ignore
        model=model,  # type: ignore
        temperature=temperature,  # type: ignore
    )

    logger.log_llm_call(llm_call_log)
