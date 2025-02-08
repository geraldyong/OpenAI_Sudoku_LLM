"use strict";

document.addEventListener("DOMContentLoaded", function () {
  // Global variables
  let currentPuzzle = {}; // Latest puzzle JSON from backend
  let selectedCell = "";  // e.g., "R3C5"
  let startTime = null;
  let timerInterval = null;
  const BASE_URL = "http://localhost:8000"; // Adjust if needed

  // History stacks for undo/redo
  let undoStack = [];
  let redoStack = [];

  // DOM Elements
  const manualInputDiv = document.getElementById("manual-input");
  const pasteInputDiv = document.getElementById("paste-input");
  const uploadInputDiv = document.getElementById("upload-input");
  const radioButtons = document.getElementsByName("inputType");
  const manualTable = document.getElementById("manual-table");
  const submitButton = document.getElementById("submit-puzzle");
  const submissionContainer = document.getElementById("submission-container");
  const activeButtons = document.getElementById("active-buttons");
  const newPuzzleBtn = document.getElementById("new-puzzle-btn");
  const puzzleTableContainer = document.getElementById("puzzle-table-container");
  const messageDiv = document.getElementById("message");
  const fileUploadInput = document.getElementById("file-upload");
  const modal = document.getElementById("modal");
  const modalClose = document.getElementById("modal-close");
  const modalCell = document.getElementById("modal-cell");
  const assignBtn = document.getElementById("assign-btn");
  const eliminateBtn = document.getElementById("eliminate-btn");
  const candidateContainer = document.getElementById("candidate-container");
  const timerDiv = document.getElementById("timer");
  const tilesDiv = document.getElementById("tiles");
  const undoBtn = document.getElementById("undo-btn");
  const redoBtn = document.getElementById("redo-btn");
  const downloadJsonBtn = document.getElementById("download-json");
  const downloadMdBtn = document.getElementById("download-md");
  const proposeMoveBtn = document.getElementById("propose-move-btn");
  const nextMoveDisplay = document.getElementById("next-move-display");

  // --- Create Manual Input Grid (9x9) ---
  function createManualTable() {
    manualTable.innerHTML = "";
    for (let r = 1; r <= 9; r++) {
      let row = document.createElement("tr");
      for (let c = 1; c <= 9; c++) {
        let cell = document.createElement("td");
        if (c % 3 === 0) cell.classList.add("block-right");
        if (r % 3 === 0) cell.classList.add("block-bottom");
        let input = document.createElement("input");
        input.type = "text";
        input.maxLength = 1;
        input.style.fontSize = "16px";
        input.style.textAlign = "center";
        input.addEventListener("input", function () {
          this.value = this.value.replace(/[^0-9_]/g, "");
        });
        cell.appendChild(input);
        row.appendChild(cell);
      }
      manualTable.appendChild(row);
    }
  }
  createManualTable();

  // --- Toggle Input Sections Based on Radio Button ---
  radioButtons.forEach(rb => {
    rb.addEventListener("change", function () {
      if (this.value === "manual") {
        manualInputDiv.classList.remove("hidden");
        pasteInputDiv.classList.add("hidden");
        uploadInputDiv.classList.add("hidden");
      } else if (this.value === "paste") {
        manualInputDiv.classList.add("hidden");
        pasteInputDiv.classList.remove("hidden");
        uploadInputDiv.classList.add("hidden");
      } else if (this.value === "upload") {
        manualInputDiv.classList.add("hidden");
        pasteInputDiv.classList.add("hidden");
        uploadInputDiv.classList.remove("hidden");
      }
    });
  });

  // --- Build Puzzle Text from Manual Table ---
  function buildPuzzleTextFromTable() {
    let lines = [];
    let rows = manualTable.getElementsByTagName("tr");
    for (let r = 0; r < rows.length; r++) {
      let inputs = rows[r].getElementsByTagName("input");
      let line = [];
      for (let c = 0; c < inputs.length; c++) {
        let val = inputs[c].value.trim();
        line.push(val === "" ? "_" : val);
      }
      lines.push(line.join(" "));
    }
    return lines.join("\n");
  }

  // --- Timer Functions ---
  function startTimer() {
    startTime = new Date();
    timerInterval = setInterval(() => {
      let now = new Date();
      let diff = Math.floor((now - startTime) / 1000);
      let hours = String(Math.floor(diff / 3600)).padStart(2, "0");
      let minutes = String(Math.floor((diff % 3600) / 60)).padStart(2, "0");
      let seconds = String(diff % 60).padStart(2, "0");
      timerDiv.textContent = `Time: ${hours}:${minutes}:${seconds}`;
    }, 1000);
  }

  function stopTimer() {
    clearInterval(timerInterval);
  }

  // --- Update Remaining Digits Display ---
  function updateRemainingDigits() {
    let counts = {};
    for (let d = 1; d <= 9; d++) {
      counts[d] = 0;
    }
    for (let r = 1; r <= 9; r++) {
      for (let c = 1; c <= 9; c++) {
        let key = `R${r}C${c}`;
        let cell = currentPuzzle[key];
        if (cell.value !== null && cell.value !== undefined) {
          counts[cell.value]++;
        }
      }
    }
    tilesDiv.innerHTML = "";
    for (let d = 1; d <= 9; d++) {
      if (counts[d] < 9) {
        let tile = document.createElement("div");
        tile.className = "tile";
        tile.textContent = d;
        tile.title = `Remaining: ${9 - counts[d]}`;
        tile.addEventListener("mouseover", () => {
          highlightByDigit(d);
        });
        tile.addEventListener("mouseout", () => {
          removeHighlightByDigit(d);
        });
        tilesDiv.appendChild(tile);
      }
    }
  }

  // --- Highlight and Remove Highlight on Board ---
  function highlightByDigit(digit) {
    document.querySelectorAll("#puzzle-table td").forEach(td => {
      let key = td.getAttribute("data-cell-key");
      let cell = currentPuzzle[key];
      if (!cell) return;
      if (cell.value == digit) {
        td.classList.add("tile-solved-highlight");
      } else if (cell.value === null && cell.candidates && cell.candidates.includes(digit)) {
        td.classList.add("tile-candidate-highlight");
      }
    });
  }

  function removeHighlightByDigit(digit) {
    document.querySelectorAll("#puzzle-table td").forEach(td => {
      td.classList.remove("tile-solved-highlight", "tile-candidate-highlight");
    });
  }

  // --- History Management ---
  function pushState() {
    undoStack.push(JSON.parse(JSON.stringify(currentPuzzle)));
    redoStack = [];
    updateHistoryButtons();
  }

  function updateHistoryButtons() {
    undoBtn.disabled = (undoStack.length === 0);
    redoBtn.disabled = (redoStack.length === 0);
  }

  undoBtn.addEventListener("click", () => {
    if (undoStack.length === 0) return;
    redoStack.push(JSON.parse(JSON.stringify(currentPuzzle)));
    currentPuzzle = undoStack.pop();
    renderPuzzle();
    updateHistoryButtons();
  });

  redoBtn.addEventListener("click", () => {
    if (redoStack.length === 0) return;
    undoStack.push(JSON.parse(JSON.stringify(currentPuzzle)));
    currentPuzzle = redoStack.pop();
    renderPuzzle();
    updateHistoryButtons();
  });

  // --- Submit Puzzle Event Handler ---
  submitButton.addEventListener("click", async () => {
    let inputType = document.querySelector('input[name="inputType"]:checked').value;
    let puzzleText = "";
    if (inputType === "manual") {
      puzzleText = buildPuzzleTextFromTable();
    } else if (inputType === "paste") {
      let pt = document.getElementById("puzzle-text");
      if (pt) {
        puzzleText = pt.value;
      }
    } else if (inputType === "upload") {
      if (fileUploadInput && fileUploadInput.files && fileUploadInput.files[0]) {
        puzzleText = await fileUploadInput.files[0].text();
      } else {
        alert("Please select a file.");
        return;
      }
    }
    try {
      const loadRes = await fetch(`${BASE_URL}/loadPuzzle`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: puzzleText })
      });
      if (!loadRes.ok) {
        const err = await loadRes.json();
        throw new Error(err.detail);
      }
      let puzzle = await loadRes.json();
      const candRes = await fetch(`${BASE_URL}/computeCandidates`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ puzzle })
      });
      if (!candRes.ok) {
        const err = await candRes.json();
        throw new Error(err.detail);
      }
      currentPuzzle = await candRes.json();
      renderPuzzle();
      messageDiv.textContent = "";
      // Hide submission container and show active buttons
      if (submissionContainer) 
        submissionContainer.classList.add("hidden");
      if (activeButtons) 
        activeButtons.classList.remove("hidden");
      startTimer();
      updateRemainingDigits();
      undoStack = [];
      redoStack = [];
      updateHistoryButtons();
    } catch (error) {
      alert("Error: " + error.message);
    }
  });

  // --- New Puzzle Button Handler ---
  newPuzzleBtn.addEventListener("click", () => {
    stopTimer();
    if (submissionContainer) submissionContainer.classList.remove("hidden");
    if (activeButtons) activeButtons.classList.add("hidden");
    puzzleTableContainer.innerHTML = "";
    messageDiv.textContent = "";
  });

  // --- Download Functionality ---
  function downloadFile(filename, content, type) {
    let blob = new Blob([content], { type: type });
    let url = URL.createObjectURL(blob);
    let a = document.createElement("a");
    a.href = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
  }

  function generateMarkdown() {
    let lines = [];
    for (let r = 1; r <= 9; r++) {
      let row = [];
      for (let c = 1; c <= 9; c++) {
        let key = `R${r}C${c}`;
        let cell = currentPuzzle[key];
        let val = (cell && cell.value != null) ? cell.value : "_";
        row.push(val);
      }
      let rowStr = row.slice(0, 3).join(" ") + " | " + row.slice(3, 6).join(" ") + " | " + row.slice(6).join(" ");
      lines.push(rowStr);
      if (r === 3 || r === 6) {
        lines.push("---------------------");
      }
    }
    return lines.join("\n");
  }

  downloadJsonBtn.addEventListener("click", () => {
    let jsonStr = JSON.stringify(currentPuzzle, null, 2);
    downloadFile("sudoku.json", jsonStr, "application/json");
  });

  downloadMdBtn.addEventListener("click", () => {
    let mdStr = generateMarkdown();
    downloadFile("sudoku.md", mdStr, "text/markdown");
  });

  // --- Propose Next Move Button Handler ---
  proposeMoveBtn.addEventListener("click", async () => {
    try {
      // Immediately display the right panel with "Thinking..." in flashing text.
      nextMoveDisplay.innerHTML = `<h3 class="flashing">Thinking...</h3>`;
      nextMoveDisplay.classList.remove("hidden");  // ensure it is visible

      const response = await fetch(`${BASE_URL}/proposeNextMove`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ puzzle: currentPuzzle })
      });
      if (!response.ok) {
        const err = await response.json();
        throw new Error(err.detail);
      }
      const nextMove = await response.json();
      
      // Build HTML for the steps list.
      let stepsHtml = "";
      if (Array.isArray(nextMove.steps) && nextMove.steps.length > 0) {
        stepsHtml = "<ul>" +
          nextMove.steps.map(step =>
            `<li><strong>Cell:</strong> ${step.cell}, <strong>Action:</strong> ${step.action}, <strong>Digit:</strong> ${step.digit}</li>`
          ).join("") +
          "</ul>";
      }
      
      nextMoveDisplay.innerHTML = `
        <h3>Next Move Suggestion</h3>
        <p><strong>Strategy:</strong> ${nextMove.strategy}</p>
        <p><strong>Reasoning:</strong> ${nextMove.reasoning}</p>
        <h4>Steps:</h4>
        ${stepsHtml}
      `;
      nextMoveDisplay.classList.remove("hidden");
    } catch (error) {
      alert("Error: " + error.message);
    }
  });

  // --- Render Puzzle Board ---
  function renderPuzzle() {
    // Hide next move display (in case it is visible)
    nextMoveDisplay.classList.add("hidden");

    puzzleTableContainer.innerHTML = "";
    const table = document.createElement("table");
    table.id = "puzzle-table";

    // Create header row: first empty header cell, then column headers (C1...C9)
    const headerRow = document.createElement("tr");
    headerRow.classList.add("header-row");
    let emptyTh = document.createElement("th");
    emptyTh.classList.add("header-cell");
    headerRow.appendChild(emptyTh);
    for (let c = 1; c <= 9; c++) {
      let th = document.createElement("th");
      th.classList.add("header-cell");
      th.textContent = "C" + c;
      th.style.textAlign = "bottom";  // align text to bottom
      headerRow.appendChild(th);
    }
    table.appendChild(headerRow);

    // Create rows R1 to R9. Each row begins with a header cell (e.g., "R1") then 9 board cells.
    for (let r = 1; r <= 9; r++) {
      const row = document.createElement("tr");
      let rowHeader = document.createElement("th");
      rowHeader.classList.add("header-cell");
      rowHeader.textContent = "R" + r;
      rowHeader.style.textAlign = "right"; // align text to right
      row.appendChild(rowHeader);
      for (let c = 1; c <= 9; c++) {
        const td = document.createElement("td");
        if (c % 3 === 0) td.classList.add("block-right");
        if (r % 3 === 0) td.classList.add("block-bottom");
        const cellKey = `R${r}C${c}`;
        td.setAttribute("data-cell-key", cellKey);
        const cell = currentPuzzle[cellKey];
        if (cell.value !== null && cell.value !== undefined) {
          td.textContent = cell.value;
        } else if (cell.candidates && cell.candidates.length > 0) {
          let sorted = cell.candidates.slice().sort((a, b) => a - b);
          td.textContent = "{" + sorted.join(", ") + "}";
        } else {
          td.textContent = "_";
        }
        td.addEventListener("mouseover", () => handleMouseOver(cellKey));
        td.addEventListener("mouseout", () => handleMouseOut());
        td.addEventListener("click", () => openModal(cellKey));
        row.appendChild(td);
      }
      table.appendChild(row);
    }
    puzzleTableContainer.appendChild(table);
    updateRemainingDigits();
    checkSolved();
  }

  // --- Check if Puzzle is Solved ---
  async function checkSolved() {
    let solved = true;
    for (let r = 1; r <= 9; r++) {
      for (let c = 1; c <= 9; c++) {
        let key = `R${r}C${c}`;
        let cell = currentPuzzle[key];
        if (cell.value === null || cell.value === undefined) {
          solved = false;
          break;
        }
      }
      if (!solved) break;
    }

    if (solved) {
      try {
        const response = await fetch(`${BASE_URL}/checkStrict`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ puzzle: currentPuzzle })
        });
        const data = await response.json();
        if (data.result) {
          messageDiv.textContent = "Congratulations! The puzzle is solved!";
          stopTimer();
        } else {
          messageDiv.textContent = "Puzzle appears solved but strict consistency check failed.";
        }
      } catch (error) {
        messageDiv.textContent = "Error in consistency check: " + error.message;
      }
    } else {
      messageDiv.textContent = "";
    }
  }

  // --- Hover Effects for Puzzle Cells ---
  function handleMouseOver(cellKey) {
    const [r, c] = cellKey.match(/\d+/g).map(Number);
    let relatedKeys = new Set();
    for (let i = 1; i <= 9; i++) {
      relatedKeys.add(`R${r}C${i}`);
      relatedKeys.add(`R${i}C${c}`);
    }
    let blockRow = Math.floor((r - 1) / 3) * 3 + 1;
    let blockCol = Math.floor((c - 1) / 3) * 3 + 1;
    for (let i = blockRow; i < blockRow + 3; i++) {
      for (let j = blockCol; j < blockCol + 3; j++) {
        relatedKeys.add(`R${i}C${j}`);
      }
    }
    document.querySelectorAll("#puzzle-table td").forEach(td => {
      const key = td.getAttribute("data-cell-key");
      if (relatedKeys.has(key)) {
        td.classList.add("hover-highlight");
      }
    });
    if (currentPuzzle[cellKey].value !== null && currentPuzzle[cellKey].value !== undefined) {
      let digit = currentPuzzle[cellKey].value;
      document.querySelectorAll("#puzzle-table td").forEach(td => {
        const key = td.getAttribute("data-cell-key");
        if (currentPuzzle[key].value == digit) {
          td.classList.add("same-digit-highlight");
        }
      });
    }
  }

  function handleMouseOut() {
    document.querySelectorAll("#puzzle-table td").forEach(td => {
      td.classList.remove("hover-highlight", "same-digit-highlight");
    });
  }

  // --- Modal Operations ---
  function openModal(cellKey) {
    selectedCell = cellKey;
    modalCell.textContent = `Cell ${cellKey}`;
    let modalButtons = document.getElementById("modal-buttons");
    if (modalButtons) modalButtons.style.display = "block";
    candidateContainer.innerHTML = "";
    modal.style.display = "block";
  }
  if (modalClose) {
    modalClose.addEventListener("click", () => { modal.style.display = "none"; });
  }
  window.addEventListener("click", (event) => { if (event.target === modal) modal.style.display = "none"; });

  // --- Show Candidate Options for Assignment ---
  assignBtn.addEventListener("click", () => {
    let cell = currentPuzzle[selectedCell];
    candidateContainer.innerHTML = "";
    let candidates = cell.candidates && cell.candidates.length > 0 ? cell.candidates : [];
    if (candidates.length === 0) {
      candidateContainer.textContent = "No candidates available.";
      return;
    }
    candidates.sort((a, b) => a - b).forEach(digit => {
      let btn = document.createElement("button");
      btn.textContent = digit;
      btn.className = "candidate-button";
      btn.addEventListener("click", () => performAssignment(digit));
      candidateContainer.appendChild(btn);
    });
    let modalButtons = document.getElementById("modal-buttons");
    if (modalButtons) modalButtons.style.display = "none";
  });

  // --- Show Candidate Options for Elimination ---
  eliminateBtn.addEventListener("click", () => {
    let cell = currentPuzzle[selectedCell];
    candidateContainer.innerHTML = "";
    let candidates = cell.candidates && cell.candidates.length > 0 ? cell.candidates : [];
    if (candidates.length === 0) {
      candidateContainer.textContent = "No candidates available.";
      return;
    }
    candidates.sort((a, b) => a - b).forEach(digit => {
      let btn = document.createElement("button");
      btn.textContent = digit;
      btn.className = "candidate-button";
      btn.addEventListener("click", () => performElimination(digit));
      candidateContainer.appendChild(btn);
    });
    let modalButtons = document.getElementById("modal-buttons");
    if (modalButtons) modalButtons.style.display = "none";
  });

  // --- Perform Assignment ---
  async function performAssignment(digit) {
    pushState();
    try {
      const response = await fetch(`${BASE_URL}/assignDigit`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ puzzle: currentPuzzle, cell_ref: selectedCell, digit: Number(digit) })
      });
      if (!response.ok) {
        const err = await response.json();
        throw new Error(err.detail);
      }
      currentPuzzle = await response.json();
      renderPuzzle();
      highlightCell(selectedCell);
    } catch (error) {
      alert("Error: " + error.message);
    }
    modal.style.display = "none";
    updateHistoryButtons();
  }

  // --- Perform Elimination ---
  async function performElimination(digit) {
    pushState();
    try {
      const response = await fetch(`${BASE_URL}/eliminateDigit`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ puzzle: currentPuzzle, cell_ref: selectedCell, digit: Number(digit) })
      });
      if (!response.ok) {
        const err = await response.json();
        throw new Error(err.detail);
      }
      currentPuzzle = await response.json();
      renderPuzzle();
      highlightCell(selectedCell);
    } catch (error) {
      alert("Error: " + error.message);
    }
    modal.style.display = "none";
    updateHistoryButtons();
  }

  // --- Highlight a Cell Briefly ---
  function highlightCell(cellKey) {
    let td = document.querySelector(`[data-cell-key="${cellKey}"]`);
    if (td) {
      td.classList.add("highlight");
      setTimeout(() => td.classList.remove("highlight"), 1000);
    }
  }
});
