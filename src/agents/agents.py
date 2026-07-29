from langchain.agents import create_agent
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from src.tools.tools import web_searach , scrape_url 

from dotenv import load_dotenv

llm = ChatGoogleGenerativeAI(model="gemini-3.6-flash" , temperature=0)

#1st Agent : Search Agent
def build_search_agent():
    return create_agent(
        model=llm,
        tools=[web_searach],
    )

#2nd Agent : Reader Agent
def build_reader_agent():
    return create_agent(
        model=llm,
        tools=[scrape_url]
    )

writer_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are an expert research writer. Write clear , structured and insightful reports."),
    ("human" , """Write a detailed research report on topic below.
    
    Topic: {topic}
    Research Gathered:
    {research}

    Structure the report as:
    -Introduction
    -Key Findings (minimun 3 well-explained points)
    -Conclusion
    -Sources (list all URLs found in the research)

    Be detailed, factual and professional.
    """),
])

writer_chain = writer_prompt | llm | StrOutputParser()

#Critic_chain

critic_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a sharp and constructive research critic. Be honest and specific."),
    ("human", """Review the research report below and evaluate it strictly.
    
Report:
{report}

Respond in this exact fromat:

Score: X/10

Strengths:

- ...
- ...

Area of imporvements:
- ...
- ...

one line verdict:
..."""
    ),
])

critic_chain = critic_prompt | llm | StrOutputParser