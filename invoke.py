import os
from dotenv import load_dotenv, find_dotenv
from utils import *
from utils import build_retriever

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.utils.function_calling import convert_to_openai_function
#from langchain_core.agents import OpenAIFunctionsAgentOutputParser
# -------------------------------------------------
# Env setup
# -------------------------------------------------
_ = load_dotenv(find_dotenv())
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")

# -------------------------------------------------
# Build retriever (RAG)
# -------------------------------------------------
retriever = build_retriever(limit=5)

# -------------------------------------------------
# Tools → OpenAI functions
# -------------------------------------------------
tools = [
    load_full_recipe,
    get_recipe_stats,
    get_recipe_nutrition,
]

functions = [
    convert_to_openai_function(tool)
    for tool in tools
]

# -------------------------------------------------
# Model
# -------------------------------------------------
model = ChatOpenAI(
    temperature=0
).bind(functions=functions)

# -------------------------------------------------
# Prompt
# -------------------------------------------------
prompt = ChatPromptTemplate.from_messages([
    ("system",
     "You are a helpful but slightly sassy cooking assistant. "
     "Use the provided recipes when relevant. "
     "Only call tools if you need exact details."),
    ("user", "{input}")
])