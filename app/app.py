import openai
from openai import AzureOpenAI
import streamlit as st
from streamlit_js_eval import streamlit_js_eval
import time
import os
from io import StringIO
from dotenv import load_dotenv



# load_dotenv()  # take environment variables from .env.

client = AzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),  
    api_version="2024-02-15-preview",
    azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    )

azureOpenAIAssistantId =  os.getenv("AZURE_OPENAI_ASSISTANT_ID")

if "start_chat" not in st.session_state:
    st.session_state.start_chat = False
if "thread_id" not in st.session_state:
    st.session_state.thread_id = None
if "fileId" not in st.session_state:
    st.session_state.fileId = None
if "deleteFile" not in st.session_state:
    st.session_state.deleteFile = True

st.set_page_config(page_title="CustomGPT-Assistant", page_icon=":speech_balloon:")

st.sidebar.image(os.getenv("LOGO_IMAGE_URL"))
st.sidebar.header("Assistant Setup")
st.sidebar.text("Assistant Name: " + os.getenv("AZURE_OPENAI_ASSISTANT_NAME"))
st.sidebar.text("Assistant ID: " + azureOpenAIAssistantId)
st.sidebar.text("Assistant Instructions: " + os.getenv("AZURE_OPENAI_ASSISTANT_INSTRUCTIONS"))
on = st.sidebar.checkbox("Code Interpreter", value=True, key=None, help=None, on_change=None, args=None, kwargs=None, disabled=True, label_visibility="visible")


st.image(os.getenv("LOGO_IMAGE_URL"))
st.title("Lendi Assistant App")
# st.divider()
# st.write("This is a demo of the OpenAI GPT-4 model using the OpenAI Assistants API. This is a beta feature and is subject to change. Please use with caution")
# st.divider()


#adding a file uploader
input_file = st.sidebar.file_uploader("Please choose a file")
if st.session_state.fileId is None and input_file is not None:    
        # Upload a file with an "assistants" purpose
        file_bytes = input_file.getvalue()
        file = client.files.create(
            file = (input_file.name, file_bytes),
            purpose='assistants'
        )        
        st.session_state.fileId = file.id

        # Assign File Id to Assistant using file ID       
        assistant = client.beta.assistants.update(
            assistant_id=azureOpenAIAssistantId,
            name="Finance Assistant",
            instructions="You are a financial assistant. You help users get relevant insights from structured data",
            file_ids= [file.id],
            tools= [ 
                {"type": "code_interpreter"
                } 
            ]
        ) 
if(st.session_state.fileId is not None):
    input_file.close()
    st.session_state.deleteFile = st.sidebar.toggle("Delete File after Chat", value=False, key=None, help=None, on_change=None, args=None, kwargs=None, disabled=False, label_visibility="visible")
    st.sidebar.text("File Id:" + st.session_state.fileId)    
    st.sidebar.text("File Uploaded: " + input_file.name)

if st.button(":broom: Clear Chat "):
    st.session_state.messages = []  # Clear the chat history
    st.session_state.start_chat = False  # Reset the chat state
    st.session_state.thread_id = None

if st.button(":robot_face: Start Chatting"):
    st.session_state.start_chat = True
    thread = client.beta.threads.create()
    st.session_state.thread_id = thread.id  

if st.session_state.start_chat:
    if "openai_model" not in st.session_state:
        st.session_state.openai_model = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("Type your question here"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        client.beta.threads.messages.create(
                thread_id=st.session_state.thread_id,
                role="user",
                content=prompt
            )
        
        run = client.beta.threads.runs.create(
            thread_id=st.session_state.thread_id,
            assistant_id=azureOpenAIAssistantId
        )

        while run.status != 'completed':
            # time.sleep(1)
            run = client.beta.threads.runs.retrieve(
                thread_id=st.session_state.thread_id,
                run_id=run.id
            )
        messages = client.beta.threads.messages.list(
            thread_id=st.session_state.thread_id
        )

        # Process and display assistant messages
        assistant_messages_for_run = [
            message for message in messages 
            if message.run_id == run.id and message.role == "assistant"
        ]
        for message in assistant_messages_for_run:
            st.session_state.messages.append({"role": "assistant", "content": message.content[0].text.value})
            with st.chat_message("assistant"):
                st.markdown(message.content[0].text.value)


 

if st.sidebar.button("Reset Chat", type="primary"):
    streamlit_js_eval(js_expressions="parent.window.location.reload()")
    
 