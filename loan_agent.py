import json
from langchain.vectorstores import Chroma
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.docstore.document import Document
from langchain.chains import RetrievalQA
from langchain.chains.question_answering import load_qa_chain
from langchain.agents import Tool, initialize_agent, AgentType
from langchain.llms import Cohere
import os
llm = Cohere(cohere_api_key=os.getenv("COHERE_API_KEY"))
def load_faq_chain():
    with open("loan_data.json", "r") as f:
        faqs = json.load(f)

    docs = [Document(page_content=f"{faq['question']} - {faq['answer']}") for faq in faqs]
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    vectorstore = Chroma.from_documents(
        documents=docs,
        embedding=embeddings,
        persist_directory="./loan_faq_db"
    )

    qa_chain = load_qa_chain(llm=llm, chain_type="stuff")

    return RetrievalQA(
        retriever=vectorstore.as_retriever(search_kwargs={"k": 2}),
        combine_documents_chain=qa_chain
    )

faq_chain = load_faq_chain()

faq_tool = Tool(
    name="Loan FAQ Retriever",
    func=lambda q: faq_chain.run(q),
    description="Use this to answer FAQs related to student loan approval."
)
class LoanDecisionAgent:
    def __init__(self, budget, income_threshold):
        self.budget = budget
        self.income_threshold = income_threshold

    def approve_loan(self, input_str):
        try:
            data = json.loads(input_str)

            # Extract inputs
            shortlisted = data.get("shortlisted", "").strip().lower()
            annual_income = float(data.get("annual_income", 0))
            requested_loan = float(data.get("requested_loan", 0))

            temp_budget = self.budget  # Avoid mutation unless approved in final output

            if shortlisted != "shortlisted":
                return "Loan Rejected: Student not shortlisted."

            if annual_income > self.income_threshold:
                return f"Loan Rejected: Annual income {annual_income} exceeds threshold {self.income_threshold}."

            if requested_loan > temp_budget:
                return f"Loan Rejected: Requested loan ({requested_loan}) exceeds remaining budget ({temp_budget})."

            # Simulate approval, don't mutate real budget during intermediate calls
            return f"Loan Approved for ₹{requested_loan}. Remaining Budget: ₹{temp_budget - requested_loan}"

        except Exception as e:
            return f"Error processing loan application: {str(e)}"

    def finalize_approval(self, input_str):
        """Deduct from real budget after final decision"""
        data = json.loads(input_str)
        requested_loan = float(data.get("requested_loan", 0))
        self.budget -= requested_loan
        return f"[FINAL] Loan Approved. Remaining Budget: ₹{self.budget}"
loan_agent = LoanDecisionAgent(budget=500000, income_threshold=300000)
loan_tool = Tool(
    name="Student Loan Agent",
    func=lambda query: loan_agent.approve_loan(query),
    description="Use this to decide if a student is eligible for a loan based on shortlisting, income, and university budget."
)

# Register tools with agent
tools = [faq_tool, loan_tool]

agent_executor = initialize_agent(
    tools=tools,
    llm=llm,
    agent_type=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    verbose=True,
    handle_parsing_errors=True
)
if __name__ == "__main__":
    # Example usage
    annual_income = int(input("Enter your annual income (in INR): "))
    requested_loan_amount = int(input("Enter requested loan amount (in INR): "))

    query_loan={   
       "shortlisted": "shortlisted",# You can pass in the extr10acted cleaned_response
       "annual_income": annual_income,        # From user input
       "requested_loan": requested_loan_amount
    }

    response = agent_executor.run(f"Evaluate loan eligibility: {json.dumps(query_loan)}")
    print(response)