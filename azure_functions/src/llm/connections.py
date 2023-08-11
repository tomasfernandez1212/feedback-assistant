from typing import Dict, List
import openai
from src.data import DataPoint, ActionItem
from src.llm.utils import unpack_function_call_arguments


def infer_action_items_to_data_point_connections(
    feedback_item: str,
    data_points: List[DataPoint],
    action_items: List[ActionItem],
) -> Dict[int, List[int]]:
    """
    Given a feedback item as context, a list of data points, and a list of action items, infer which action items address which data points.
    """

    # Exit if there are no data points or action items
    if len(data_points) == 0:
        return {}
    if len(action_items) == 0:
        return {}

    # Create a numbered list of data points and action items
    numbered_data_points = ""
    for i, data_point in enumerate(data_points):
        numbered_data_points += f"{i}. {data_point.text}\n"

    numbered_action_items = ""
    for i, action_item in enumerate(action_items):
        numbered_action_items += f"{i}. {action_item.text}\n"

    response = openai.ChatCompletion.create(  # type: ignore
        model="gpt-3.5-turbo-0613",
        messages=[
            {
                "role": "system",
                "content": "You are an expert in customer service. Your task is to interpret customer's reviews, feedback, and conversations with us to infer which action items will help us address takeaways taken from a customer's feedback. ",
            },
            {
                "role": "user",
                "content": f"Here is a customer's feedback:\n\n{feedback_item}\n\nFrom this feedback, we have the following takeaways:\n\n{numbered_data_points}\n\nHere are the action items we have in our backlog:\n\n{numbered_action_items}\n\nFor each action item, report which takeaway(s) the action item helps to address.",
            },
        ],
        functions=[
            {
                "name": "report_action_item_relationships",
                "description": "This function is used report which action items address which takeaway. It accepts an array of action item objects.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "relationships": {
                            "type": "array",
                            "description": "A list of relationships.",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "action_item_id": {
                                        "type": "integer",
                                        "description": "The id of the action item. For example: 0",
                                    },
                                    "data_point_ids": {
                                        "type": "array",
                                        "description": "A list of data point ids. For example: [0, 1]",
                                        "items": {"type": "integer"},
                                    },
                                },
                                "required": ["action_item_id", "data_point_ids"],
                            },
                        }
                    },
                    "required": ["relationships"],
                },
            },
        ],
        function_call={"name": "report_action_item_relationships"},
    )

    relationships = unpack_function_call_arguments(response)["relationships"]  # type: ignore

    # Convert to mapping of action item index to data point indices
    action_item_to_data_points: Dict[int, List[int]] = {}
    for relationship in relationships:
        action_item_to_data_points[relationship["action_item_id"]] = relationship[
            "data_point_ids"
        ]

    return action_item_to_data_points  # type: ignore
