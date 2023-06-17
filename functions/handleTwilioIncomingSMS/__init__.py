import logging
import azure.functions as func

def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')

    # read incoming parameters
    body = req.params.get('Body')
    from_number = req.params.get('From')
    
    # print the incoming message body to the Azure logs
    logging.info(f'Received message {body} from {from_number}')

    # return the response
    return func.HttpResponse("Received your message", status_code=200)
