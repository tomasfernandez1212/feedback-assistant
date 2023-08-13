from typing import Dict, List
import openai
from src.data import DataPoint, ActionItem, Topic
from src.llm.utils import unpack_function_call_arguments


def infer_action_items_to_data_points_connections(
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


def infer_data_point_to_action_items_connections(
    data_point: DataPoint,
    action_items: List[ActionItem],
) -> List[ActionItem]:
    """
    Given a single data point, and a list of action items, infer which subset of action items address the data point.
    """

    # Exit if there are no action items
    if len(action_items) == 0:
        return []

    numbered_action_items = ""
    for i, action_item in enumerate(action_items):
        numbered_action_items += f"{i}. {action_item.text}\n"

    response = openai.ChatCompletion.create(  # type: ignore
        model="gpt-3.5-turbo-0613",
        temperature=0.0,
        messages=[
            {
                "role": "system",
                "content": "You are an expert in customer service.",
            },
            {
                "role": "user",
                "content": f"We have the following takeaway from a customer review:\n\n{data_point.text}\n\nFor each of the following action items, report if the action item directly addresses the takeaway above:\n\n{numbered_action_items}",
            },
        ],
        functions=[
            {
                "name": "report_action_item",
                "description": "This function is used report whether each action item directly addresses the takeaway.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "addresses": {
                            "type": "array",
                            "description": "A list of booleans. Do not add any comentary. Only report with booleans. For example, [true, false, true].",
                            "items": {
                                "type": "boolean",
                                "description": "Whether the action item directly addresses the takeaway.",
                            },
                        }
                    },
                    "required": ["addresses"],
                },
            },
        ],
        function_call={"name": "report_action_item"},
    )

    booleans = unpack_function_call_arguments(response)["addresses"]  # type: ignore

    # Convert to mapping of action item index to data point indices
    related_action_items: List[ActionItem] = []
    for i, boolean in enumerate(booleans):
        if boolean:
            related_action_items.append(action_items[i])

    return related_action_items  # type: ignore


def infer_data_point_to_topics_connections(
    data_point: DataPoint,
    topics: List[Topic],
) -> List[Topic]:
    """
    Given a single data point, and a list of topics, infer which subset of topics the data point belongs to.
    """

    # Exit if there are no topics
    if len(topics) == 0:
        return []

    numbered_topics = ""
    for i, topic in enumerate(topics):
        numbered_topics += f"{i}. {topic.text}\n"

    response = openai.ChatCompletion.create(  # type: ignore
        model="gpt-3.5-turbo-0613",
        messages=[
            {
                "role": "system",
                "content": "You are an expert in customer service.",
            },
            {
                "role": "user",
                "content": f"We have the following takeaway from a customer review:\n\n{data_point.text}\n\nFor each of the following topics, report if the takeaway above belongs to the topic:\n\n{numbered_topics}",
            },
        ],
        functions=[
            {
                "name": "report_topic",
                "description": "This function is used report whether the takeaway belongs to each topic.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "belongs_to": {
                            "type": "array",
                            "description": "A list of booleans. Do not add any comentary. Only report with booleans. For example, [true, false, true].",
                            "items": {
                                "type": "boolean",
                                "description": "Whether the takeaway belongs to the topic.",
                            },
                        }
                    },
                    "required": ["belongs_to"],
                },
            },
        ],
        function_call={"name": "report_topic"},
    )

    booleans = unpack_function_call_arguments(response)["belongs_to"]  # type: ignore

    # Convert the booleans to a list of topics
    related_topics: List[Topic] = []
    for i, boolean in enumerate(booleans):
        if boolean:
            related_topics.append(topics[i])

    return related_topics  # type: ignore


def infer_topic_to_data_points_connections(
    topic: Topic,
    data_points: List[DataPoint],
) -> List[DataPoint]:
    """
    Given a single topic, and a list of data points, infer which subset of data points belong to the topic.
    """

    # Exit if there are no data points
    if len(data_points) == 0:
        return []

    numbered_data_points = ""
    for i, data_point in enumerate(data_points):
        numbered_data_points += f"{i}. {data_point.text}\n"

    response = openai.ChatCompletion.create(  # type: ignore
        model="gpt-3.5-turbo-0613",
        temperature=0.0,
        messages=[
            {
                "role": "system",
                "content": "You are an expert in customer service. Your task is to discern if a given takeaway directly discusses the specified topic. Ensure you look for clear, explicit, and literal mentions or indications of the topic within each takeaway. Avoid making indirect or tangential associations. For example, if the topic is 'Ambiance', and one takeaway is 'The lights were too bright.', that's a direct mention. But if another takeaway is 'The apple pie was delicious.', that does not explicitly discuss 'Ambiance' even if ambiance might influence the dining experience.",
            },
            {
                "role": "user",
                "content": f"For each of the following takeaways, report if the takeaway is talking about the topic '{topic.text}':\n\n{numbered_data_points}",
            },
        ],
        functions=[
            {
                "name": "report_takeaways",
                "description": f"Use this to report whether each takeaway is talking about the topic '{topic.text}'.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "belongs_to": {
                            "type": "array",
                            "description": "A list of booleans. Do not add any comentary. Only report with booleans. For example, [true, false, true].",
                            "items": {
                                "type": "boolean",
                                "description": f"Indicates whether the takeaway is talking about the topic of '{topic.text}'.",
                            },
                        }
                    },
                    "required": ["belongs_to"],
                },
            },
        ],
        function_call={"name": "report_takeaways"},
    )

    booleans = unpack_function_call_arguments(response)["belongs_to"]  # type: ignore

    # Convert the booleans to a list of data points
    related_data_points: List[DataPoint] = []
    for i, boolean in enumerate(booleans):
        if boolean:
            related_data_points.append(data_points[i])

    return related_data_points  # type: ignore


def infer_action_item_to_data_points_connections(
    action_item: ActionItem,
    data_points: List[DataPoint],
) -> List[DataPoint]:
    """
    Given a single action_item, and a list of data points, infer which subset of data points are addressed by the action item.
    """

    # Exit if there are no data points
    if len(data_points) == 0:
        return []

    numbered_data_points = ""
    for i, data_point in enumerate(data_points):
        numbered_data_points += f"{i}. {data_point.text}\n"

    response = openai.ChatCompletion.create(  # type: ignore
        model="gpt-3.5-turbo-0613",
        temperature=0.0,
        messages=[
            {
                "role": "system",
                "content": "You are an expert in customer service. Your task is to discern if a given takeaway drawn from customers' feedback can be directly addressed by a provided action item.",
            },
            {
                "role": "user",
                "content": f"For each of the following takeaways, report if the takeaway can be directly addressed by this action item: '{action_item.text}':\n\n{numbered_data_points}",
            },
        ],
        functions=[
            {
                "name": "report_takeaways",
                "description": f"Use this to report whether each takeaway can be directly addressed by this action item: '{action_item.text}'.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "addressed": {
                            "type": "array",
                            "description": "A list of booleans. Do not add any comentary. Only report with booleans. For example, [true, false, true].",
                            "items": {
                                "type": "boolean",
                                "description": f"Indicates whether the takeaway can be directly addressed by the action item: '{action_item.text}'.",
                            },
                        }
                    },
                    "required": ["addressed"],
                },
            },
        ],
        function_call={"name": "report_takeaways"},
    )

    booleans = unpack_function_call_arguments(response)["addressed"]  # type: ignore

    # Convert the booleans to a list of data points
    related_data_points: List[DataPoint] = []
    for i, boolean in enumerate(booleans):
        if boolean:
            related_data_points.append(data_points[i])

    return related_data_points  # type: ignore
