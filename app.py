import os
import json
from dotenv import load_dotenv
from fastapi import FastAPI, Form
import uvicorn
from fastapi.middleware.cors import CORSMiddleware
import openai  # Use OpenAI instead of Google Generative AI
from fastapi.responses import JSONResponse
import re

# Initialize FastAPI app
app = FastAPI()

# Load environment variables
load_dotenv()

# Set OpenAI API key securely using environment variable
openai.api_key = os.getenv("OPENAI_API_KEY")  # Ensure you have set this in your environment variables

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Helper function to extract questions and answers from text
def extract_questions_answers_with_gpt(content: str):
    """
    Sends the content to OpenAI's GPT-4o model to extract questions and suggested answers.
    If the document is for a case study assessment, extracts the case study context separately and only once.
    """
    print("Started extracting questions and answers from content...")

    # Check for case study keywords
    is_case_study = "case study" in content.lower()
    print(f"Is the content identified as a case study? {is_case_study}")

    # Prepare the prompt based on the type of assessment
    if is_case_study:
        prompt = f"""
        You are an assistant that extracts structured information from text. 
        Extract the case study context only once if the document is for a case study assessment. 
        Then extract all the questions and suggested answers in the specified format.

        Extract the case study context only once if the document is for a case study assessment. Then extract all the questions and suggested answers, and format them as a JSON array. Each item should have the following structure:
        -'Total Duration,Duration,time(Give only number , do not add any unit name with the number example:- 30 ,60,120 etc)'
        -'instructions to Candidate'
        - 'question_number'
        - 'question'
        - 'question_instruction (These instruction come after question number. It is present in ())'
        -'comparison_count (This count will come after the Suggested answer Handing give if it is present if comparison_count not present then try  to find it form the question. if there are not present both place then all )
       -'comparison_instruction(This count will come after the Suggested answer Handing (any 1,any 2,any 3,any one,any two,any three) if not presnet then send null)
        
        - 'suggested_answer' (as an array of points)
        - 'case_study_context' (if applicable)

        Example output format:
        {{
            "assessment_type": "case_study",
            "duration":"Duration",
            "assessment_instruction":[<instructions to Candidate_point_1>, <instructions to Candidate_point_2>, ...],
            "case_study_context": "<case study content>",
            "questions_and_answers": [
                {{
                    "question_number": <question_number>,
                    "question": "<question_text>",
                    "question_instruction": "<question_instruction>",
                    "comparison_count":<comparison_count>,
                    "comparison_instruction":<comparison_instruction>,
                    "suggested_answer": [<answer_point_1>, <answer_point_2>, ...]
                }}
            ]
        }}

        Document content:
        {content}
        """
    else:
        prompt = f"""
        You are an assistant that extracts structured information from text. 
        Extract all the questions and suggested answers in the specified format.

        Extract all the questions and suggested answers, and format them as a JSON array. Each item should have the following structure:
        -'Total Duration,Duration,time(Give only number , do not add any unit name with the number example:- 30 ,60,120 etc)'
        -'instructions to Candidate'
        - 'question_number'
        - 'question'
        - 'question_instruction (These instruction come after question number. It is present in ())'
        -'comparison_count (This count will come after the Suggested answer Handing give if it is present if comparison_count not present then try  to find it form the question. if there are not present both place then all )'
        -'comparison_instruction(This count will come after the Suggested answer Handing (any 1,any 2,any 3,any one,any two,any three) if not presnet then send null)
        - 'suggested_answer' (as an array of points)

        Example output format:
        {{
            "assessment_type": "written_assessment",
            "duration":"Duration",
            "assessment_instruction":[<instructions to Candidate_point_1>, <instructions to Candidate_point_2>, ...],
            "case_study_context": "",
            "questions_and_answers": [
                {{
                    "question_number": <question_number>,
                    "question": "<question_text>",
                    "question_instruction": "<question_instruction>",
                    "conparison_instruction":<comparison_instruction>,
                    "comparison_count":<comparison_count>,
                    "suggested_answer": [<answer_point_1>, <answer_point_2>, ...]
                }}
            ]
        }}

        Document content:
        {content}
        """

    try:
        # Send the content to OpenAI's GPT-4o model
        print("Sending request to GPT-4o model...")
        response = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that extracts structured data from text."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
        )
        print("Received response from GPT-4o model.")

        # Extract the response text
        output = response["choices"][0]["message"]["content"].strip()

        # Clean the unwanted JSON markdown delimiter
        cleaned_result = re.sub(r'```json\n|\n```', '', output)

        # Parse the cleaned result to ensure it's in proper JSON format
        json_result = json.loads(cleaned_result)  # This will ensure the output is a valid JSON object

        print(f"Cleaned result: {json_result}")
        return json_result  # Return the result as a JSON object
    
    except Exception as e:
        print(f"Error during the request: {e}")
        return {"error": f"Error processing the request: {str(e)}"}


@app.get("/hello")
def hello():
    return "Hello, World!"

# API endpoint to process the text content
@app.post("/extract/")
async def extract_data_from_text(content: str = Form(...)):
    print(f"Received request to extract data. Content length: {len(content)} characters.")

    # Process the content and extract data
    extracted_data = extract_questions_answers_with_gpt(content)

    try:
        # Return the extracted data directly as a JSON response
        return JSONResponse(content=extracted_data, status_code=200)
    except Exception as e:
        return {"error": f"Error processing the request: {str(e)}"}

# Run the app with uvicorn if the script is executed directly
if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")
