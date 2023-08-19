from typing import Dict, List
import openai
from src.data import Observation, ActionItem, Topic
from src.llm.utils import unpack_function_call_arguments


def infer_action_items_to_observations_connections(
    feedback_item: str,
    observations: List[Observation],
    action_items: List[ActionItem],
) -> Dict[int, List[int]]:
    """
    Given a feedback item as context, a list of observations, and a list of action items, infer which action items address which observations.
    """

    # Exit if there are no observations or action items
    if len(observations) == 0:
        return {}
    if len(action_items) == 0:
        return {}

    # Create a numbered list of observations and action items
    numbered_observations = ""
    for i, observation in enumerate(observations):
        numbered_observations += f"{i}. {observation.text}\n"

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
                "content": f"Here is a customer's feedback:\n\n{feedback_item}\n\nFrom this feedback, we have the following takeaways:\n\n{numbered_observations}\n\nHere are the action items we have in our backlog:\n\n{numbered_action_items}\n\nFor each action item, report which takeaway(s) the action item helps to address.",
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
                                    "observation_ids": {
                                        "type": "array",
                                        "description": "A list of observation ids. For example: [0, 1]",
                                        "items": {"type": "integer"},
                                    },
                                },
                                "required": ["action_item_id", "observation_ids"],
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

    # Convert to mapping of action item index to observation indices
    action_item_to_observations: Dict[int, List[int]] = {}
    for relationship in relationships:
        action_item_to_observations[relationship["action_item_id"]] = relationship[
            "observation_ids"
        ]

    return action_item_to_observations  # type: ignore


def infer_observation_to_action_items_connections(
    observation: Observation,
    action_items: List[ActionItem],
) -> List[ActionItem]:
    """
    Given a single observation, and a list of action items, infer which subset of action items address the observation.
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
                "content": f"We have the following takeaway from a customer review:\n\n{observation.text}\n\nFor each of the following action items, report if the action item directly addresses the takeaway above:\n\n{numbered_action_items}",
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

    # Convert to mapping of action item index to observation indices
    related_action_items: List[ActionItem] = []
    for i, boolean in enumerate(booleans):
        if boolean:
            related_action_items.append(action_items[i])

    return related_action_items  # type: ignore


def infer_observation_to_topics_connections(
    observation: Observation,
    topics: List[Topic],
) -> List[Topic]:
    """
    Given a single observation, and a list of topics, infer which subset of topics the observation belongs to.
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
                "content": f"We have the following takeaway from a customer review:\n\n{observation.text}\n\nFor each of the following topics, report if the takeaway above belongs to the topic:\n\n{numbered_topics}",
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


def infer_topic_to_observations_connections(
    topic: Topic,
    observations: List[Observation],
) -> List[Observation]:
    """
    Given a single topic, and a list of observations, infer which subset of observations belong to the topic.
    """

    # Exit if there are no observations
    if len(observations) == 0:
        return []

    numbered_observations = ""
    for i, observation in enumerate(observations):
        numbered_observations += f"{i}. {observation.text}\n"

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
                "content": f"For each of the following takeaways, report if the takeaway is talking about the topic '{topic.text}':\n\n{numbered_observations}",
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

    # Convert the booleans to a list of observations
    related_observations: List[Observation] = []
    for i, boolean in enumerate(booleans):
        if boolean:
            related_observations.append(observations[i])

    return related_observations  # type: ignore


def infer_action_item_to_observations_connections(
    action_item: ActionItem,
    observations: List[Observation],
) -> List[Observation]:
    """
    Given a single action_item, and a list of observations, infer which subset of observations are addressed by the action item.
    """

    # Exit if there are no observations
    if len(observations) == 0:
        return []

    numbered_observations = ""
    for i, observation in enumerate(observations):
        numbered_observations += f"{i}. {observation.text}\n"

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
                "content": f"For each of the following takeaways, report if the takeaway can be directly addressed by this action item: '{action_item.text}':\n\n{numbered_observations}",
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

    # Convert the booleans to a list of observations
    related_observations: List[Observation] = []
    for i, boolean in enumerate(booleans):
        if boolean:
            related_observations.append(observations[i])

    return related_observations  # type: ignore
