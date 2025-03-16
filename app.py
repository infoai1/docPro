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
    client = openai.OpenAI(api_key=api_key)  # Create OpenAI client
    response = client.chat.completions.create(
        model="gpt-4",
        messages=messages,
        temperature=0.5
    )
    return response.choices[0].message.content  # Updated response format

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
def process_chapters(api_key, chapters, file_name):
    results = []
    for chapter in chapters:
        messages = [
            {"role": "system", "content": "You are an expert in thematic analysis and text chunking."},
            {"role": "user", "content": f"Given the chapter title and its text, split the text into coherent thematic chunks of around **200-300 tokens each**.\n\nFor each chunk, generate:\n- **Chapter**: The section title (if available, otherwise use the chapter title).\n- **Text**: The thematic text chunk.\n- **Contextual Question**: A comprehensive, question-style title that includes **themes, keywords, and references** to clarify the context.\n- **Summary**: A concise **2-3 sentence summary** of the chunk.\n- **Context**: A brief **2-3 sentence explanation** of the chunk’s background.\n- **Outline**: A structured **series of probing questions** based on **references (Quran, Hadith, historical figures, places, themes).**\n- **Theme**: Thematic focus of the chunk.\n- **Keywords**: The most **important keywords** in the chunk.\n- **References**: List of **Quranic verses, Hadith, historical events, names, dates, quotes, etc.** found in the chunk.\n\nAdditionally, generate:\n- A **contextual question** that captures the **core idea** of the chapter.\n- A **summary (2-3 sentences)**\n- A **context (2-3 sentences)**\n- An **outline as a series of questions** based on **references (Quran, Hadith, historical events, figures, places, themes).**\n- The **theme** of the chapter.\n- Important **keywords**.\n\nTitle: {chapter['title']}\nText: {chapter['text']}"}
        ]
        
        response = call_openai_api(api_key, messages)
        
        try:
            response_json = json.loads(response)
            for chunk in response_json.get("chunks", []):
                results.append({
                    "Chapter Name": chapter['title'],
                    "Text Chunk": chunk.get("text", ""),
                    "Contextual Question (Chapter)": response_json.get("contextual_question", ""),
                    "Contextual Question (Chunk)": chunk.get("contextual_question", ""),
                    "Chapter Summary": response_json.get("summary", ""),
                    "Chapter Context": response_json.get("context", ""),
                    "Chapter Outline (Series of Questions)": response_json.get("outline", ""),
                    "Chapter Theme": response_json.get("theme", ""),
                    "Chapter Keywords": ", ".join(response_json.get("keywords", [])),
                    "Chunk Summary": chunk.get("summary", ""),
                    "Chunk Context": chunk.get("context", ""),
                    "Chunk Outline (Series of Questions)": chunk.get("outline", ""),
                    "Chunk Theme": chunk.get("theme", ""),
                    "Chunk Keywords": ", ".join(chunk.get("keywords", [])),
                    "References": ", ".join(chunk.get("references", []))
                })
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
            file_name = docx_file.name.replace(".docx", "")
            results = process_chapters(api_key, chapters, file_name)
            df = convert_to_csv(results)
            st.success("Processing complete!")
            
            # Download CSV File
            csv_buffer = io.BytesIO()
            df.to_csv(csv_buffer, index=False)
            csv_buffer.seek(0)
            st.download_button("Download CSV", csv_buffer, file_name="processed_chapters.csv", mime="text/csv")
    elif not api_key:
        st.warning("⚠️ Please enter your OpenAI API Key before proceeding.")
