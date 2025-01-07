#-------------------------------------------------------------------------------------------------------------------------------------
#                                             This String to  JSON formatter
#-------------------------------------------------------------------------------------------------------------------------------------


import openai
import os
from dotenv import load_dotenv
from fastapi import FastAPI, Form
import json
import uvicorn
from fastapi.middleware.cors import CORSMiddleware

# Initialize FastAPI app
app = FastAPI()

# Load environment variables
load_dotenv()

# Set OpenAI API key
openai.api_key = os.getenv("OPENAI_API_KEY")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Helper function to extract questions and answers from text
def extract_questions_answers_with_openai(content: str):
    """
    Sends the content to OpenAI API to extract questions and suggested answers.
    If the document is for a case study assessment, extracts the case study context separately and only once.
    """
    # Check for case study keywords
    is_case_study = "case study" in content.lower()

    # Prepare the prompt based on the type of assessment
    if is_case_study:
        prompt = [
            {"role": "system", "content": "You are an assistant that extracts structured information from text."},
            {"role": "user", "content": f"""
                Extract the case study context only once if the document is for a case study assessment. Then extract all the questions and suggested answers, and format them as a JSON array. Each item should have the following structure:
                - 'question'
                - 'question_instruction'
                - 'suggested_answer' (as an array of points)
                - 'case_study_context' (if applicable)

                Example output format:
                {{
                    "assessment_type": "case_study",
                    "case_study_context": "<case study content>",
                    "questions_and_answers": [
                        {{
                            "question_number": <question_number>,
                            "question": "<question_text>",
                            "question_instruction": "<question_instruction>",
                            "suggested_answer": [<answer_point_1>, <answer_point_2>, ...]
                        }}
                    ]
                }}

                Document content:
                {content}
            """}
        ]
    else:
        prompt = [
            {"role": "system", "content": "You are an assistant that extracts structured information from text."},
            {"role": "user", "content": f"""
                Extract all the questions and suggested answers, and format them as a JSON array. Each item should have the following structure:
                - 'question'
                - 'question_instruction'
                - 'suggested_answer' (as an array of points)

                Example output format:
                {{
                    "assessment_type": "written_assessment",
                    "questions_and_answers": [
                        {{
                            "question_number": <question_number>,
                            "question": "<question_text>",
                            "question_instruction": "<question_instruction>",
                            "suggested_answer": [<answer_point_1>, <answer_point_2>, ...]
                        }}
                    ]
                }}

                Document content:
                {content}
            """}
        ]

    # Send the content to OpenAI with the selected prompt
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=prompt,
        timeout=180
    )

    return response["choices"][0]["message"]["content"]
@app.get("/hello")
def hello():
    return "Hello, World!"

# API endpoint to process the text content
@app.post("/extract/")
async def extract_data_from_text(content: str = Form(...)):
    # Process the content
    extracted_data = extract_questions_answers_with_openai(content)

    # Return extracted data as JSON response
    try:
        return json.loads(extracted_data)
    except json.JSONDecodeError:
        return {"error": "Failed to parse the response from OpenAI"}

# Run the app with uvicorn if the script is executed directly
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
