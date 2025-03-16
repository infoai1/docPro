import streamlit as st
import openai
import pandas as pd
import json
import io
from docx import Document

# Streamlit UI
st.title("Google Doc Thematic Analysis with GPT-4")

# API Key Input
api_key = st.text_input("Enter your OpenAI API Key:", type="password")

# File Upload
docx_file = st.file_uploader("Upload a DOCX file", type=["docx"])

# OpenAI API Call Function
def call_openai_api(api_key, messages):
    openai.api_key = api_key  # Set API Key dynamically
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=messages,
        temperature=0.5
    )
    return response["choices"][0]["message"]["content"]

# Extract text from DOCX
def extract_text_from_docx(docx_file):
    document = Document(docx_file)
    text = "\n".join([para.text for para in document.paragraphs if para.text.strip()])
    return text

# Detect Chapters (Basic Heading Detection)
def split_into_chapters(text):
    lines = text.split("\n")
    chapters = []
    current_chapter = {"title": "Introduction", "text": ""}
    
    for line in lines:
        if len(line.strip()) > 0 and line.strip().isupper():
            if current_chapter["text"].strip():
                chapters.append(current_chapter)
            current_chapter = {"title": line.strip(), "text": ""}
        else:
            current_chapter["text"] += line + " "
    
    if current_chapter["text"].strip():
        chapters.append(current_chapter)
    
    return chapters

# Process Chapters with OpenAI API
def process_chapters(api_key, chapters):
    results = []
    for chapter in chapters:
        messages = [
            {"role": "system", "content": "You are an expert in thematic analysis."},
            {"role": "user", "content": f"Analyze this chapter and provide structured JSON output:\nTitle: {chapter['title']}\nText: {chapter['text']}"}]
        
        response = call_openai_api(api_key, messages)
        
        try:
            response_json = json.loads(response)
            response_json["Chapter"] = chapter['title']
            response_json["Text"] = chapter['text']
            results.append(response_json)
        except json.JSONDecodeError:
            st.error(f"Error processing chapter: {chapter['title']}")
    
    return results

# Convert Processed Data to CSV
def convert_to_csv(data):
    df = pd.DataFrame(data)
    return df

# Main Processing Logic
if docx_file:
    with st.spinner("Extracting text..."):
        text = extract_text_from_docx(docx_file)
        chapters = split_into_chapters(text)
        st.success(f"Extracted {len(chapters)} chapters.")
    
    if api_key and st.button("Process with GPT-4"):
        with st.spinner("Processing chapters..."):
            results = process_chapters(api_key, chapters)
            df = convert_to_csv(results)
            st.success("Processing complete!")
            
            # Download CSV File
            csv_buffer = io.BytesIO()
            df.to_csv(csv_buffer, index=False)
            csv_buffer.seek(0)
            st.download_button("Download CSV", csv_buffer, file_name="processed_chapters.csv", mime="text/csv")
    elif not api_key:
        st.warning("⚠️ Please enter your OpenAI API Key before proceeding.")
