import openai
import logging
import json


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
