import openai
from docx import Document
import os
from dotenv import load_dotenv

load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")

def extract_questions_answers_with_openai(doc_path):
    """
    Reads the content of a DOCX file and sends it to OpenAI API to extract questions and suggested answers.
    If the document is for a case study assessment, extracts the case study context separately and only once.
    """
    # Read the content from the DOCX file
    document = Document(doc_path)
    content = "\n".join([paragraph.text.strip() for paragraph in document.paragraphs if paragraph.text.strip()])

    # Determine if it's a case study or written assessment based on keywords or headings
    if "case study" in content.lower():
        prompt = [
            {"role": "system", "content": "You are an assistant that extracts structured information from text."},
            {"role": "user", "content": f"Extract the case study context only once if the document is for a case study assessment. Then extract all the questions and suggested answers, and format them as a JSON array. Each item should have the following structure:\n"
                                      "1. Include 'question' and 'suggested_answer' keys.\n"
                                      "2. In the 'suggested_answer', separate the points as individual elements in an array.\n"
                                      "3. Add a 'question_type' tag like 'WA5', 'WA6', etc., along with the question number.\n"
                                      "4. Ensure no points are shortened or altered, and the content remains intact as it is.\n"
                                      "5. Extract any specific instructions like time to spend on the question and include them in a separate field 'question_instruction'.\n"
                                      "6. If the document contains a case study, provide the full context of the case study exactly as it is written in the document in a separate field 'case_study_context' (only once).\n\n"
                                      "Here is the document content:\n"
                                      f"{content}\n\n"
                                      "Please ensure the output is in JSON format and includes the following structure:\n"
                                      "{\n"
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
                                      "        { 'question_number': <question_number>,\n"
                                      "          'question': <question_text>,\n"
                                      "          'question_instruction': <question_instruction>,\n"
                                      "          'suggested_answer': <suggested_answer_list> },\n"
                                      "        ...\n"
                                      "}\n\n"
                                      "Now process the following content:"
                                      }
        ]

    # Send the content to OpenAI with the selected prompt
    response = openai.ChatCompletion.create(
        model="gpt-4",  # Use the correct model name
        messages=prompt
    )

    return response["choices"][0]["message"]["content"]

# Example usage
if __name__ == "__main__":
    # Path to your DOCX file
    doc_path = "read.docx"  # Replace with the path to your DOCX file

    result = extract_questions_answers_with_openai(doc_path)
    print("Extracted Data:")
    print(result)

    # Save the result to a JSON file
    with open("output.json", "w") as json_file:
        json_file.write(result)
