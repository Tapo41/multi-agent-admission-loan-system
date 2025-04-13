import os
import json
import re
import cv2
import pytesseract
from langchain.agents import initialize_agent, AgentType
from langchain.llms import Cohere
from crewai import Agent
from langchain_community.llms import HuggingFaceEndpoint
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.chains import RetrievalQA
from langchain.tools import Tool
from dotenv import load_dotenv
from langchain.docstore.document import Document
from langchain.vectorstores import Chroma
from langchain.chains.question_answering import load_qa_chain

# Initialize environment variables from .env file
load_dotenv()

# Set the path for tesseract
pytesseract.pytesseract.tesseract_cmd = "C:\\Program Files\\Tesseract-OCR\\tesseract.exe"
class DocumentCheckingAgent:
    def __init__(self, tesseract_path=None):
        if tesseract_path:
            pytesseract.pytesseract.tesseract_cmd = tesseract_path

        self.agent = Agent(
            role="Document Checker",
            goal="Verify submitted student documents for admission.",
            backstory="You analyze scanned student documents...",
            llm=HuggingFaceEndpoint(
                endpoint_url="https://api-inference.huggingface.co/models/HuggingFaceH4/zephyr-7b-alpha",
                #huggingfacehub_api_token="",  # Optional unless using a private model
                temperature=0.2
            ),
            verbose=True
        )

    def extract_text_from_image(self, image_path):
        if not os.path.exists(image_path):
            return "Error: File not found."

        img = cv2.imread(image_path)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        text = pytesseract.image_to_string(gray)
        return text.strip()

    def validate_document(self, image_path, expected_keywords):
        extracted_text = self.extract_text_from_image(image_path)
        if extracted_text == "Error: File not found.":
            return {"status": "error", "message": "Document not found."}

        missing_keywords = [word for word in expected_keywords if word.lower() not in extracted_text.lower()]
        if missing_keywords:
            return {"status": "failed", "message": f"Missing data: {', '.join(missing_keywords)}"}
        return {"status": "verified", "message": "Document is valid."}

llm = Cohere(cohere_api_key=os.getenv("COHERE_API_KEY"))
def load_faq_chain():
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

faq_chain = load_faq_chain()

# Define FAQ tool
faq_tool = Tool(
    name="FAQ Retriever",
    func=lambda q: faq_chain.run(q),
    description="Use this to answer FAQs related to student admission."
)
def parse_extracted_text(extracted_text):
    # Extract result (PASS/FAIL)
    result_match = re.search(r"Grade\s+([A-Z\+]+)", extracted_text)  # Capture result (PASS/FAIL)
    result = result_match.group(1) if result_match else None

    # Extract overall grade (B, A, B+ etc.)
    grade_match = re.search(r"PASS\s+\d+\s+([A-Z\+]+)", extracted_text)  # Capture grade (B, A, B+)
    overall_grade = grade_match.group(1) if grade_match else None

    return {
        "result": result,
        "overall_grade": overall_grade
    }
class ShortlistingAgent:
    def __init__(self, accepted_grades=["B","B+", "A", "A+"]):
        self.accepted_grades = accepted_grades

    def shortlist(self, input_str):
        try:
            # Parse the input JSON string into Python data structure (dict)
            data = json.loads(input_str)

            # Extract verification result and extracted text
            verification_result = data.get("verification_result") or data.get("verified_document")
            extracted_text = data.get("extracted_text")

            # If not available, try reconstructing from other keys
            if isinstance(extracted_text, dict):
                overall_grade = extracted_text.get('overall_grade')
                result = extracted_text.get('result')
                if overall_grade:
                    extracted_text = f"Result: {result}\nOverall Grade: {overall_grade}"

            if not verification_result:
                return "Rejected: No verification info provided."

            if verification_result.get("status") != "verified":
                return f"Rejected: {verification_result.get('message', 'Document verification failed.')}"

            # Extract grade information from the extracted_text
            lines = [line.strip() for line in extracted_text.split('\n') if line.strip()]

            # Print lines to ensure we're extracting the correct information
            print(f"Lines after splitting extracted text: {lines}")

            grade = None

            # Try to extract the overall grade
            for line in lines:
                if "Overall Grade" in line:
                    # Use regex to cleanly extract the grade after "Overall Grade"
                    match = re.search(r"Overall Grade\s*[:\-]?\s*(\w+)", line)
                    if match:
                        grade = match.group(1)  # Extracted grade
                    break

            # If grade is not found, return rejection
            if not grade:
                return f"Rejected: Grade not found in the extracted text."

            # Print the extracted grade for debugging
            print(f"Extracted Grade: {grade}")

            # Validate the grade
            if grade in self.accepted_grades:
                return "Shortlisted"
            else:
                return f"Rejected: Grade '{grade}' not accepted."

        except Exception as e:
            return f"Error processing the input: {str(e)}"
# Wrap shortlisting agent in a Tool
shortlist_agent = ShortlistingAgent()

shortlisting_tool = Tool(
    name="Shortlisting Agent",
    func=lambda query: shortlist_agent.shortlist(query),
    description="Use this to decide if a student should be shortlisted based on verified document and grade info."
)

# Create the agent
tools = [faq_tool, shortlisting_tool]

agent_executor = initialize_agent(
    tools,
    llm,
    agent_type=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    verbose=True,
    handle_parsing_errors=True  # Add this parameter
)

# Define the Shortlisting Tool (assuming you have `Tool` and `agent_executor` properly set up)
shortlisting_tool = Tool(
    name="Shortlisting Agent",
    func=lambda query: shortlist_agent.shortlist(query),
    description="Use this to decide if a student should be shortlisted based on verified document and grade info."
)

if __name__ == "__main__":
    image_path = "D:\\web_download\\sample_result.jpeg"  # Replace with your image path
    doc_checker = DocumentCheckingAgent("C:\\Program Files\\Tesseract-OCR\\tesseract.exe")
    
    # Document verification
    result = doc_checker.validate_document(image_path, ["Name", "Registration No", "Overall Grade", "Result", "Roll No"])
    print(result)
    extracted_text = doc_checker.extract_text_from_image(image_path)
    # Parse the extracted text
    parsed_data = parse_extracted_text(extracted_text)

    # Print the parsed data
    print(parsed_data)
    # Create query data
    query_data = {
       "verification_result": result,
       "extracted_text": parsed_data
    }

   # Assuming agent_executor is properly initialized
    response = agent_executor.run(f"Shortlist this student: {json.dumps(query_data)}")
    print(response)