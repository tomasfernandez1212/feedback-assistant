import azure.functions as func
import logging

from gremlin_python.driver import client, serializer, protocol
from gremlin_python.driver.protocol import GremlinServerError
import sys, os
import traceback
import asyncio

from dotenv import load_dotenv
load_dotenv()

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

    if AZURE_COSMOS_HOST_NAME is None:
        raise Exception("AZURE_COSMOS_HOST_NAME is not set")

    # Unpack
    logging.info(req)
    logging.info(req.params)

    body = req.params.get('Body')
    from_number = req.params.get('From')
    
    # Log in Function App
    logging.info(f'Received message {body} from {from_number}')

    # Add Human to Graph
    callback = client.submitAsync(f"g.V().hasLabel('human').has('phoneNumber', '{from_number}')")
    human_already_registered = callback.result().one() is None
    logging.info(f"Human already registered: {human_already_registered}")
    if human_already_registered:
        logging.info(f"Human already in graph")
    else:
        callback = client.submitAsync(f"g.addV('human').property('phoneNumber', '{from_number}').property('pk', 'pk')")
        logging.info(f"Added human to graph")

    # Add Message to Graph
    callback = client.submitAsync(f"g.addV('message').property('text', '{body}').property('type', 'human').property('pk', 'pk')")
    logging.info(f"Added message to graph")

    return func.HttpResponse("Received your message", status_code=200)
