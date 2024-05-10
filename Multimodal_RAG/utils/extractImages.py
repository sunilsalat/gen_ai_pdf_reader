
from django.conf import settings
from unstructured.partition.pdf import partition_pdf
import pytesseract
pytesseract.pytesseract.tesseract_cmd = r'usr\bin\tesseract'

import os
import boto3
import uuid
import base64
from IPython import display
from unstructured.partition.pdf import partition_pdf
from langchain.chat_models import ChatOpenAI
from langchain.embeddings import OpenAIEmbeddings
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain.schema.messages import HumanMessage, SystemMessage
from langchain.schema.document import Document
from langchain.vectorstores import FAISS
from langchain.retrievers.multi_vector import MultiVectorRetriever

def extract_images_using_partition_pdf(file_path):

    raw_pdf_elements = partition_pdf(
        filename=file_path,
        extract_images_in_pdf=True,
        infer_table_structure=True,
        chunking_strategy="by_title",
        max_characters=4000,
        new_after_n_chars=3800,
        combine_text_under_n_chars=2000,
        extract_image_block_output_dir=settings.IMAGES_OUT_DIR,
    )

    return raw_pdf_elements

def process_pdf_and_create_faiss_index(raw_pdf_elements, img_urls):

    #
    # Get text summaries and table summaries
    #
    text_elements = []
    table_elements = []

    text_summaries = []
    table_summaries = []

    summary_prompt = """
    Summarize the following {element_type}:
    {element}
    """

    summary_chain = LLMChain(
        llm=ChatOpenAI(model="gpt-3.5-turbo", openai_api_key = settings.OPENAI_API_KEY, max_tokens=1024),
        prompt=PromptTemplate.from_template(summary_prompt)
    )

    for e in raw_pdf_elements:
        if 'CompositeElement' in repr(e):
            text_elements.append(e.text)
            summary = summary_chain.run({'element_type': 'text', 'element': e})
            text_summaries.append(summary)

        elif 'Table' in repr(e):
            table_elements.append(e.text)
            summary = summary_chain.run({'element_type': 'table', 'element': e})
            table_summaries.append(summary)
    #
    # Get image summaries
    #
    image_elements = []
    image_summaries = []

    def summarize_image(image_path):
        prompt = [
            SystemMessage(content="You are a bot that is good at analyzing images related to Dog's health."),
            HumanMessage(content=[
                {
                    "type": "text",
                    "text": "Describe the contents of this image."
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": image_path
                    },
                },
            ])
        ]
        response = ChatOpenAI(model="gpt-4-vision-preview", openai_api_key=settings.OPENAI_API_KEY, max_tokens=1024).invoke(prompt)
        return response.content

    for i in img_urls:
        if i:
            image_elements.append(i)
            summary = summarize_image(i)
            image_summaries.append(summary)

    #
    # Storing agg Result in FAIIS Vector-Store
    #
    documents = []
    retrieve_contents = []

    for e, s in zip(text_elements, text_summaries):
        i = str(uuid.uuid4())
        doc = Document(
            page_content = s,
            metadata = {
                'id': i,
                'type': 'text',
                'original_content': e
            }
        )
        retrieve_contents.append((i, e))
        documents.append(doc)

    for e, s in zip(table_elements, table_summaries):
        doc = Document(
            page_content = s,
            metadata = {
                'id': i,
                'type': 'table',
                'original_content': e
            }
        )
        retrieve_contents.append((i, e))
        documents.append(doc)

    for e, s in zip(image_elements, image_summaries):
        doc = Document(
            page_content = s,
            metadata = {
                'id': i,
                'type': 'image',
                'original_content': e
            }
        )
        retrieve_contents.append((i, s))
        documents.append(doc)

    vectorstore = FAISS.from_documents(documents=documents, embedding=OpenAIEmbeddings(openai_api_key=settings.OPENAI_API_KEY))

    vectorstore.save_local(settings.FAISS_INDEX_PATH)
    return 'Vector Stored Locally'


__all__ = ['extract_images_using_partition_pdf', 'process_pdf_and_create_faiss_index' ]

# https://www.youtube.com/watch?v=hSuCT6Z2QLk&t=66s

# https://stackoverflow.com/questions/76258587/combine-vectore-store-into-langchain-toolkit
# db1 = FAISS.from_texts(<txt>, embeddings)
# db2 = FAISS.from_texts(<pdf>, embeddings)

# vectorstore_info = VectorStoreInfo(
#     name="Guidelines",
#     description="QA Analysis Guidelines",
#     vectorstore=db1
#     )

# vectorstore_info2 = VectorStoreInfo(
#     name="Transcript",
#     description="Transcript of Call Center Agent Call",
#     vectorstore=db2
#     )

# db1.merge_from(db2)  # This will combine db2 INTO db1