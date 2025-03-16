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
