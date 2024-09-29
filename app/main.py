from fastapi import FastAPI
import gradio as gr
import time
from openai import AzureOpenAI
import os
from dotenv import dotenv_values
from azure.core.exceptions import AzureError
from azure.core.credentials import AzureKeyCredential
import uuid

#Cosmos DB imports
from azure.cosmos import CosmosClient
# from azure.cosmos.aio import CosmosClient as CosmosAsyncClient
# from azure.cosmos import PartitionKey, exceptions

app = FastAPI()

OPENAI_API_KEY = os.getenv('AZURE_OPENAI_KEY')
OPENAI_API_ENDPOINT = os.getenv('AZURE_OPENAI_ENDPOINT')
OPENAI_API_VERSION = os.getenv('AZURE_OPENAI_VERSION') # at the time of authoring, the api version is 2024-02-01
COMPLETIONS_MODEL_DEPLOYMENT_NAME = os.getenv('AZURE_OPENAI_COMPLETIONS_DEPLOYMENT')
EMBEDDING_MODEL_DEPLOYMENT_NAME = os.getenv('AZURE_OPENAI_EMBEDDINGS_DEPLOYMENT')
COSMOSDB_NOSQL_ACCOUNT_KEY = os.getenv('COSMOSDB_KEY')
COSMOSDB_NOSQL_ACCOUNT_ENDPOINT = os.getenv('COSMOSDB_URI')

# Initialize the Azure OpenAI client
AOAI_client = AzureOpenAI(api_key=OPENAI_API_KEY, azure_endpoint=OPENAI_API_ENDPOINT, api_version=OPENAI_API_VERSION)

#Intialize Cosmosclient and container client
cosmos_client = CosmosClient(url=COSMOSDB_NOSQL_ACCOUNT_ENDPOINT, credential=COSMOSDB_NOSQL_ACCOUNT_KEY)

#create database
DATABASE_NAME = "vector-nosql-db"
db= cosmos_client.create_database_if_not_exists(
    id=DATABASE_NAME
)

CONTAINER_NAME = "vector-nosql-cont"
CACHE_CONTAINER_NAME = "vector-nosql-cache"

container = db.get_container_client(CONTAINER_NAME)
cache_container = db.get_container_client(CACHE_CONTAINER_NAME)



# function to generate embeddings
def generate_embeddings(text):
    '''
    Generate embeddings from string of text.
    This will be used to vectorize data and user input for interactions with Azure OpenAI.
    '''
    response = AOAI_client.embeddings.create(input=text, model=EMBEDDING_MODEL_DEPLOYMENT_NAME)
    embeddings =response.model_dump()
    time.sleep(0.5) 
    return embeddings['data'][0]['embedding']

# Simple function to assist with vector search
def vector_search(query, num_results=5):
    query_embedding = generate_embeddings(query)
    results = container.query_items(
            query='SELECT TOP @num_results c.content, c.title, c.category, VectorDistance(c.contentVector,@embedding) AS SimilarityScore  FROM c ORDER BY VectorDistance(c.contentVector,@embedding)',
            parameters=[
                {"name": "@embedding", "value": query_embedding}, 
                {"name": "@num_results", "value": num_results} 
            ],enable_cross_partition_query=True)    #correct this
    return results

# function to get chat history.
def get_chat_history(container, completions=3):
    results = container.query_items(
        query= '''
        SELECT TOP @completions *
        FROM c
        ORDER BY c._ts DESC
        ''',
        parameters=[
            {"name": "@completions", "value": completions},
        ],enable_cross_partition_query=True)
    results = list(results)
    return results

#function to ground the model with prompts and system instructions.
def generate_completion(vector_search_results, user_prompt, chat_history):
    system_prompt = '''
    You are an intelligent assistant for Microsoft Azure services.
    You are designed to provide helpful answers to user questions about Azure services given the information about to be provided.
        - Only answer questions related to the information provided below, provide at least 3 clear suggestions in a list format.
        - Write two lines of whitespace between each answer in the list.
        - If you're unsure of an answer, you can say ""I don't know"" or ""I'm not sure"" and recommend users search themselves."
        - Only provide answers that have products that are part of Microsoft Azure and part of these following prompts.
    '''

    messages=[{"role": "system", "content": system_prompt}]
    
        #chat history
    for chat in chat_history:
        messages.append({'role': 'user', 'content': chat['prompt'] + " " + chat['completion']})

    for item in vector_search_results:
        messages.append({"role": "system", "content": item['content']})
    messages.append({"role": "user", "content": user_prompt})
    response = AOAI_client.chat.completions.create(model=COMPLETIONS_MODEL_DEPLOYMENT_NAME, messages=messages,temperature=0)
    
    return response

#function to cache response
def cache_response(container, user_prompt, prompt_vectors, response):
    # Create a dictionary representing the chat document
    chat_document = {
        'id':  str(uuid.uuid4()),  
        'prompt': user_prompt,
        'completion': response.choices[0].message.content,
        'completionTokens': str(response.usage.completion_tokens),
        'promptTokens': str(response.usage.prompt_tokens),
        'totalTokens': str(response.usage.total_tokens),
        'model': response.model,
        'vector': prompt_vectors
    }
    # Insert the chat document into the Cosmos DB container
    container.create_item(body=chat_document)
    print("item inserted into cache.", chat_document)


# Perform a vector search on the Cosmos DB container to get cached content
def get_cache(container, vectors, similarity_score=0.0, num_results=5):
    # Execute the query
    results = container.query_items(
        query= '''
        SELECT TOP @num_results *
        FROM c
        WHERE VectorDistance(c.vector,@embedding) > @similarity_score
        ORDER BY VectorDistance(c.vector,@embedding)
        ''',
        parameters=[
            {"name": "@embedding", "value": vectors},
            {"name": "@num_results", "value": num_results},
            {"name": "@similarity_score", "value": similarity_score},
        ],
        enable_cross_partition_query=True, populate_query_metrics=True)
    results = list(results)
    return results

# method to perform chat completion
def chat_completion(cache_container,user_input):
   # container = db.get_container_client(CONTAINER_NAME)
    cache_container = db.get_container_client(CACHE_CONTAINER_NAME)
    #while user_input.lower() != "end":
    user_embeddings = generate_embeddings(user_input)

   # Query the chat history cache first to see if this question has been asked before
    cache_results = get_cache(container = cache_container, vectors = user_embeddings, similarity_score=0.99, num_results=1)
    if len(cache_results) > 0:
        print("Cached Result\n")
        return cache_results[0]['completion'], True
   
    else: 

      print("New result\n")
      search_results = vector_search(user_input)
      #chat history
      chat_history = get_chat_history(cache_container, 3)

      completions_results = generate_completion(search_results, user_input,chat_history)
      print("\n")
      print("Caching response \n")
      #cache the response
      cache_response(cache_container, user_input, user_embeddings, completions_results)

      return completions_results.choices[0].message.content, False




 # create a simple chat app using gradio

chat_history = []
with gr.Blocks() as demo:
    chatbot = gr.Chatbot(label="Azure Assistant")
    
    msg = gr.Textbox(label="Ask me about Azure Services!")
    clear = gr.Button("Clear")

    def user(user_message, chat_history):
        # Create a timer to measure the time it takes to complete the request
        start_time = time.time()
        # Get LLM completion
        response_payload, cached = chat_completion(cache_container, user_message)
        # Stop the timer
        end_time = time.time()
        elapsed_time = round((end_time - start_time) * 1000, 2)
        #response = response_payload
        print(response_payload)
        # Append user message and response to chat history
        details = f"\n (Time: {elapsed_time}ms)"
        if cached:
         details += " (Cached)"
        chat_history.append([user_message, response_payload + details])
        
        return gr.update(value=""), chat_history
    
    msg.submit(user, [msg, chatbot], [msg, chatbot], queue=False)

    clear.click(lambda: None, None, chatbot, queue=False)


app = gr.mount_gradio_app(app, demo, path="/")
