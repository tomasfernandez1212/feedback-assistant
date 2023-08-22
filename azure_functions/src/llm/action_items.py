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
                "content": "You are an expert in customer service. Your task is to interpret customer's reviews, feedback, and conversations with us to infer action items for us to improve our customer's experience. ",
            },
            {
                "role": "user",
                "content": f"Here is a customer's feedback:\n\n{feedback_item}\n\nFrom this feedback, we have the following observations:\n\n{numbered_observations}\n\nHere are the existing action items we have in our backlog:\n\n{numbered_existing_action_items}\n\nWhat action items to we need to add to our backlog to address the observations. Don't add action items if the ones in the backlog already address the issue.",
            },
        ],
        functions=[
            {
                "name": "report_action_items",
                "description": "This function is used to add more action items to the list. It accepts an array of action item objects.",
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
