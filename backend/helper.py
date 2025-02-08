from typing import Dict, List, Optional, Union
from models import SudokuCell
import json
import re

# -----------------------------------------
# Core Sudoku Functions (Logic)
# -----------------------------------------
def read_puzzle_from_text(text: str) -> Dict[str, dict]:
    """
    Parses a Sudoku puzzle from either a multiline text string or from a JSON string.
    
    Auto-detects if the input text is a JSON string of the following format:
    
    {
      "R1C1": {"value": 4, "candidates": []},
      "R1C2": {"value": 7, "candidates": []},
      ...
    }
    
    If so, validates each cell using the SudokuCell model and returns the puzzle.
    Otherwise, it parses the text as a traditional puzzle (with rows of tokens).
    """
    # Attempt to interpret the text as JSON.
    try:
        data = json.loads(text)
        # Check that the data is a dict and that keys follow the expected pattern.
        if isinstance(data, dict):
            valid = True
            for key, cell in data.items():
                if not re.match(r"R\d+C\d+", key):
                    valid = False
                    break
                try:
                    # Validate the cell data using the Pydantic model.
                    SudokuCell(**cell)
                except ValidationError:
                    valid = False
                    break
            if valid:
                return data
    except Exception:
        # If JSON parsing fails, fall through to traditional parsing.
        pass

    # Fallback: parse the text as a traditional multiline puzzle.
    puzzle: Dict[str, dict] = {}
    rows = []
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("-"):
            continue
        # Remove separators like '|'
        line = line.replace("|", "")
        tokens = line.split()
        if tokens:
            rows.append(tokens)
    if len(rows) != 9:
        raise ValueError(f"Expected 9 rows in puzzle, got {len(rows)}")
    for row_idx, tokens in enumerate(rows, start=1):
        if len(tokens) != 9:
            raise ValueError(f"Expected 9 tokens in row {row_idx}, got {len(tokens)}")
        for col_idx, token in enumerate(tokens, start=1):
            cell_key = f"R{row_idx}C{col_idx}"
            if token in ("_", "0"):
                cell_value = None
            else:
                try:
                    cell_value = int(token)
                except ValueError:
                    raise ValueError(f"Invalid token '{token}' in cell {cell_key}.")
            # Create a SudokuCell model instance (with an empty candidate list)
            cell_model = SudokuCell(value=cell_value, candidates=[])
            puzzle[cell_key] = cell_model.dict()
    return puzzle

def get_cell_contents(puzzle: Dict[str, dict], cell_ref: str) -> List[int]:
    """
    Given a puzzle (a dictionary) and a cell reference (e.g., "R1C1"),
    return a string representation of that cell's contents.
      - If the cell has a solved value, return that digit as a string.
      - Otherwise, return the candidate list as a comma-separated string 
        enclosed in curly braces (e.g., "{1, 2, 3}").
    """
    cell = puzzle.get(cell_ref)
    if cell is None:
        raise ValueError(f"Cell {cell_ref} not found in the puzzle.")
    
    if cell.get("value") is not None:
        #return str(cell["value"])
        return cell["value"]
    else:
        return cell.get("candidates", [])
        #candidates = cell.get("candidates", [])
        #if candidates:
            #return "{" + ", ".join(str(d) for d in sorted(candidates)) + "}"
        #else:
        #    return "_"

def get_units_for_cell(cell_ref: str) -> Dict[str, List[str]]:
    """
    Given a cell reference (e.g. "R4C1"), returns a dict with keys:
      - 'row': all cell keys in the same row,
      - 'col': all cell keys in the same column,
      - 'block': all cell keys in the same 3×3 block.
    """
    m = re.match(r"R(\d+)C(\d+)", cell_ref)
    if not m:
        raise ValueError(f"Invalid cell reference: {cell_ref}")
    row_num = int(m.group(1))
    col_num = int(m.group(2))
    row_unit = [f"R{row_num}C{c}" for c in range(1, 10)]
    col_unit = [f"R{r}C{col_num}" for r in range(1, 10)]
    block_row = (row_num - 1) // 3
    block_col = (col_num - 1) // 3
    row_start = block_row * 3 + 1
    col_start = block_col * 3 + 1
    block_unit = [
        f"R{r}C{c}"
        for r in range(row_start, row_start + 3)
        for c in range(col_start, col_start + 3)
    ]
    return {"row": row_unit, "col": col_unit, "block": block_unit}

def compute_candidates(puzzle: Dict[str, dict]) -> Dict[str, dict]:
    """
    For each unsolved cell, compute candidate digits (those not already in its row,
    column, or block) and update the puzzle in place.
    """
    for cell_ref, cell in puzzle.items():
        if cell["value"] is not None:
            cell["candidates"] = []
            continue
        used_digits = set()
        units = get_units_for_cell(cell_ref)
        for unit in units.values():
            for peer in unit:
                peer_value = puzzle[peer]["value"]
                if peer_value is not None:
                    used_digits.add(peer_value)
        cell["candidates"] = [d for d in range(1, 10) if d not in used_digits]
    return puzzle

def assign_digit(puzzle: Dict[str, dict], cell_ref: str, digit: int) -> Dict[str, dict]:
    """
    Assigns a digit to a cell if it is unsolved and the digit is in its candidate list.
    Also eliminates that digit from the candidate lists of all peers (row, col, block)
    and auto-assigns any peers reduced to a single candidate.
    """
    cell = puzzle.get(cell_ref)
    if cell is None:
        raise ValueError(f"Cell {cell_ref} not found in the puzzle.")
    if cell["value"] is not None:
        raise ValueError(f"Cell {cell_ref} is already solved with value {cell['value']}.")
    if digit not in cell["candidates"]:
        raise ValueError(f"Digit {digit} is not a candidate for cell {cell_ref}.")
    cell["value"] = digit
    cell["candidates"] = []
    units = get_units_for_cell(cell_ref)
    for unit in units.values():
        for peer_ref in unit:
            if peer_ref == cell_ref:
                continue
            peer = puzzle[peer_ref]
            if peer["value"] is None and digit in peer["candidates"]:
                peer["candidates"].remove(digit)
                if len(peer["candidates"]) == 1:
                    sole_candidate = peer["candidates"][0]
                    assign_digit(puzzle, peer_ref, sole_candidate)
    return puzzle

def eliminate_digit(puzzle: Dict[str, dict], cell_ref: str, digit: int) -> Dict[str, dict]:
    """
    Eliminates a digit from a cell’s candidate list (if the cell is unsolved).
    If the elimination leaves only one candidate, that candidate is automatically assigned.
    """
    cell = puzzle.get(cell_ref)
    if cell is None:
        raise ValueError(f"Cell {cell_ref} not found.")
    if cell["value"] is not None:
        raise ValueError(f"Cannot eliminate digit from cell {cell_ref} because it is already solved.")
    if digit in cell["candidates"]:
        cell["candidates"].remove(digit)
        # If only one candidate remains, assign that candidate automatically.
        if len(cell["candidates"]) == 1:
            sole_candidate = cell["candidates"][0]
            assign_digit(puzzle, cell_ref, sole_candidate)
    return puzzle

def scan_and_assign(puzzle: Dict[str, dict]) -> Dict[str, dict]:
    """
    Repeatedly scans the board and assigns a digit to any unsolved cell that has
    exactly one candidate.
    """
    progress = True
    while progress:
        progress = False
        for cell_ref, cell in list(puzzle.items()):
            if cell["value"] is None and len(cell["candidates"]) == 1:
                candidate = cell["candidates"][0]
                assign_digit(puzzle, cell_ref, candidate)
                progress = True
    return puzzle

def get_unit(puzzle: Dict[str, dict], unit_ref: str) -> Dict[str, dict]:
    """
    Returns a dictionary of cells for a given unit reference:
      - "R1" returns row 1,
      - "C1" returns column 1,
      - "B1" returns block 1 (top-left block).
    """
    unit_type = unit_ref[0].upper()
    try:
        index = int(unit_ref[1:])
    except ValueError:
        raise ValueError(f"Invalid unit reference: {unit_ref}")
    if unit_type == "R":
        keys = [f"R{index}C{c}" for c in range(1, 10)]
    elif unit_type == "C":
        keys = [f"R{r}C{index}" for r in range(1, 10)]
    elif unit_type == "B":
        row_start = ((index - 1) // 3) * 3 + 1
        col_start = ((index - 1) % 3) * 3 + 1
        keys = [f"R{r}C{c}" for r in range(row_start, row_start + 3)
                              for c in range(col_start, col_start + 3)]
    else:
        raise ValueError("Unit reference must start with 'R', 'C', or 'B'.")
    return {k: puzzle[k] for k in keys if k in puzzle}

def check_strict_consistency(puzzle: Dict[str, dict]) -> bool:
    """
    In every unit (row, column, block), ensures no solved digit appears more than once.
    """
    unit_refs = [f"R{i}" for i in range(1, 10)] + \
                [f"C{i}" for i in range(1, 10)] + \
                [f"B{i}" for i in range(1, 10)]
    for unit_ref in unit_refs:
        unit_cells = get_unit(puzzle, unit_ref)
        seen = {}
        for cell_key, cell in unit_cells.items():
            if cell["value"] is not None:
                digit = cell["value"]
                if digit in seen:
                    return False
                seen[digit] = cell_key
    return True

def check_candidate_consistency(puzzle: Dict[str, dict]) -> bool:
    """
    In every unit, for every digit 1-9, either the digit is solved in that unit
    or it appears in at least one unsolved cell's candidate list.
    """
    unit_refs = [f"R{i}" for i in range(1, 10)] + \
                [f"C{i}" for i in range(1, 10)] + \
                [f"B{i}" for i in range(1, 10)]
    for unit_ref in unit_refs:
        unit_cells = get_unit(puzzle, unit_ref)
        solved_digits = {cell["value"] for cell in unit_cells.values() if cell["value"] is not None}
        for d in range(1, 10):
            if d not in solved_digits:
                if not any(d in cell["candidates"] for cell in unit_cells.values() if cell["value"] is None):
                    return False
    return True

def render_puzzle(
    puzzle: Dict[str, dict],
    *,
    as_markdown: bool = False,
    as_json: bool = False,
    show_candidates: bool = False
) -> str:
    """
    Renders the puzzle into a string.
    
    Parameters:
      - puzzle: The internal puzzle dictionary.
      - as_markdown: If True, output a Markdown table (with row and column headers).
      - as_json: If True, output a JSON string representation.
      - show_candidates: For unsolved cells, if True, include the sorted candidate list;
                         otherwise, unsolved cells are represented as an underscore ("_").
    
    (Note: The standalone asterisk (*) in the parameter list requires all parameters following the asterisk 
    to be passed as keyword arguments rather than positional arguments.)
    
    Returns a string representing the puzzle.
    
    If as_json is True, the function returns a JSON string in the format:
      {
         "R1C1": {"value": 4, "candidates": []},
         "R1C2": {"value": 7, "candidates": []},
         ...
      }
    
    Otherwise, it returns a textual representation (Markdown table if as_markdown is True,
    or a plain text representation with 3x3 block separators).
    """
    if as_json:
        return json.dumps(puzzle, indent=2)
    
    elif as_markdown:
        # Create header row
        header = [""] + [f"C{col}" for col in range(1, 10)]
        table_rows = [header, ["---"] * len(header)]
        for r in range(1, 10):
            row_label = f"R{r}"
            row_data = [row_label]
            for c in range(1, 10):
                cell = puzzle[f"R{r}C{c}"]
                if cell["value"] is not None:
                    cell_str = str(cell["value"])
                else:
                    if show_candidates and cell["candidates"]:
                        candidates = sorted(cell["candidates"])
                        cell_str = "{" + ", ".join(str(d) for d in candidates) + "}"
                    else:
                        cell_str = "_"
                row_data.append(cell_str)
            table_rows.append(row_data)
        # Build a Markdown table
        lines = ["| " + " | ".join(row) + " |" for row in table_rows]
        return "\n".join(lines)
    
    else:
        # Plain text representation with 3x3 block separators.
        lines = []
        for r in range(1, 10):
            row_cells = []
            for c in range(1, 10):
                cell = puzzle[f"R{r}C{c}"]
                if cell["value"] is not None:
                    cell_str = str(cell["value"])
                else:
                    if show_candidates and cell["candidates"]:
                        candidates = sorted(cell["candidates"])
                        cell_str = "{" + ", ".join(str(d) for d in candidates) + "}"
                    else:
                        cell_str = "_"
                row_cells.append(cell_str)
            # Group the row into three groups (for block separation)
            row_line = " | ".join([" ".join(row_cells[i:i+3]) for i in range(0, 9, 3)])
            lines.append(row_line)
            if r % 3 == 0 and r < 9:
                lines.append("-" * len(row_line))
        return "\n".join(lines)