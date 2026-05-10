# GEO Fact-Checker 🔍

An AI-powered web app that automatically verifies claims in PDF documents by cross-referencing them against live web data.

## 🚀 Live Demo
👉 [Click here to use the app](https://factcheck-ai-app.streamlit.app/)

## 🎯 What It Does
- Upload any PDF document
- Automatically extracts factual claims (stats, dates, figures)
- Searches the live web to verify each claim
- Flags each claim as ✅ Verified, ⚠️ Inaccurate, or ❌ False

## 🛠️ Tech Stack
- Frontend: Streamlit
- AI: Claude API (Anthropic)
- PDF Parsing: PyPDF2
- Deployment: Streamlit Cloud

## ⚙️ How to Run Locally

1. Clone this repository
   git clone https://github.com/ishamishra0421-gif/fact-checker.git

2. Install dependencies
   pip install -r requirements.txt

3. Add your API key — create a .env file and add:
   ANTHROPIC_API_KEY=your_key_here

4. Run the app
   streamlit run app.py

## 📁 Project Structure
- app.py → Main application code
- requirements.txt → Python dependencies
- README.md → Project documentation

## 👤 Author
Isha Mishra — CogCulture PM Trainee Assessment 2026
