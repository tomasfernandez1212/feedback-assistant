
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

_gremlin_cleanup_graph = "g.V().drop()"


_gremlin_insert_vertices = [
    "g.addV('messenger').property('phoneNumber', '19547404574')",
    "g.addV('messenger').property('phoneNumber', '17132584727')",
    "g.addV('ai').property('version', '0.1')",
    "g.addV('message').property('text', 'I didn't like it.').property('type', 'human')",
    "g.addV('aiMessage').property('text', 'Thank you for your message. Can you elaborate?').property('type', 'ai')"
]

_gremlin_insert_edges = [
    "g.V('thomas').addE('knows').to(g.V('mary'))",
    "g.V('thomas').addE('knows').to(g.V('ben'))",
    "g.V('ben').addE('knows').to(g.V('robin'))"
]


def print_status_attributes(result):
    # This logs the status attributes returned for successful requests.
    # See list of available response status attributes (headers) that Gremlin API can return:
    #     https://docs.microsoft.com/en-us/azure/cosmos-db/gremlin-headers#headers
    #
    # These responses includes total request units charged and total server latency time.
    # 
    # IMPORTANT: Make sure to consume ALL results returend by cliient tothe final status attributes
    # for a request. Gremlin result are stream as a sequence of partial response messages
    # where the last response contents the complete status attributes set.
    #
    # This can be 
    print("\tResponse status_attributes:\n\t{0}".format(result.status_attributes))

def cleanup_graph(client):
    print("\n> {0}".format(_gremlin_cleanup_graph))
    callback = client.submitAsync(_gremlin_cleanup_graph)
    if callback.result() is not None:
        callback.result().all().result() 
    print("\n")
    print_status_attributes(callback.result())
    print("\n")


def insert_vertices(client):
    for query in _gremlin_insert_vertices:
        print("\n> {0}\n".format(query))
        callback = client.submitAsync(query)
        if callback.result() is not None:
            print("\tInserted this vertex:\n\t{0}".format(
                callback.result().all().result()))
        else:
            print("Something went wrong with this query: {0}".format(query))
        print("\n")
        print_status_attributes(callback.result())
        print("\n")

    print("\n")


def insert_edges(client):
    for query in _gremlin_insert_edges:
        print("\n> {0}\n".format(query))
        callback = client.submitAsync(query)
        if callback.result() is not None:
            print("\tInserted this edge:\n\t{0}\n".format(
                callback.result().all().result()))
        else:
            print("Something went wrong with this query:\n\t{0}".format(query))
        print_status_attributes(callback.result())
        print("\n")

    print("\n")


client = client.Client(f'wss://{AZURE_COSMOS_HOST_NAME}.gremlin.cosmos.azure.com:443/', 'g',
                        username=f"/dbs/{AZURE_COSMOS_DB_NAME}/colls/{AZURE_COSMOS_GRAPH_NAME}",
                        password=AZURE_COSMOS_DB_KEY,
                        message_serializer=serializer.GraphSONSerializersV2d0()
                        )

print("Welcome to Azure Cosmos DB + Gremlin on Python!")

# Drop the entire Graph
input("We're about to drop whatever graph is on the server. Press any key to continue...")
cleanup_graph(client)

# Insert all vertices
input("Let's insert some vertices into the graph. Press any key to continue...")
insert_vertices(client)

# Create edges between vertices
input("Now, let's add some edges between the vertices. Press any key to continue...")
insert_edges(client)