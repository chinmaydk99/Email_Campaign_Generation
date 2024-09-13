import os
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import ToolExecutor
from langchain_community.tools.tavily_search import TavilySearchResults
import base64


# Constants
MODEL = "gemma2:9b-instruct-q8_0"
WRITING_MODEL  = "gemma2:9b-instruct-q8_0"
OPENAI_API_KEY = "NA"
TAVILY_API_KEY = "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"

# Environment variables
os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY
os.environ["TAVILY_API_KEY"] = TAVILY_API_KEY

TONES = [
    "friendly and conversational",
    "excited and enthusiastic",
    "professional and informative",
    "urgent and action oriented",
    "empathetic and supportive",
    "playful and humorous"
]

PRODUCT_CATEGORIES = {
    "tablets": {
        "options": ["Tab_A9", "Tab_S9_FE", "Tab_S9"],
    },
    "phones": {
        "options": ["Galaxy_S24", "Galaxy_Z_Flip_6", "Galaxy_Z_Fold_6"],
    },
    "watches": {
        "options": ["Watch_FE", "Watch_Ultra", "Watch6", "Watch7"],
    },
    "tv": {
        "options": ["Samsung_8K_TV", "Crystal_UHD_TV","OLED_TV"],
    }
}


GALAXY_AI_URL = "https://www.samsung.com/us/galaxy-ai/"
# LLM Setup
llm = ChatOpenAI(
    model=MODEL,
    base_url="http://localhost:11434/v1"
)

tavily_search_results = TavilySearchResults()
tools = [tavily_search_results]
tool_executor = ToolExecutor(tools)