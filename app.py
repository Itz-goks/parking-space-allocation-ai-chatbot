
import json
import re
from pathlib import Path

import streamlit as st
from pypdf import PdfReader
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

BASE = Path(__file__).resolve().parent
PDF_PATH = BASE / "knowledge" / "Parking_Space_Allocation.pdf"
SLOTS_PATH = BASE / "data" / "parking_slots.json"

# Exact example weights from the supplied assignment:
# H(A) = 1(D) + 30(S) + 20(Cg) + 100(R)
W_DISTANCE = 1
W_SIZE = 30
W_CONGESTION = 20
W_RESTRICTION = 100


@st.cache_resource
def load_knowledge():
    reader = PdfReader(str(PDF_PATH))
    text = "\n".join((p.extract_text() or "") for p in reader.pages)
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    chunks, current = [], ""
    for paragraph in paragraphs:
        if len(current) + len(paragraph) + 2 <= 1200:
            current = (current + "\n\n" + paragraph).strip()
        else:
            if current:
                chunks.append(current)
            current = paragraph
    if current:
        chunks.append(current)

    vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2))
    matrix = vectorizer.fit_transform(chunks)
    return chunks, vectorizer, matrix


def retrieve(query, k=3):
    chunks, vectorizer, matrix = load_knowledge()
    q = vectorizer.transform([query])
    scores = cosine_similarity(q, matrix).ravel()
    idx = scores.argsort()[::-1][:k]
    return [(chunks[i], float(scores[i])) for i in idx if scores[i] > 0]


def load_slots():
    return json.loads(SLOTS_PATH.read_text(encoding="utf-8"))


def parse_vehicle_type(text):
    q = text.lower()
    if "two wheeler" in q or "two-wheeler" in q or "bike" in q or "scooter" in q:
        return "two-wheeler"
    if "bus" in q:
        return "bus"
    if "car" in q or "four wheeler" in q or "four-wheeler" in q:
        return "car"
    return None


def parse_user_type(text):
    q = text.lower()
    if "staff" in q or "faculty" in q:
        return "staff"
    if "visitor" in q or "guest" in q:
        return "visitor"
    if "student" in q:
        return "student"
    return None


def size_mismatch(slot, vehicle_type):
    if vehicle_type == "car":
        if slot["slot_type"] == "car":
            return 0
        if slot["slot_type"] == "large bay":
            return 1
        return 2
    if vehicle_type == "two-wheeler":
        if slot["slot_type"] == "two-wheeler":
            return 0
        if slot["slot_type"] == "car":
            return 1
        return 2
    if vehicle_type == "bus":
        return 0 if slot["slot_type"] == "large bay" else 2
    return 0


def restriction_penalty(slot, user_type):
    if user_type and user_type in slot.get("allowed_users", []):
        return 0
    return 1


def score_slot(slot, vehicle_type, user_type):
    s = size_mismatch(slot, vehicle_type)
    r = restriction_penalty(slot, user_type)
    cg = int(slot.get("congestion", 0))
    d = int(slot["distance_m"])
    score = W_DISTANCE*d + W_SIZE*s + W_CONGESTION*cg + W_RESTRICTION*r
    return {
        "slot": slot["name"],
        "zone": slot["zone"],
        "distance": d,
        "size_mismatch": s,
        "congestion": cg,
        "restriction": r,
        "heuristic": score
    }


def allocate(vehicle_type, user_type):
    slots = load_slots()
    available = [s for s in slots if s["status"].lower() == "free"]
    if user_type:
        # Keep restricted spaces in the candidate list so the score visibly
        # demonstrates the restriction penalty from the assignment.
        pass
    if not available:
        return [], "No free parking spaces are currently available."

    scored = [score_slot(s, vehicle_type, user_type) for s in available]
    scored.sort(key=lambda x: x["heuristic"])
    return scored, None


def direct_answer(q):
    ql = q.lower()
    if "formula" in ql or "heuristic function" in ql:
        return (
            "**Heuristic function from the assignment:**\n\n"
            "H(A) = W1(D) + W2(S) + W3(Cg) + W4(R)\n\n"
            "For the example weights:\n"
            "**H(A) = 1(D) + 30(S) + 20(Cg) + 100(R)**\n\n"
            "D = walking distance, S = size mismatch, Cg = congestion, "
            "and R = restriction penalty. Lower is better."
        )
    if "hill climbing" in ql:
        return (
            "Hill Climbing starts with an initial parking allocation and repeatedly "
            "looks for a neighboring allocation with a lower heuristic value. A neighbor "
            "can be created by moving one vehicle to another parking space or exchanging "
            "spaces between two vehicles. It stops when no better neighboring allocation exists."
        )
    if "objective" in ql or "objectives" in ql:
        return (
            "The objectives are to find a suitable parking space, reduce walking distance, "
            "match vehicle type with space size, avoid crowded lanes and entrances, avoid "
            "reserved/restricted spaces, and provide a good allocation without checking every possible allocation."
        )
    if "input" in ql or "inputs" in ql:
        return (
            "Inputs include vehicle type and arrival time, destination, user type "
            "(student/staff/visitor), parking-space type and location, availability, "
            "walking distance, congestion, and restrictions."
        )
    if "limitation" in ql or "limitations" in ql:
        return (
            "The assignment lists limitations including dependence on selected weights, "
            "changing congestion, a space being taken before arrival, the possibility of a "
            "Hill Climbing local optimum, and the need for updated occupancy information."
        )
    if "scope" in ql:
        return (
            "The approach can be used for college campuses, hostel areas and similar shared "
            "parking facilities. Possible extensions include live occupancy sensors, event-day "
            "rules, EV charging spaces and accessibility requirements."
        )
    return None


def answer(query):
    vehicle = parse_vehicle_type(query)
    user = parse_user_type(query)
    allocation_words = [
        "allocate", "recommend", "which slot", "which parking",
        "parking space", "choose a slot", "select a slot", "find parking"
    ]

    if vehicle and any(w in query.lower() for w in allocation_words):
        scores, error = allocate(vehicle, user)
        if error:
            return error, []
        best = scores[0]
        response = (
            f"### 🅿️ Recommended parking space: {best['slot']}\n\n"
            f"- Vehicle: **{vehicle}**\n"
            f"- User: **{user or 'not specified'}**\n"
            f"- Zone: **{best['zone']}**\n"
            f"- Walking distance: **{best['distance']} m**\n"
            f"- Size mismatch penalty (S): **{best['size_mismatch']}**\n"
            f"- Congestion penalty (Cg): **{best['congestion']}**\n"
            f"- Restriction penalty (R): **{best['restriction']}**\n"
            f"- Heuristic score: **{best['heuristic']}**\n\n"
            "The assignment defines this as a minimization problem, so a lower score is preferred.\n\n"
            "**Formula:** H(A) = 1(D) + 30(S) + 20(Cg) + 100(R)"
        )
        return response, scores

    direct = direct_answer(query)
    if direct:
        return direct, []

    retrieved = retrieve(query)
    if retrieved:
        context = "\n\n".join(chunk for chunk, score in retrieved)
        return (
            "### 📚 Based on the supplied parking-space assignment\n\n"
            + context[:3500]
            + "\n\nYou can ask me to explain this in simpler words."
        ), []

    return (
        "I couldn't find a reliable answer in the supplied PDF. "
        "Try asking about the heuristic function, objectives, inputs, worked example, "
        "Hill Climbing, advantages, limitations, or possible improvements."
    ), []


st.set_page_config(page_title="Parking Space Allocation AI Chatbot", page_icon="🅿️", layout="wide")

st.title("🅿️ Parking Space Allocation AI Chatbot")
st.caption("AI assignment chatbot + heuristic parking-space allocation")

with st.sidebar:
    st.header("Project")
    st.write(
        "This chatbot uses the uploaded parking-space allocation assignment "
        "as its knowledge source and implements its example heuristic."
    )
    st.divider()
    st.subheader("Heuristic")
    st.code("H(A) = 1(D) + 30(S) + 20(Cg) + 100(R)")
    st.caption("Lower score = more suitable allocation")
    st.divider()
    st.subheader("Try these")
    st.write("• What is the heuristic function?")
    st.write("• Explain Hill Climbing")
    st.write("• What are the objectives?")
    st.write("• Allocate parking for a student arriving by car")
    st.write("• What are the limitations?")

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg.get("scores"):
            st.dataframe(msg["scores"], use_container_width=True)

prompt = st.chat_input("Ask about the parking assignment or request a parking space...")

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    response, scores = answer(prompt)
    st.session_state.messages.append({"role": "assistant", "content": response, "scores": scores})

    with st.chat_message("assistant"):
        st.markdown(response)
        if scores:
            st.dataframe(scores, use_container_width=True)

st.divider()
st.caption("Knowledge source: Parking_Space_Allocation.pdf | Educational prototype")
