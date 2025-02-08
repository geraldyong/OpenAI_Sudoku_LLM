from typing import Dict
from models import NextMove
from openai import OpenAI
from helper import *
import os
import json

# OpenAI API Key (ensure this is secured in a real-world app, like using environment variables)
client = OpenAI(
    api_key  = os.getenv('OPENAI_API_KEY'),
    organization = os.getenv('OPENAI_ORGANIZATION_ID')
)

# Strip pretext and posttext.
def strip_pre_post(text):
  # Find the start index of the first '[' character
  # and the end index of the first ']' character after '['
  start = text.find('[')
  end = text.rfind(']')

  # Check if both brackets were found
  if start != -1 and end != -1 and end > start:
    # Extract the text from '[' to ']'
    content = text[start + 1 : end]
  else:
    content = text

  return content

# -----------------------------------------
# LLM Calls (OpenAI)
# -----------------------------------------
def propose_next_move(puzzle: Dict[str, dict]) -> NextMove:
    """
    Given a puzzle (JSON/dict) representing the sudoku board, call the OpenAI LLM
    to propose the next move. The function returns a NextMove instance.
    """
    # Convert the puzzle to a text representation
    puzzle_str = json.dumps(puzzle)

    # In-memory conversation store
    conversation_history = []

    # Call the LLM.
    assistant_message = call_llm(puzzle_str, conversation_history)
    
    # Ensure there is content for the assistant's message.  
    if assistant_message.content is None:
        assistant_message.content = "I am sorry, I am not able to process your request."
    else:
        # Extract the LLM's reply
        answer = strip_pre_post(
            assistant_message.content.strip()
        )

        try:
            data = json.loads(answer)
            next_move = NextMove(**data)
            return next_move
        except Exception as e:
            raise ValueError("CRITICAL: Failed to parse LLM response: " + str(e))

def call_llm(puzzle_str: str, conversation_history: List[str]):
    # Create a prompt for the LLM.
    system_prompt = (
        "You are an expert sudoku solving agent. Your task is to analyze the current puzzle board and propose the next move without modifying the board.\n"
        "Output only a JSON array containing one object with the keys:\n"
        "\"strategy\": the name of the solving technique used\n"
        "\"reasoning\": a detailed explanation of your reasoning\n"
        "\"steps\": a list of steps to achieve the strategy\n"
        "\"cell\": the cell reference (e.g. 'R1C2')\n"
        "\"action\": either 'assign' or 'eliminate'\n"
        "\"digit\": the digit to assign or eliminate\n\n"
    )

    user_prompt = (
        "Below is the current 9x9 Sudoku board represented as JSON string.\n"
        "Each cell is referenced by a cell reference \"RxCy\" which denotes Row x and Column y.\n"
        f"{puzzle_str}\n\n"
        "A solved cell is represented by its digit under the key \"value\".\n"
        "An unsolved cell has null for value but has a candidate list under the key \"candidates\", which contains a list of the possible digits that can be likely for this cell.\n"
        "Analyze the board and propose the next move based solely on the data provided.\n\n"
        "Output only a JSON array:\n"
        "[\n"
        "  {\n"
        "    \"strategy\": \"xxxx\",\n"
        "    \"reasoning\": \"xxxx\",\n" 
        "    \"steps\": [\n"
        "      { \"cell\": \"RxCy\",\n"
        "        \"action\": \"'assign' or 'eliminate'\",\n"
        "        \"digit\": x\n"
        "      },\n"
        "      { ... }\n"
        "  }\n"
        "]\n"
    )

    # Call the OpenAI Chat API
    try:
        response = client.chat.completions.create(
            messages = [
                {"role": "assistant", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ] + conversation_history,
            model = "o1-preview",
        )
    except Exception as e:
        raise Exception("OpenAI API call failed: " + str(e))

    return response.choices[0].message