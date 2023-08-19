# Feedback Assistant
Feedback Assistant is a tool designed to draw meaningful insights from feedback. 

The current focus is on restaurant management teams, but this idea can be expanded to any setting where feedback is used. For example, in other consumer facing small business settings, in mid size and large corporations where feedback is given to employees, feedback for teachers and students in academic settings, feedback for executives at large institutions wanting to gauge public sentiment, product teams, and so forth.  

# Data 

Currently, data from Yelp reviews is used, but in the future this can be expanded to other review platforms and even new forms of feedback submission such as a messaging system. For example, at a restaurant you could have QR codes that lead to a text messaging system where you provide feedback and in realtime an LLM system responds and gathers more details. 

# Backend 

The backend consists of a an Azure Cosmos DB Graph Database, Azure Functions, and Azure Service Bus Messaging Queues. 

Data ingestion for reviews is processed by an azure function that is triggered from a periodic timer. This timer is currently set to a low periodicity (Chron schedule: 0 0 0 1 1 *) to save costs during development, but in the future this can be set to high frequency (Every minute: 0 */1 * * * *) as an example. 

When data is added to the Cosmos DB, it triggers a function (GraphChangeRouter) which is used to route changes to different queues depending on the type of change that occured. 

Each queue then feeds other functions that have the core logic of the application. 

"Reviews" create "Feedback Items", from "Feedback Items" we draw "Observations", "Observations" are scored by different metrics, "Observations" are tagged with "Topics", "Action Items" are created from "Observations" and "Feedback Items". 

When these entities are created in the graph database, they are also combined by logical edges. For example, action items "address" certain feedback items, topics, and observations. 


# Frontend

TBD