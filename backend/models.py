from typing import Dict, List, Optional
from pydantic import BaseModel

# -----------------------------------------
# Pydantic Models for Sudoku Functions
# -----------------------------------------
class SudokuCell(BaseModel):
    value: Optional[int] = None  # Solved digit (1-9) or None if unsolved.
    candidates: List[int] = []   # Candidate digits list.

# -----------------------------------------
# Pydantic Models for API Inputs
# -----------------------------------------
# The puzzle is represented as a dict mapping cell keys (e.g. "R1C1") to SudokuCell
# For API endpoints we wrap the puzzle in a model.
class PuzzleInput(BaseModel):
    puzzle: Dict[str, SudokuCell]

class PuzzleTextInput(BaseModel):
    text: str

class CellAction(BaseModel):
    puzzle: Dict[str, SudokuCell]
    cell_ref: str
    digit: int

class UnitRequest(BaseModel):
    puzzle: Dict[str, SudokuCell]
    unit_ref: str  # e.g., "R1", "C5", or "B1"

class RenderRequest(BaseModel):
    puzzle: Dict[str, SudokuCell]
    as_markdown: bool = True
    as_json: bool = False
    show_candidates: bool = False

class CheckResult(BaseModel):
    result: bool
    message: Optional[str] = None

class CellDigitRequest(BaseModel):
    puzzle: Dict[str, SudokuCell]
    cell_ref: str
    digit: int

class CellRequest(BaseModel):
    puzzle: Dict[str, SudokuCell]
    cell_ref: str

class SubsetCandidatesRequest(BaseModel):
    puzzle: Dict[str, SudokuCell]
    cell_ref: str
    candidate_list: List[int]

# -----------------------------------------
# Pydantic Models for LLM
# -----------------------------------------
class NextStep(BaseModel):
    cell: str       # e.g. "R1C2"
    action: str     # e.g. "assign" or "eliminate"
    digit: int      # e.g. "the digit to assign or eliminate"

class NextMove(BaseModel):
    strategy: str   # e.g. "hidden singles", "naked pairs", etc.
    reasoning: str  # A detailed description of the reasoning
    steps: List[NextStep]