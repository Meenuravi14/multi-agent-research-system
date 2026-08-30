from langchain.agents import create_agent
from langchain.chat_models import init_chat_model
from langchain_core.tools import tool
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
import os
from tool import web_search, scrape_url
from dotenv import load_dotenv
from langchain_openrouter import ChatOpenRouter

load_dotenv()

openrouter_api_key = os.getenv("OPENROUTER_API_KEY")

llm = ChatOpenRouter(
    model="nvidia/nemotron-3-super-120b-a12b:free",
    api_key=os.getenv("OPENROUTER_API_KEY"),
    temperature=0,
)

def build_search_agent():
    return create_agent(
        model=llm,
        tools=[web_search],
        system_prompt=(
            "You are a research search assistant. Call web_search ONCE with a well-formed query, "
            "then immediately summarize the results in your final answer. Do not call the tool more than twice."
        ),
    )

def build_reader_agent():
    return create_agent(
        model=llm,
        tools=[scrape_url],
        system_prompt=(
            "You are a content reader. You will be given an exact URL. Call scrape_url ONCE on that URL, "
            "then summarize the returned content in your final answer. Do not call the tool more than once."
        ),
    )

writer_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are an expert research writer. Write clear, structured and insightful reports..."),
    ("human", """Write a detailed research report on the topic below.

Topic: {topic}

Research Gathered:
{research}

Structure the report as:
- Introduction
- Key Findings (minimum 3 well-explained points)
- Conclusion
- Sources (list all URLs found in the research)

Be detailed, factual and professional."""),
])

writer_chain = writer_prompt | llm | StrOutputParser()

#critic_chain

critic_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a sharp and constructive research critic. Be honest and specific."),
    ("human", """Review the research report below and evaluate it strictly.

Report:
{report}

Respond in this exact format:

Score: X/10

Strengths:
- ...
- ...

Areas to Improve:
- ...
- ...

One line verdict:
..."""),
])

critic_chain = critic_prompt | llm | StrOutputParser()


