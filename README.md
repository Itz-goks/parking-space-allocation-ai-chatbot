# Parking Space Allocation AI Chatbot

A Python/Streamlit chatbot built from the supplied assignment:

**Development of a Heuristic Function for Parking Space Allocation**

## Features

- ChatGPT-style chat interface
- PDF-based retrieval using TF-IDF
- Questions about the assignment
- Heuristic parking-space recommendation
- Sample Slot P1, P2 and P3 data from the PDF
- Size mismatch, congestion and restriction penalties
- Hill Climbing explanation
- No paid API key required

## Heuristic

The assignment specifies:

`H(A) = W1(D) + W2(S) + W3(Cg) + W4(R)`

and example weights:

`H(A) = 1(D) + 30(S) + 20(Cg) + 100(R)`

where D is walking distance, S is size mismatch, Cg is congestion, and R is restriction.

Lower score is preferred.

## Install

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

## Run

```bash
streamlit run app.py
```

## Example prompts

```text
What is the heuristic function?
Explain Hill Climbing
What are the objectives?
Allocate parking for a student arriving by car
What are the limitations?
```

## Project structure

```text
parking_space_chatbot/
├── app.py
├── requirements.txt
├── README.md
├── data/
│   └── parking_slots.json
└── knowledge/
    └── Parking_Space_Allocation.pdf
```

## Important

The sample parking information reproduces the example in the supplied assignment. Replace the JSON data with actual campus parking information before treating it as a real parking system.
