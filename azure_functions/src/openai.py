import openai
import json
from typing import List, Dict, Any, Tuple
from enum import Enum
from src.data.scores import Score
from pydantic import BaseModel


class ScoreConfig(BaseModel):
    name: str
    range_min: int
    range_middle: int
    range_max: int
    range_min_description: str
    range_middle_description: str
    range_max_description: str
    var_name: str = ""

    def model_post_init(self, __context: Any) -> None:
        if self.var_name == "":
            self.var_name: str = self.name.lower().replace(" ", "_")
        return super().model_post_init(__context)


class ScoreType(Enum):
    SATISFACTION = ScoreConfig(
        name="Satisfaction",
        range_min=0,
        range_middle=50,
        range_max=100,
        range_min_description="very negative",
        range_middle_description="neutral",
        range_max_description="very positive",
    )
    SPECIFICITY = ScoreConfig(
        name="Specificity",
        range_min=0,
        range_middle=50,
        range_max=100,
        range_min_description="not specific (lacking constructive detail)",
        range_middle_description="somewhat specific",
        range_max_description="very specific (highly constructive feedback)",
    )
    BUSINESS_IMPACT = ScoreConfig(
        name="Business Impact",
        range_min=0,
        range_middle=50,
        range_max=100,
        range_min_description="not impactful on business outcomes",
        range_middle_description="somewhat important",
        range_max_description="high severity (very impactful on business outcomes)",
    )


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

        score: int = json.loads(response["choices"][0]["message"]["function_call"]["arguments"])["score"]  # type: ignore
        return score  # type: ignore

    def get_data_points_text(self, text: str) -> list[str]:
        response = openai.ChatCompletion.create(  # type: ignore
            model="gpt-3.5-turbo-0613",
            messages=[
                {
                    "role": "system",
                    "content": """
                    You are an expert in customer service. Your task is to interpret customer's reviews, feedback, and conversations with us to infer facts about their experience. 
                 
                    For example, if a customer says "A fun Greek spot for a quick bite -- located right on Divisadero, it looks a bit hole-in-the-wall but has a lovely back patio with heaters. You order at the front and they give you a number, so it's a fast-casual vibe. The staff are very sweet and helpful, too. There aren't large tables, so would recommend going with a smaller group. The food is fresh and healthy, with a selection of salads and gyros! The real star of the show is dessert. The gryo is a little hard to eat IMHO -- I got the white sweet potato and ended up just using a fork and knife, and I didn't think the flavor was anything too memorable. The fries are SO good -- crispy on the outside, soft on the inside. My absolute favorite thing was the Baklava Crumbles on the frozen Greek yoghurt -- literally... FIRE. The yoghurt is tart and the baklava is sweet and I am obsessed. I'd come back for that alone.",

                    You would identify: ["The customer visited our location on Divisadero.", "The exterior of the restaurant may seem modest or unassuming, as described as 'hole-in-the-wall'.", "The restaurant has a back patio equipped with heaters.", "The ordering system is more casual, with customers placing orders at the front and given a number to wait for their food.", "The staff of the restaurant made a positive impression on the customer, being described as 'sweet' and 'helpful'.", "The restaurant is not suitable for larger groups due to the lack of large tables.", "The food offered is fresh and healthy, including options like salads and gyros.", "The customer found the gyro hard to eat and not particularly flavorful, specifically mentioning a white sweet potato gyro.", "The restaurant serves high-quality fries that are crispy on the outside and soft on the inside.", "The restaurant offers a dessert option that involves Baklava Crumbles on frozen Greek yogurt.", "The customer was highly impressed with the Baklava Crumbles on frozen Greek yogurt, describing it as 'FIRE' and expressing an eagerness to revisit the restaurant for this dessert.", "The customer found the combination of tart yogurt and sweet baklava to be very satisfying."]

                    The goal is to infer data points from customers' experiences.""",
                },
                {
                    "role": "user",
                    "content": f"What can we infer here: {text}",
                },
            ],
            functions=[
                {
                    "name": "report_interpretation",
                    "description": "Used to report interpretations to the system.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "data_points": {
                                "type": "array",
                                "description": "A list of interpretations.",
                                "items": {"type": "string"},
                            },
                        },
                    },
                    "required": ["data_points"],
                }
            ],
            function_call={"name": "report_interpretation"},
        )

        list_of_data_points: List[str] = json.loads(response["choices"][0]["message"]["function_call"]["arguments"])["data_points"]  # type: ignore
        return list_of_data_points  # type: ignore

    def _generate_score_properties_and_required(
        self,
        score_types: List[ScoreType],
    ) -> Tuple[Dict[str, Dict[str, Any]], List[str]]:
        properties: Dict[str, Dict[str, Any]] = {}
        required: List[str] = []

        for score_type in score_types:
            properties.update(
                {
                    f"{score_type.value.var_name}_score": {
                        "type": "integer",
                        "description": f"The customer's {score_type.value.name} Score regarding that statement. It is a relative score from {score_type.value.range_min} to {score_type.value.range_max} where {score_type.value.range_min} is {score_type.value.range_min_description}, {score_type.value.range_middle} is {score_type.value.range_middle_description}, and {score_type.value.range_max} is {score_type.value.range_max_description}.",
                        "minimum": score_type.value.range_min,
                        "maximum": score_type.value.range_max,
                    },
                    f"{score_type.value.var_name}_explanation": {
                        "type": "string",
                        "description": "An explanation for the provided score.",
                    },
                }
            )
            required.append(f"{score_type.value.var_name}_score")
            required.append(f"{score_type.value.var_name}_explanation")

        return (properties, required)

    def score_data_point(
        self, data_point: str, feedback_item: str, score_types: List[ScoreType]
    ) -> List[Score]:
        model_name = "gpt-3.5-turbo-0613"

        messages = [
            {
                "role": "system",
                "content": "You are an expert in customer service. Your task is to report a score.",
            },
            {
                "role": "user",
                "content": f"""Here is something a customer said about their experience with us:\n{feedback_item}\n\nFrom this feedback, we have the following takeaway:\n{data_point}\n\nFrom that takeaway, report the customer's scores on a continuous scale.""",
            },
        ]

        properties, required = self._generate_score_properties_and_required(score_types)

        functions = [
            {
                "name": "report_scores",
                "description": "Used to report the requested scores.",
                "parameters": {
                    "type": "object",
                    "properties": properties,
                    "required": required,
                },
            }
        ]

        function_call = {"name": "report_scores"}

        response = openai.ChatCompletion.create(  # type: ignore
            model=model_name,
            messages=messages,
            functions=functions,
            function_call=function_call,
        )

        result = json.loads(response["choices"][0]["message"]["function_call"]["arguments"])  # type: ignore

        scores: List[Score] = []
        for score_type in score_types:
            score = Score(
                name=score_type.value.name,
                score=result[score_type.value.var_name + "_score"],
                explanation=result[score_type.value.var_name + "_explanation"],
            )
            scores.append(score)

        return scores

    def get_embedding(self, text: str) -> List[float]:
        response = openai.Embedding.create(input=text, model="text-embedding-ada-002")  # type: ignore
        embeddings = response["data"][0]["embedding"]  # type: ignore
        return embeddings  # type: ignore

    def get_topic_from_data_points(
        self, data_points: List[str], limit_points: int = 15
    ) -> str:
        response = openai.ChatCompletion.create(  # type: ignore
            model="gpt-3.5-turbo-0613",
            messages=[
                {
                    "role": "system",
                    "content": """
                    You are an expert in customer service. Your task is to identify the a common topic among a list of data points from customer's reviews, feedback, and in conversations with us. 
                 
                    For example, given these data points ["Good Food", "Black Bean Vegan 'Lamb'", "Chicken Salad", "Delicious Mandarin Oranges", "Delicious Greek Fries"]
                 
                    You would identify a single topic that encapsulates the theme of these data points: "Delicious Food"
                 
                    The goal is to summarize these data point.""",
                },
                {
                    "role": "user",
                    "content": f"What is the overarching topic from these data points: {data_points[:limit_points]}",
                },
            ],
            functions=[
                {
                    "name": "report_topic",
                    "description": "Used to report a topic to the system.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "topic": {
                                "type": "string",
                                "description": "A topic.",
                            },
                        },
                    },
                    "required": ["topic"],
                }
            ],
            function_call={"name": "report_topic"},
        )

        topic: str = json.loads(response["choices"][0]["message"]["function_call"]["arguments"])["topic"]  # type: ignore
        return topic  # type: ignore
