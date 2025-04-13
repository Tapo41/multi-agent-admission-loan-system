import os
import json
from dotenv import load_dotenv
from langchain.llms import Cohere
from langchain.vectorstores import Chroma
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.docstore.document import Document
from langchain.chains import RetrievalQA
from langchain.chains.question_answering import load_qa_chain
from langchain.agents import Tool

load_dotenv()
llm = Cohere(cohere_api_key=os.getenv("COHERE_API_KEY"))
def load_faq_chain(llm):
    with open("faq_data.json", "r") as f:
        faqs = json.load(f)

    docs = [Document(page_content=f"{faq['question']} - {faq['answer']}") for faq in faqs]
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    vectorstore = Chroma.from_documents(
        documents=docs,
        embedding=embeddings,
        persist_directory="./chroma_db"
    )

    qa_chain = load_qa_chain(llm=llm, chain_type="stuff")

    return RetrievalQA(
        retriever=vectorstore.as_retriever(search_kwargs={"k": 2}),
        combine_documents_chain=qa_chain
    )

faq_chain = load_faq_chain(llm)


faq_tool = Tool(
    name="FAQ Retriever",
    func=lambda q: faq_chain.run(q),
    description="Use this to answer FAQs related to student admission."
)

tools = [faq_tool]
