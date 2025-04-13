import streamlit as st
from login import show_login
import time
import uuid
import os
from datetime import datetime, timedelta
from langchain.agents import initialize_agent, AgentType
from agent_tools import tools, llm
import streamlit as st
import json
from doc_extrac_shortlist import DocumentCheckingAgent, parse_extracted_text, shortlist_agent, agent_executor
from loan_agent import agent_executor, LoanDecisionAgent
# --- SESSION TIMEOUT CONFIG ---
SESSION_TIMEOUT_MINUTES = 15

if "choice" not in st.session_state:
    st.session_state["choice"] = "🏠 Home"
# --- SESSION STATE INIT ---
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
    st.session_state["role"] = None
    st.session_state["last_active"] = datetime.now()

# --- SESSION EXPIRATION CHECK ---
if st.session_state["logged_in"]:
    now = datetime.now()
    if now - st.session_state["last_active"] > timedelta(minutes=SESSION_TIMEOUT_MINUTES):
        st.warning("⏳ Session expired due to inactivity.")
        st.session_state["logged_in"] = False
        st.session_state["role"] = None
        st.stop()
    else:
        st.session_state["last_active"] = now

# --- LOGIN ---
if not st.session_state["logged_in"]:
    show_login()
    st.stop()

# --- SIDEBAR MENU ---
with st.sidebar:
    st.image("https://webdosolutions.net/wp-content/uploads/2023/09/user-icon-2048x2048-ihoxz4vq-1024x1024.png", width=150)
    st.title("Helpdesk Navigation")
    choice = st.radio(
        "Go to:",
        [
            "🏠 Home",
            "📄 Document Verification",
            "📄 Document Shortlisting",
            "🏦 Loan Queries",
            "📈 Admin Analytics",
            "❓ FAQ & Support",
            "🔐 Logout",
        ],
    )

# --- LOGOUT ---
if choice == "🔐 Logout":
    st.session_state["logged_in"] = False
    st.session_state["role"] = None
    st.success("✅ You have been logged out.")
    time.sleep(5)
    st.rerun()

# --- HOME PAGE ---
elif choice == "🏠 Home":
    st.title(f"🎉 Welcome, {st.session_state['role']}!")
    st.write("This is the main dashboard for managing student admissions.")

# --- DOCUMENT VERIFICATION PAGE ---
elif choice == "📄 Document Verification":
    if st.session_state["role"] != "Document Checker":
        st.warning("⚠️ Access denied! Only Document Checkers can access this page.")
        st.stop()

    st.header("📄 Upload and Verify Documents")
    uploaded_file = st.file_uploader("Upload the document for verification", type=["pdf", "docx","jpg","png","jpeg"])

    if uploaded_file:
        st.success("✅ Document uploaded successfully!")
        st.info("🔎 Verification in progress...")

        # Simulate verification process
        progress_bar = st.progress(0)
        for percent_complete in range(100):
            time.sleep(0.02)
            progress_bar.progress(percent_complete + 1)

        st.success("✅ Document verified successfully!")
        st.download_button(
            label="📥 Download Verified Document",
            data=uploaded_file.read(),
            file_name=uploaded_file.name,
            mime="application/octet-stream",
        )
elif choice == "📄 Document Shortlisting":
    if st.session_state["role"] != "Document Checker":
        st.warning("⚠️ Access denied! Only Document Checkers can access this page.")
        st.stop()

    st.header("📄 Upload and Verify Documents")
    uploaded_file = st.file_uploader("Upload student result image (JPEG/PNG)", type=["jpg", "jpeg", "png"])

    if uploaded_file:
        temp_path = f"./temp_upload_{uuid.uuid4()}.{uploaded_file.type.split('/')[-1]}"
        with open(temp_path, "wb") as f:
            f.write(uploaded_file.read())

        st.image(temp_path, caption="Uploaded Document", use_container_width=True)

        try:
            doc_checker = DocumentCheckingAgent("C:\\Program Files\\Tesseract-OCR\\tesseract.exe")
            extracted_text = doc_checker.extract_text_from_image(temp_path)

            st.subheader("📄 Extracted Text")
            with st.expander("📄 Show Raw Extracted Text"):
                st.text(extracted_text)

            expected_keywords = ["Name", "Registration No", "Overall Grade", "Result", "Roll No"]
            validation_result = doc_checker.validate_document(temp_path, expected_keywords)
            st.subheader("✅ Validation Result:")
            st.json(validation_result)

            parsed_data = parse_extracted_text(extracted_text)
            st.subheader("📊 Parsed Data:")
            st.json(parsed_data)

            query_data = {
                "verification_result": validation_result,
                "extracted_text": parsed_data
            }

            if st.button("📌 Run Shortlisting Agent"):
                with st.spinner("Processing..."):
                    response = agent_executor.run(f"Shortlist this student: {json.dumps(query_data)}")
                st.success("✅ Response from Agent:")
                st.markdown(f"**{response}**")

        except Exception as e:
            st.error(f"❌ An error occurred: {str(e)}")

        finally:
            os.remove(temp_path)
# --- LOAN QUERIES PAGE ---
# --- LOAN QUERIES PAGE ---
elif choice == "🏦 Loan Queries":
    if st.session_state["role"] != "Loan Agent":
        st.warning("⚠️ Access denied! Only Loan Agents can handle loan queries.")
        st.stop()

    st.header("🏦 Loan Application Assistant")
    st.write("This tool helps Loan Agents answer student queries and evaluate loan eligibility.")

    loan_tab1, loan_tab2 = st.tabs(["💡 FAQs", "📋 Loan Eligibility Checker"])

    with loan_tab1:
        st.subheader("Got Questions? Ask here 👇")
        user_question = st.text_input("Ask any question about student loan approval:")
        if st.button("Get Answer", key="faq"):
            if user_question:
                with st.spinner("Thinking..."):
                    try:
                        response = agent_executor.run(user_question)
                        st.success(response)
                    except Exception as e:
                        st.error(f"Error: {e}")
            else:
                st.warning("Please enter a question.")

    with loan_tab2:
        st.subheader("Check Student Loan Eligibility 📊")

        shortlisted = st.selectbox("Was the student shortlisted by the admission committee?", ["Yes", "No"])
        annual_income = st.number_input("Annual Income (₹)", min_value=0)
        requested_loan = st.number_input("Requested Loan Amount (₹)", min_value=0)

        if st.button("Check Loan Eligibility", key="loan_check"):
            status = "shortlisted" if shortlisted == "Yes" else "not shortlisted"
            data = {
                "shortlisted": status,
                "annual_income": annual_income,
                "requested_loan": requested_loan
            }

            with st.spinner("Evaluating loan eligibility..."):
                try:
                    response = agent_executor.run(f"Evaluate loan eligibility: {json.dumps(data)}")
                    st.success(response)
                except Exception as e:
                    st.error(f"Error: {e}")


# --- ADMIN ANALYTICS PAGE ---
elif choice == "📈 Admin Analytics":
    if st.session_state["role"] != "Admin":
        st.warning("⚠️ Access denied! Only Admins can access analytics.")
        st.stop()

    st.header("📈 Admission Insights")

    applications = 150
    verified_docs = 120
    rejected_docs = 30
    loans_approved = 50
    loans_rejected = 20

    col1, col2 = st.columns(2)
    col1.metric("📄 Total Applications", applications)
    col2.metric("✅ Verified Documents", verified_docs)

    st.subheader("📊 Admission Progress")
    st.bar_chart({"Status": ["Verified", "Rejected"], "Count": [verified_docs, rejected_docs]})

    st.subheader("🏦 Loan Approval Rate")
    st.bar_chart({"Status": ["Approved", "Rejected"], "Count": [loans_approved, loans_rejected]})

# --- FAQ PAGE ---
elif choice == "❓ FAQ & Support":
    st.header("🤖 Ask Our Admission Counsellor Bot")
    query = st.text_input("💬 What's your admission-related question?")

    if query and st.button("Ask"):
        with st.spinner("🤖 Thinking..."):
            try:
                agent_executor = initialize_agent(
                    tools=tools,
                    llm=llm,
                    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
                    verbose=False,
                    handle_parsing_errors=True,
                    return_intermediate_steps=True
                )

                result = agent_executor.invoke({"input": query})

                st.subheader("🧠 Reasoning Process")
                for i, step in enumerate(result["intermediate_steps"]):
                    action, observation = step
                    st.markdown(f"**Step {i + 1}:**")
                    st.markdown(f"*Tool:* `{action.tool}`")
                    st.code(action.tool_input)
                    st.markdown(f"**Response:** {observation}")
                    st.markdown("---")

                st.subheader("✅ Final Answer")
                st.success(result["output"])

            except Exception as e:
                st.error(f"⚠️ Something went wrong: {e}")