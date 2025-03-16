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
    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=messages,
            temperature=0.5
        )
        return response.choices[0].message.content
    except Exception as e:
        st.error(f"❌ OpenAI API Error: {e}")
        return None

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
# Process Chapters with OpenAI API
def process_chapters(api_key, chapters):
    results = []
    for chapter in chapters:
        messages = [
            {"role": "system", "content": "You are an expert in thematic analysis and text chunking."},
            {"role": "user", "content": f"""
                Given the chapter title and its text, split the text into coherent thematic chunks of around **200-300 tokens each**.

                **IMPORTANT:** Return the response in **valid JSON format only**, with the following fields:

                {{
                  "contextual_question": "...",
                  "summary": "...",
                  "context": "...",
                  "outline": "...",
                  "theme": "...",
                  "keywords": ["Keyword1", "Keyword2"],
                  "chunks": [
                    {{
                      "chapter": "...",
                      "text": "...",
                      "contextual_question": "...",
                      "summary": "...",
                      "context": "...",
                      "outline": "...",
                      "theme": "...",
                      "keywords": ["Keyword1", "Keyword2"],
                      "references": ["Reference1", "Reference2"]
                    }},
                    ...
                  ]
                }}

                Respond **ONLY** with valid JSON. Do **not** include any extra text or explanation.

                **Example Output:**
                {{
                  "contextual_question": "What is the core idea of this chapter?",
                  "summary": "This chapter explores...",
                  "context": "Historically...",
                  "outline": "1. Question one?\\n2. Question two?",
                  "theme": "Transformation",
                  "keywords": ["Paradise", "Change"],
                  "chunks": [
                    {{
                      "chapter": "Thematic Section 1",
                      "text": "This section discusses...",
                      "contextual_question": "What is the impact?",
                      "summary": "A short summary...",
                      "context": "Historical context...",
                      "outline": "1. Question A?\\n2. Question B?",
                      "theme": "Universal Change",
                      "keywords": ["Creation", "Time"],
                      "references": ["Quran 2:30", "Hadith on change"]
                    }}
                  ]
                }}

                **Now, analyze the following chapter:**
                - **Title:** {chapter['title']}
                - **Text:** {chapter['text']}
            """}
        ]
        
        response = call_openai_api(api_key, messages)
        
        if response:
            try:
                # Ensure JSON is properly parsed
                response_json = json.loads(response.strip())

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
                st.error(f"❌ Error processing chapter: {chapter['title']} - AI returned invalid JSON.")
    
    return results

# Convert Processed Data to CSV
def convert_to_csv(data):
    df = pd.DataFrame(data)
    
    # Debug: Show first few rows in Streamlit before downloading
    if not df.empty:
        st.write("✅ Processed Data Preview:")
        st.dataframe(df.head(10))
    else:
        st.error("❌ No data generated. Please check AI responses.")
    
    return df

# Main Processing Logic
if docx_file:
    with st.spinner("Extracting text..."):
        text = extract_text_from_docx(docx_file)
        chapters = split_into_chapters(text)
        st.success(f"✅ Extracted {len(chapters)} chapters.")
    
    if api_key and st.button("Process with GPT-4"):
        with st.spinner("Processing chapters..."):
            results = process_chapters(api_key, chapters)
            df = convert_to_csv(results)
            
            if not df.empty:
                # Download CSV File
                csv_buffer = io.BytesIO()
                df.to_csv(csv_buffer, index=False)
                csv_buffer.seek(0)
                st.download_button("📥 Download CSV", csv_buffer, file_name="processed_chapters.csv", mime="text/csv")
            else:
                st.error("❌ No data available to download.")
    elif not api_key:
        st.warning("⚠️ Please enter your OpenAI API Key before proceeding.")
