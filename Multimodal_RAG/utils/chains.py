from langchain.chains import LLMChain
from langchain.chat_models import ChatOpenAI
from langchain.prompts import PromptTemplate
from django.conf import settings


def run_qa_chian(context, question):
    prompt_template = """You are a vet doctor and an expert in analyzing dog's health.
        Answer the question based only on the following context, which can include text, images and tables:
        {context}
        Question: {question}
        Don't answer if you are not sure and decline to answer and say "Sorry, I don't have much information about it."
        Just return the helpful answer in as much as detailed possible.
        Answer:
        """

    qa_chain = LLMChain(llm=ChatOpenAI(model="gpt-4", openai_api_key = settings.OPENAI_API_KEY, max_tokens=1024),
                        prompt=PromptTemplate.from_template(prompt_template))
    result = qa_chain.run({'context': context, 'question': question})
    return result

__all__ = ['run_qa_chian']