from typing import List
import openai
from src.data.observations import Observation
from src.data.actionItems import ActionItem

from src.llm.utils import unpack_function_call_arguments


def generate_action_items(
    feedback_item: str,
    observations: List[Observation],
    existing_action_items: List[ActionItem],
) -> List[ActionItem]:
    """
    Given a feedback item, a list of observations, and a list of existing action items, return a list of new action items to add.
    """
    numbered_observations = ""
    for i, observation in enumerate(observations):
        numbered_observations += f"{i}. {observation.text}\n"

    # Identify areas for improvement - if there aren't any, return an empty list. Prevents too many action items.
    areas_for_improvement = identify_areas_for_improvement(feedback_item, observations)
    if len(areas_for_improvement) == 0:
        return []

    # Create a numbered list of areas for improvement
    numbered_areas_for_improvement = ""
    for i, area_for_improvement in enumerate(areas_for_improvement):
        numbered_areas_for_improvement += f"{i}. {area_for_improvement}\n"

    # Create a numbered list of existing action items
    if len(existing_action_items) == 0:
        numbered_existing_action_items = "[]"
    else:
        numbered_existing_action_items = ""
        for i, action_item_text in enumerate(existing_action_items):
            numbered_existing_action_items += f"{i}. {action_item_text.text}\n"

    response = openai.ChatCompletion.create(  # type: ignore
        model="gpt-3.5-turbo-0613",
        messages=[
            {
                "role": "system",
                "content": "You are an expert in customer service. Your task is to interpret customer feedback to infer action items we can take to improve customer experience. ",
            },
            {
                "role": "user",
                "content": f"Here is a customer's feedback:\n\n{feedback_item}\n\nFrom this feedback, we identified the following areas for improvement:\n\n{numbered_areas_for_improvement}\n\nHere are the existing action items we have in our backlog:\n\n{numbered_existing_action_items}\n\nWhat action items to we need to add to our backlog to address the areas of improvement if any. Don't add action items if the ones in the backlog already address the issue.",
            },
        ],
        functions=[
            {
                "name": "report_action_items",
                "description": "This function is used to add more action items.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "action_items": {
                            "type": "array",
                            "description": "A list of action items. For example: ['Evaluate the presentation of the gyro dish, particularly the white sweet potato gyro, to make it easier to eat. The customer found it hard to consume in its current form.', 'Maintain the quality of the fries, as they received high praise from the customer.']",
                            "items": {"type": "string"},
                        }
                    },
                    "required": ["action_items"],
                },
            },
        ],
        function_call={"name": "report_action_items"},
    )

    new_action_items_text: List[str] = unpack_function_call_arguments(response)["action_items"]  # type: ignore

    new_action_items: List[ActionItem] = []
    for action_item_text in new_action_items_text:
        action_item = ActionItem(text=action_item_text)
        new_action_items.append(action_item)

    return new_action_items  # type: ignore


def identify_areas_for_improvement(
    feedback_item: str,
    observations: List[Observation],
) -> List[str]:
    """
    Given a feedback item, identify a list of areas for improvement mentioned.
    """
    numbered_observations = ""
    for i, observation in enumerate(observations):
        numbered_observations += f"{i}. {observation.text}\n"

    response = openai.ChatCompletion.create(  # type: ignore
        model="gpt-3.5-turbo-0613",
        messages=[
            {
                "role": "system",
                "content": "You are an expert in customer service. Your task is to analyze customer feedback and infer if there are any areas for improvement. ",
            },
            {
                "role": "user",
                "content": f"Here is a customer's feedback:\n\n{feedback_item}\n\nFrom this feedback, we have the following observations:\n\n{numbered_observations}\n\nIdentify if there are any potential areas for improvement.",
            },
        ],
        functions=[
            {
                "name": "report_areas_for_improvement",
                "description": "This function is used to report areas for improvement.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "areas_for_improvement": {
                            "type": "array",
                            "description": "A list of areas for improvement. It can be an empty list if there aren't any.",
                            "items": {"type": "string"},
                        }
                    },
                    "required": ["areas_for_improvement"],
                },
            },
        ],
        function_call={"name": "report_areas_for_improvement"},
    )

    areas_for_improvement: List[str] = unpack_function_call_arguments(response)["areas_for_improvement"]  # type: ignore

    return areas_for_improvement  # type: ignore
