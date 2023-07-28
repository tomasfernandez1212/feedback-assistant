import openai
import logging
import json
from typing import List


class OpenAIInterface:
    def get_satisfaction_score(self, text: str) -> int:
        response = openai.ChatCompletion.create(  # type: ignore
            model="gpt-3.5-turbo-0613",
            messages=[
                {"role": "system", "content": "You are an expert in customer service."},
                {
                    "role": "user",
                    "content": f"What is the following customer's satisfaction score: {text}",
                },
            ],
            functions=[
                {
                    "name": "report_score",
                    "description": "Used to report a quantitative score to the system.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "score": {
                                "type": "integer",
                                "description": "A relative score from 0 to 100.",
                                "minimum": 0,
                                "maximum": 100,
                            },
                        },
                    },
                    "required": ["score"],
                }
            ],
            function_call={"name": "report_score"},
        )

        logging.info("Response: %s", response)  # type: ignore

        score: int = json.loads(response["choices"][0]["message"]["function_call"]["arguments"])["score"]  # type: ignore
        return score  # type: ignore

    def get_list_of_topics(self, text: str) -> list[str]:
        response = openai.ChatCompletion.create(  # type: ignore
            model="gpt-3.5-turbo-0613",
            messages=[
                {
                    "role": "system",
                    "content": """
                    You are an expert in customer service. Your task is to identify the topics that are being discussed in customer's reviews, feedback, and in conversations with us. 
                 
                    For example, if a customer says "So glad to have tried the Souvla in the Marina. Parking is more reasonable, indoor and outdoor seating is plenty, and the food is just as good. I often get the black bean vegan “lamb” option in the gyro wrap and my wife gets their chicken salad. The mandarin oranges in the salad are SO good, you’ve gotta try it once. We also get the Greek fries, which are equally as delicious. And when you get to enjoy the meal with your pup in their sunny parklet, you won’t want to leave."
                 
                    You would identify the following topics: ["Reasonable Parking", "Plenty of Seating", "Good Food", "Black Bean Vegan 'Lamb'", "Chicken Salad", "Delicious Mandarin Oranges", "Delicious Greek Fries", "Sunny Parklet", "Dog Friendly"]
                 
                    The goal is to infer facts about the customer's experience.""",
                },
                {
                    "role": "user",
                    "content": f"What topics are being discussed here: {text}",
                },
            ],
            functions=[
                {
                    "name": "report_topics",
                    "description": "Used to report topics to the system.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "topics": {
                                "type": "array",
                                "description": "A list of topics.",
                                "items": {"type": "string"},
                            },
                        },
                    },
                    "required": ["topics"],
                }
            ],
            function_call={"name": "report_topics"},
        )

        logging.info("Response: %s", response)  # type: ignore

        list_of_topics: List[str] = json.loads(response["choices"][0]["message"]["function_call"]["arguments"])["topics"]  # type: ignore
        return list_of_topics  # type: ignore

    def get_embedding(self, text: str) -> List[float]:
        response = openai.Embedding.create(input=text, model="text-embedding-ada-002")  # type: ignore
        embeddings = response["data"][0]["embedding"]  # type: ignore
        return embeddings  # type: ignore
