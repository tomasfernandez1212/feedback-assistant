import openai
from typing import List
from src.data import Topic, DataPoint

from src.llm.utils import unpack_function_call_arguments


def generate_topics(
    feedback_item: str,
    data_points: List[DataPoint],
    existing_topics: List[Topic],
) -> List[Topic]:
    """
    Given a feedback item, a list of data points, and a list of existing topics, return a list of new topics to add.
    """
    numbered_data_points = ""
    for i, data_point in enumerate(data_points):
        numbered_data_points += f"{i}. {data_point.text}\n"

    numbered_existing_topics = ""
    for i, topic_text in enumerate(existing_topics):
        numbered_existing_topics += f"{i}. {topic_text.text}\n"

    response = openai.ChatCompletion.create(  # type: ignore
        model="gpt-3.5-turbo-0613",
        messages=[
            {
                "role": "system",
                "content": "You are an expert in customer service. Your task is to interpret customer's reviews, feedback, and conversations with us to infer topics that are being discussed. ",
            },
            {
                "role": "user",
                "content": f"Here is a customer's feedback:\n\n{feedback_item}\n\nFrom this feedback, we have the following takeaways:\n\n{numbered_data_points}\n\nHere are the existing topics identified from other feedback items:\n\n{numbered_existing_topics}\n\nWhat topics do we need to add? Don't add topics if the existing topics already reasonably cover the feedback and its takeaways. When you do decide to add a topic, make sure the topic is neutral. For example, 'The service was super quick!!' is about the 'Speed of Service'",
            },
        ],
        functions=[
            {
                "name": "report_topics",
                "description": "This function is used to add more topics to the list. It accepts an array of topics as strings.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "topics": {
                            "type": "array",
                            "description": "A list of topics. For example: ['Checkout process.', 'Payment options.', 'Outdoor Patio.']",
                            "items": {"type": "string"},
                        }
                    },
                    "required": ["topics"],
                },
            },
        ],
        function_call={"name": "report_topics"},
    )

    new_topics_text: List[str] = unpack_function_call_arguments(response)["topics"]  # type: ignore

    new_topics: List[Topic] = []
    for topic_text in new_topics_text:
        topic = Topic(text=topic_text)
        new_topics.append(topic)

    return new_topics  # type: ignore
