from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, List, Optional
from models import (
    SudokuCell,
    PuzzleInput,
    PuzzleTextInput,
    CellAction,
    UnitRequest,
    RenderRequest,
    CheckResult,
    CellDigitRequest,
    CellRequest,
    SubsetCandidatesRequest,
    NextMove,
)
from llm_agent import propose_next_move
from helper import *
import ssl

app = FastAPI(
    title = "Sudoku Microservice",
    description = "API endpoints for interacting with a sudoku puzzle."
)
ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
ssl_context.load_cert_chain('certs/geraldyong-cert.pem', keyfile='certs/geraldyong-priv.pem')

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------------------------------
# Helper: Convert API-sent puzzle to internal format
# -------------------------------------------------
def convert_puzzle(puzzle_in: Dict[str, SudokuCell]) -> Dict[str, dict]:
    """Convert each SudokuCell model to a dictionary."""
    new_puzzle = {}
    for k, v in puzzle_in.items():
        # If already a dict, leave it; otherwise convert via .dict()
        new_puzzle[k] = v if isinstance(v, dict) else v.dict()
    return new_puzzle


# -----------------------------------------
# FastAPI Endpoints
# -----------------------------------------
@app.post("/loadPuzzle", response_model=Dict[str, dict])
def load_puzzle_endpoint(input_data: PuzzleTextInput):
    """
    Upload a puzzle as text (with spaces, underscores, or zeros) and return the JSON representation.
    """
    try:
        puzzle = read_puzzle_from_text(input_data.text)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return puzzle

@app.post("/computeCandidates", response_model=Dict[str, dict])
def compute_candidates_endpoint(input_data: PuzzleInput):
    puzzle_dict = convert_puzzle(input_data.puzzle)
    updated = compute_candidates(puzzle_dict)
    return updated

@app.post("/assignDigit", response_model=Dict[str, dict])
def assign_digit_endpoint(input_data: CellAction):
    puzzle_dict = convert_puzzle(input_data.puzzle)
    try:
        updated = assign_digit(puzzle_dict, input_data.cell_ref, input_data.digit)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return updated

@app.post("/eliminateDigit", response_model=Dict[str, dict])
def eliminate_digit_endpoint(input_data: CellAction):
    puzzle_dict = convert_puzzle(input_data.puzzle)
    try:
        updated = eliminate_digit(puzzle_dict, input_data.cell_ref, input_data.digit)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return updated

@app.post("/scanAndAssign", response_model=Dict[str, dict])
def scan_and_assign_endpoint(input_data: PuzzleInput):
    puzzle_dict = convert_puzzle(input_data.puzzle)
    updated = scan_and_assign(puzzle_dict)
    return updated

@app.post("/getUnit", response_model=Dict[str, dict])
def get_unit_endpoint(input_data: UnitRequest):
    puzzle_dict = convert_puzzle(input_data.puzzle)
    try:
        unit_data = get_unit(puzzle_dict, input_data.unit_ref)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return unit_data

@app.post("/renderPuzzle")
def render_puzzle_endpoint(input_data: RenderRequest):
    puzzle_dict = convert_puzzle(input_data.puzzle)
    rendered = render_puzzle(
        puzzle_dict,
        as_markdown=input_data.as_markdown,
        as_json=input_data.as_json,
        show_candidates=input_data.show_candidates,
    )
    return {"rendered": rendered}

@app.post("/checkStrict", response_model=CheckResult)
def check_strict_endpoint(input_data: PuzzleInput):
    puzzle_dict = convert_puzzle(input_data.puzzle)
    result = check_strict_consistency(puzzle_dict)
    if result:
        return CheckResult(result=True, message="Strict consistency check passed.")
    else:
        return CheckResult(result=False, message="Strict consistency check failed.")

@app.post("/checkCandidates", response_model=CheckResult)
def check_candidates_endpoint(input_data: PuzzleInput):
    puzzle_dict = convert_puzzle(input_data.puzzle)
    result = check_candidate_consistency(puzzle_dict)
    if result:
        return CheckResult(result=True, message="Candidate consistency check passed.")
    else:
        return CheckResult(result=False, message="Candidate consistency check failed.")
    
@app.post("/proposeNextMove", response_model=NextMove)
def propose_next_move_endpoint(input_data: PuzzleInput):
    """
    Given the JSON representation of a sudoku puzzle (with candidate lists),
    call the LLM-based agent to propose the next move. Returns the cell reference,
    strategy used, and the reasoning.
    """
    puzzle_dict = convert_puzzle(input_data.puzzle)

    try:
        next_move = propose_next_move(puzzle_dict)
        return next_move
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# -----------------------------------------
# Run with Uvicorn when executed directly.
# -----------------------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)