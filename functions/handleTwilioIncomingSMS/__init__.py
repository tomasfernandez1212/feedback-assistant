import logging
import azure.functions as func

from gremlin_python.driver import client, serializer, protocol
from gremlin_python.driver.protocol import GremlinServerError
import sys, os
import traceback
import asyncio

AZURE_COSMOS_HOST_NAME = os.environ.get("AZURE_COSMOS_HOST_NAME")
AZURE_COSMOS_DB_NAME = os.environ.get("AZURE_COSMOS_DB_NAME")
AZURE_COSMOS_GRAPH_NAME = os.environ.get("AZURE_COSMOS_GRAPH_NAME")
AZURE_COSMOS_DB_KEY = os.environ.get("AZURE_COSMOS_DB_KEY")

if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

client = client.Client(f'wss://{AZURE_COSMOS_HOST_NAME}.gremlin.cosmos.azure.com:443/', 'g',
                        username=f"/dbs/{AZURE_COSMOS_DB_NAME}/colls/{AZURE_COSMOS_GRAPH_NAME}",
                        password=AZURE_COSMOS_DB_KEY,
                        message_serializer=serializer.GraphSONSerializersV2d0()
                        )


def main(req: func.HttpRequest) -> func.HttpResponse:

    logging.info('Python HTTP trigger function processed a request.')

    # Unpack
    logging.info(req)
    logging.info(req.params)

    body = req.params.get('Body')
    from_number = req.params.get('From')
    
    # Log in Function App
    logging.info(f'Received message {body} from {from_number}')

    # Add Human to Graph
    callback = client.submitAsync(f"g.V().hasLabel('human').has('phoneNumber', {from_number})")
    if callback.result().one() is None:
        # The vertex doesn't exist, add it
        callback = client.submitAsync(f"g.addV('human').property('phoneNumber', {from_number})")
        print("Vertex added")
    else:
        print("Vertex already exists")

    # Add Message to Graph
    callback = client.submitAsync(f"g.addV('message').property('text', {body}).property('type', 'human')")

    return func.HttpResponse("Received your message", status_code=200)
