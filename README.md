# GeminiVision — AI Powered Multimodal Document & Image Chatbot

## Overview

GeminiVision is a modern AI-powered multimodal chatbot built using Flask and Google Gemini.
The application allows users to upload images, PDFs, handwritten notes, invoices, medical documents, charts, and scanned files, then interact with them conversationally using natural language.

The system converts uploaded documents into AI-readable content and sends them to Google's Gemini Vision model for intelligent analysis, extraction, summarization, OCR, and question answering.

This project demonstrates how Generative AI and Vision Models can be integrated into real-world enterprise document workflows.

---

# Features

## Multimodal AI Analysis

Supports:

* Images
* Scanned PDFs
* Handwritten notes
* Medical reports
* Bills & invoices
* Charts & screenshots
* OCR extraction

---

## Conversational AI Interface

Users can:

* Ask questions about uploaded files
* Extract important information
* Summarize documents
* Analyze charts
* Read handwritten text
* Perform document intelligence tasks

---

## Smart PDF Processing

* Converts PDF pages into images
* Automatically resizes pages for optimized AI processing
* Supports multi-page PDF analysis

---

## Beautiful Modern UI

* Responsive chat interface
* Drag & drop uploads
* File previews
* Chat-style interaction
* Real-time AI responses

---

# Technologies Used

| Technology          | Purpose                |
| ------------------- | ---------------------- |
| Flask               | Backend API            |
| Google Gemini API   | Vision + Generative AI |
| PyMuPDF (fitz)      | PDF rendering          |
| Pillow (PIL)        | Image processing       |
| HTML/CSS/JavaScript | Frontend UI            |
| Flask-CORS          | Cross-origin support   |

---

# Architecture Overview

```text
                ┌────────────────────┐
                │   User Uploads     │
                │ Images / PDFs      │
                └─────────┬──────────┘
                          │
                          ▼
                ┌────────────────────┐
                │   Flask Backend    │
                │ File Validation    │
                └─────────┬──────────┘
                          │
          ┌───────────────┴────────────────┐
          │                                │
          ▼                                ▼
 ┌──────────────────┐            ┌──────────────────┐
 │ Image Processing │            │ PDF Processing   │
 │ PIL Resize       │            │ PyMuPDF Render   │
 └─────────┬────────┘            └─────────┬────────┘
           │                               │
           └───────────────┬───────────────┘
                           ▼
                ┌────────────────────┐
                │ Base64 Conversion  │
                └─────────┬──────────┘
                          ▼
                ┌────────────────────┐
                │ Gemini Vision API  │
                │ Multimodal Prompt  │
                └─────────┬──────────┘
                          ▼
                ┌────────────────────┐
                │ AI Generated Output│
                │ OCR / Summary / QA │
                └─────────┬──────────┘
                          ▼
                ┌────────────────────┐
                │ Chat UI Response   │
                └────────────────────┘
```

---

# How It Works
<img width="1914" height="840" alt="Screenshot 2026-05-29 122620" src="https://github.com/user-attachments/assets/be911d84-7384-4449-866d-4d567725d0fa" />

## Step 1 — Upload Files

Users upload:

* PDFs
* Images
* Scanned documents
* Medical reports
* Invoices
<img width="1917" height="834" alt="Screenshot 2026-05-29 122646" src="https://github.com/user-attachments/assets/6da87f0a-24b6-4255-81f8-78567a9fcc92" />

---

## Step 2 — Preprocessing

The backend:

* Validates file types
* Converts PDFs into images
* Resizes large images
* Converts files into Base64 format
<img width="1901" height="827" alt="Screenshot 2026-05-29 122702" src="https://github.com/user-attachments/assets/286d4e3e-d72e-466b-92d4-1578ca3ab4cd" />

---

## Step 3 — AI Processing

The processed files are sent to Gemini Vision Model along with the user's prompt.

Example prompts:

* "Extract all text"
* "Summarize this report"
* "Find patient details"
* "What is the invoice amount?"
* "Read handwritten content"

---<img width="1913" height="835" alt="Screenshot 2026-05-29 122718" src="https://github.com/user-attachments/assets/3acd24ef-5e63-413a-9018-93ba3e275a52" />


## Step 4 — AI Response

Gemini analyzes the visual content and generates:

* OCR output
* Summaries
* Structured information
* Answers to user questions
<img width="1909" height="826" alt="Screenshot 2026-05-29 122750" src="https://github.com/user-attachments/assets/7d77e767-474a-4a09-b025-5be70dbcc498" />

---

# Business Use Cases

## Healthcare

* Medical report summarization
* Patient information extraction
* Insurance document analysis
* Prescription OCR

---

## Finance & Accounting

* Invoice extraction
* Bill analysis
* Expense automation
* Financial document understanding

---

## Enterprise Document Automation

* OCR automation
* Smart document search
* Knowledge extraction
* AI-powered document assistant

---

## Education

* Handwritten note analysis
* Assignment digitization
* Study material summarization

---

## Legal & Compliance

* Contract review
* Legal document understanding
* Compliance document extraction

---

# Benefits

## Faster Document Processing

Reduces manual work by automating OCR and extraction.

## AI-Powered Understanding

Not just OCR — the model understands document meaning.

## Multimodal Intelligence

Can process both text and images together.

## Enterprise Ready

Can be extended into:

* RAG systems
* AI Agents
* Workflow automation
* Document intelligence platforms

## Better User Experience

Modern conversational UI improves accessibility and usability.

---

# API Endpoints

## GET /

Returns the frontend UI.

## GET /api/model

Returns current Gemini model information.

## GET /api/presets

Returns predefined AI prompts.

## POST /api/analyze

Uploads files and returns AI-generated analysis.

---

# Installation

```bash
git clone https://github.com/your-username/GeminiVision.git

cd GeminiVision

pip install -r requirements.txt

python app.py
```

---

# Run Application

```bash
python app.py
```

Application runs on:

```text
http://localhost:5001
```

---

# Example Prompts

* Extract all text from this document
* Summarize this medical report
* What is the total invoice amount?
* Extract patient details
* Read handwritten notes
* Analyze this chart
* Explain this graph

---

# Future Improvements

* Streaming responses
* Vector database integration
* RAG implementation
* Multi-agent workflow
* Authentication system
* Database storage
* Export to Excel/PDF
* Real-time OCR pipeline
* LangChain / CrewAI integration

---

# Security Note

Do not expose your Gemini API key publicly.
Store secrets using:

* Environment variables
* `.env` files
* Secret managers

---

# Project Goal

The goal of GeminiVision is to build an intelligent AI document assistant capable of understanding visual documents and enabling conversational interaction with them using Generative AI.

---

# Author

## 👨‍💻 Author

<table>
  <tr>
    <td align="center">
      <strong>Abinashkumar C</strong><br><br>
      <a href="mailto:abinashkumarc752@gmail.com">📧 abinashkumarc752@gmail.com</a><br><br>
      <a href="https://github.com/AbinashkumarC">🐙 GitHub</a> &nbsp;|&nbsp;
      <a href="https://www.linkedin.com/in/abinashkumar-c-b7222b251/">💼 LinkedIn</a> &nbsp;|&nbsp;
      <a href="https://chimerical-sunshine-442277.netlify.app/">🌐 Portfolio</a>
    </td>
  </tr>
</table>

Feel free to reach out for questions, collaboration, or feedback about this project.

