# 🎓 Student Admission Helpdesk System

An AI-powered multi-role helpdesk platform built with **Streamlit**, **LangChain**, and **OCR (Tesseract)** to automate and streamline student admissions. The system supports **Document Verification**, **Student Shortlisting**, **Loan Evaluation**, and **Admission FAQ support** with agent-based reasoning.

---
![Screenshot](C:\Users\Tapojita Kar\Pictures\Screenshots\Screenshot 2025-04-13 162502.png)



## 🚀 Features

### ✅ Role-Based Access
- **Document Checker** – Upload, extract, and verify student result documents using OCR.
- **Loan Agent** – Evaluate student loan eligibility and answer queries using LangChain.
- **Admin** – View overall analytics on applications, verifications, and loans.
- **FAQ Support** – AI chatbot to handle admission-related queries via LangChain agents.

### 🔍 Intelligent Document Verification
- Extracts and validates key data from result documents using **Tesseract OCR**.
- Parses text to structured data format.
- Verifies presence of essential fields like `Name`, `Roll No`, `Overall Grade`.

### 🎯 Student Shortlisting
- AI agent processes extracted and validated document data.
- Decides if the student qualifies for admission based on extracted info.

### 💰 Loan Eligibility Checker
- Evaluates loan approval eligibility based on:
  - Shortlisting status
  - Annual family income
  - Requested loan amount
- Offers a Q&A tab to handle frequently asked questions using LLMs.

### 📈 Admin Dashboard
- Tracks:
  - Total applications
  - Verified & rejected documents
  - Approved & rejected loan applications
- Visual analytics with Streamlit’s interactive charts.

---

## 🧠 Tech Stack

| Tech            | Role                                |
|-----------------|-------------------------------------|
| Streamlit       | UI framework                        |
| Python          | Backend logic                       |
| Tesseract OCR   | Image text extraction               |
| LangChain       | Tool-based agent framework          |
| LLMs            | AI-powered decision making          |

---

## 🔐 Roles

| Role              | Access Areas                           |
|------------------|----------------------------------------|
| Document Checker | Document Verification, Shortlisting    |
| Loan Agent       | Loan Queries and Eligibility Check     |
| Admin            | Admin Analytics                        |

---



