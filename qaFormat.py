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
            {"role": "user", "content": f"Extract the case study context only once if the document is for a case study assessment. Then extract all the questions and suggested answers, and format them as a JSON array. Each item should have the following structure:\n"
                                        "1. Include 'question' and 'suggested_answer' keys.\n"
                                        "2. In the 'suggested_answer', separate the points as individual elements in an array.\n"
                                        "3. Ensure no points are shortened or altered, and the content remains intact as it is.\n"
                                        "4. Extract any specific instructions like time to spend on the question and include them in a separate field 'question_instruction'.\n"
                                        "5. If the document contains a case study, provide the full context of the case study exactly as it is written in the document in a separate field 'case_study_context' (only once).\n\n"
                                        "Here is the document content:\n"
                                        f"{content}\n\n"
                                        "Please ensure the output is in JSON format and includes the following structure:\n"
                                        "{\n"
                                        "     'assessment_type':'case_study', \n" 
                                        "    'case_study_context': <case study content>,\n"
                                        "    'questions_and_answers': [\n"
                                        "        { 'question_number': <question_number>,\n"
                                        "          'question': <question_text>,\n"
                                        "          'question_instruction': <question_instruction>,\n"
                                        "          'suggested_answer': <suggested_answer_list> },\n"
                                        "        ...\n"
                                        "    ]\n"
                                        "}\n\n"
                                        "Now process the following content:"}
        ]
    else:
        prompt = [
            {"role": "system", "content": "You are an assistant that extracts structured information from text."},
            {"role": "user", "content": f"Extract all the questions and suggested answers from the following text and format them as a JSON array. Each item should have the following structure:\n"
                                        "1. Include 'question' and 'suggested_answer' keys.\n"
                                        "2. In the 'suggested_answer', separate the points as individual elements in an array.\n"
                                        "3. If the document is for a case study assessment, provide the entire context of the case study exactly as it is written in the document.\n"
                                        "4. Add a 'question_type' tag like 'WA5', 'WA6', etc., along with the question number.\n"
                                        "5. Ensure no points are shortened or altered, and the content remains intact as it is.\n"
                                        "6. Extract any specific instructions like time to spend on the question and include them in a separate field 'question_instruction'.\n\n"
                                        f"Here is the document content:\n{content}\n\n"
                                        "Please ensure the output is in JSON format and includes the following structure:\n"
                                        "{\n"
                                        "   'assessment_type':'written_assessment'\n "
                                        "  'questions_and_answers': [\n"
                                        "        { 'question_number': <question_number>,\n"
                                        "          'question': <question_text>,\n"
                                        "          'question_instruction': <question_instruction>,\n"
                                        "          'suggested_answer': <suggested_answer_list> },\n"
                                        "        ...\n"
                                        "     ] \n "
                                        "}\n\n"
                                        "Now process the following content:"}
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
