
import streamlit as st
import json
import re
from groq import Groq

# ---------------- PAGE SETTINGS ----------------
st.set_page_config(
    page_title="QuizCraft AI | Quiz Generator",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------------- PROFESSIONAL DESIGN ----------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

.stApp {
    background: linear-gradient(135deg, #0b1020, #15152e, #101827);
    color: #f1f5f9;
}

.block-container {
    max-width: 1150px;
    padding-top: 2rem;
    padding-bottom: 4rem;
}

.hero {
    padding: 35px 25px;
    border-radius: 24px;
    text-align: center;
    background: linear-gradient(120deg, #312e81, #6d28d9, #2563eb);
    background-size: 200% 200%;
    animation: gradientMove 8s ease infinite;
    box-shadow: 0 12px 40px rgba(109,40,217,.2);
    margin-bottom: 25px;
}

.hero h1 {
    font-size: clamp(30px, 5vw, 48px);
    font-weight: 800;
    color: white;
    margin-bottom: 8px;
}

.hero p {
    color: #e0e7ff;
    font-size: 16px;
}

@keyframes gradientMove {
    0% {background-position: 0% 50%;}
    50% {background-position: 100% 50%;}
    100% {background-position: 0% 50%;}
}

div[data-testid="stForm"], div[data-testid="stVerticalBlockBorderWrapper"] {
    border-radius: 16px;
}

.question-card {
    padding: 22px;
    margin: 15px 0;
    border: 1px solid rgba(139, 92, 246, .35);
    border-radius: 18px;
    background: rgba(30, 41, 59, .75);
    animation: fadeIn .6s ease both;
}

@keyframes fadeIn {
    from {opacity: 0; transform: translateY(12px);}
    to {opacity: 1; transform: translateY(0);}
}

.info-card {
    padding: 18px;
    background: rgba(99, 102, 241, .12);
    border: 1px solid rgba(129, 140, 248, .25);
    border-radius: 15px;
    text-align: center;
}

div.stButton > button[kind="primary"],
div.stFormSubmitButton > button {
    border-radius: 12px;
    background: linear-gradient(100deg, #7c3aed, #4f46e5);
    color: white;
    border: none;
    font-weight: 700;
    min-height: 45px;
    transition: all .25s ease;
}

div.stButton > button:hover,
div.stFormSubmitButton > button:hover {
    transform: translateY(-2px);
    box-shadow: 0 5px 20px rgba(124,58,237,.3);
}

footer {visibility: hidden;}

#MainMenu {visibility: hidden;}

</style>
""", unsafe_allow_html=True)

# ---------------- SESSION STATE ----------------
if "quiz" not in st.session_state:
    st.session_state.quiz = None

if "answers" not in st.session_state:
    st.session_state.answers = {}

if "submitted" not in st.session_state:
    st.session_state.submitted = False

# ---------------- HEADER ----------------
st.markdown("""
<div class="hero">
    <h1>🧠 QuizCraft AI</h1>
    <p>Learn smarter. Practice better. Test your knowledge.</p>
    <p>✨ Your personal AI-powered quiz studio ✨</p>
</div>
""", unsafe_allow_html=True)

# ---------------- SIDEBAR ----------------
with st.sidebar:
    st.markdown("## ⚙️ Quiz Settings")
    st.caption("Customize your learning experience.")

    difficulty = st.selectbox(
        "🎯 Difficulty Level",
        ["Normal", "Medium", "High"],
        help="Normal = basic, Medium = intermediate, High = advanced"
    )

    language = st.selectbox(
        "🌐 Quiz Language",
        ["English", "Roman Urdu", "Urdu"]
    )

    st.markdown("---")
    st.markdown("### 📚 Quiz Features")
    st.markdown("""
    - 20 AI-generated questions
    - Four options per question
    - Individual hints
    - Score calculation
    - Answer key and explanations
    - Three difficulty levels
    """)
    st.caption("Powered by Streamlit + Groq AI")

# ---------------- API CLIENT ----------------
def get_client():
    try:
        api_key = st.secrets["GROQ_API_KEY"]
    except Exception:
        return None

    if not api_key:
        return None

    return Groq(api_key=api_key)

# ---------------- GENERATE QUIZ ----------------
def generate_quiz(topic, level, quiz_language):
    client = get_client()

    if client is None:
        st.error(
            "Groq API key is missing. Add GROQ_API_KEY "
            "in your Streamlit app Secrets."
        )
        return None

    prompt = f"""
You are an expert educational quiz creator.

Create EXACTLY 20 multiple-choice questions about:
TOPIC: {topic}

DIFFICULTY: {level}
LANGUAGE: {quiz_language}

Difficulty rules:
- Normal: basic knowledge and simple concepts.
- Medium: understanding, application, and comparisons.
- High: advanced reasoning and challenging concepts.

Requirements:
1. Every question must have exactly four options.
2. Every question must have exactly one correct answer.
3. Each question must have a useful hint that DOES NOT reveal
   the correct answer.
4. Include a clear explanation for every correct answer.
5. Cover different aspects of the topic.
6. Use accurate, educational information.
7. Questions, options, hints, and explanations must be in
   the requested language.
8. Do not repeat questions.
9. Return valid JSON only. No Markdown fences or extra text.

Use this exact JSON structure:
{{
  "title": "Quiz title",
  "topic": "{topic}",
  "difficulty": "{level}",
  "questions": [
    {{
      "question": "Question text",
      "options": ["Option A", "Option B", "Option C", "Option D"],
      "answer": "Exact text of the correct option",
      "hint": "A helpful clue without the answer",
      "explanation": "Why the correct answer is right"
    }}
  ]
}}

The questions array must contain exactly 20 objects.
The answer must exactly match one of the four options.
"""

    try:
        response = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[
                {
                    "role": "system",
                    "content": "Return only valid JSON for educational quizzes."
                },
                {"role": "user", "content": prompt}
            ],
            temperature=0.6,
            max_completion_tokens=12000
        )

        content = response.choices[0].message.content.strip()

        # Remove accidental Markdown fences
        content = re.sub(
            r"^```(?:json)?\s*|\s*```$",
            "",
            content
        )

        data = json.loads(content)

        questions = data.get("questions", [])

        if len(questions) != 20:
            st.error(
                f"The AI returned {len(questions)} questions "
                "instead of 20. Please generate the quiz again."
            )
            return None

        # Validate every question
        for question in questions:
            if not all(
                key in question
                for key in [
                    "question", "options", "answer",
                    "hint", "explanation"
                ]
            ):
                st.error("The AI returned an incomplete question.")
                return None

            options = question["options"]
            answer = question["answer"]

            if (
                not isinstance(options, list)
                or len(options) != 4
                or len(set(options)) != 4
                or answer not in options
            ):
                st.error(
                    "The AI returned invalid options or an answer. "
                    "Please try again."
                )
                return None

        return data

    except Exception as error:
        st.error(
            "Quiz generation failed. Check your API key, "
            "model availability, internet connection, and "
            "Groq usage limits."
        )
        with st.expander("Technical details"):
            st.code(str(error))
        return None

# ---------------- TOPIC INPUT ----------------
st.markdown("## 🚀 Create Your Quiz")
st.write("Enter a topic, choose a difficulty, and let AI build your quiz.")

with st.form("quiz_form"):
    topic = st.text_input(
        "📖 Enter your topic",
        placeholder="e.g. Photosynthesis, Artificial Intelligence, Physics...",
        max_chars=200
    )

    submitted_form = st.form_submit_button(
        "✨ Generate 20 Questions",
        type="primary",
        use_container_width=True
    )

if submitted_form:
    if not topic.strip():
        st.warning("Please enter a topic first.")
    else:
        with st.spinner("🪄 Creating your personalized quiz..."):
            quiz = generate_quiz(
                topic.strip(),
                difficulty,
                language
            )

        if quiz:
            st.session_state.quiz = quiz
            st.session_state.answers = {}
            st.session_state.submitted = False
            st.rerun()

# ---------------- QUIZ DISPLAY ----------------
quiz = st.session_state.quiz

if quiz:
    st.markdown("---")
    st.markdown(f"## 📘 {quiz.get('title', 'Your Quiz')}")
    st.caption(
        f"Topic: {topic if topic.strip() else quiz.get('topic', 'Custom topic')} "
        f"| Difficulty: {quiz.get('difficulty', difficulty)} "
        f"| Total questions: 20"
    )

    st.markdown("""
    <div class="info-card">
        💡 Choose one answer for each question. Open a hint whenever you need help.
    </div>
    """, unsafe_allow_html=True)

    # Answers are locked until the user submits the quiz
    with st.form("answer_form"):
        for index, question in enumerate(
            quiz["questions"]
        ):
            st.markdown(
                f'<div class="question-card">'
                f'<b>QUESTION {index + 1} OF 20</b>'
                f'</div>',
                unsafe_allow_html=True
            )

            st.markdown(f"### {question['question']}")

            st.radio(
                "Select your answer:",
                options=question["options"],
                key=f"answer_{index}",
                index=None,
                disabled=st.session_state.submitted,
                label_visibility="collapsed"
            )

            with st.expander(f"💡 Hint for question {index + 1}"):
                st.info(question["hint"])

            st.markdown("---")

        if not st.session_state.submitted:
            submitted_answers = st.form_submit_button(
                "✅ Submit Quiz & Reveal Answers",
                type="primary",
                use_container_width=True
            )
        else:
            submitted_answers = False

    if submitted_answers:
        st.session_state.answers = {
            i: st.session_state.get(f"answer_{i}")
            for i in range(20)
        }
        st.session_state.submitted = True
        st.rerun()

    # ---------------- RESULTS ----------------
    if st.session_state.submitted:
        questions = quiz["questions"]

        score = sum(
            1 for i, question in enumerate(questions)
            if st.session_state.answers.get(i) == question["answer"]
        )

        percentage = score * 5

        st.balloons()
        st.markdown("---")
        st.markdown("## 🏆 Your Quiz Results")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Your Score", f"{score} / 20")

        with col2:
            st.metric("Percentage", f"{percentage}%")

        with col3:
            st.metric("Difficulty", quiz.get("difficulty", difficulty))

        st.progress(percentage / 100)

        if percentage >= 80:
            st.success("Excellent work! You have a strong understanding of this topic.")
        elif percentage >= 50:
            st.info("Good effort! Review the explanations to improve further.")
        else:
            st.warning("Keep practicing! Review the answers and try again.")

        st.markdown("## 📝 Answer Key & Explanations")
        st.write("Review every question, your response, and the correct answer.")

        for index, question in enumerate(questions):
            selected = st.session_state.answers.get(index)
            correct = selected == question["answer"]

            with st.expander(
                f"{'✅' if correct else '❌'} "
                f"Question {index + 1}: "
                f"{'Correct' if correct else 'Review this answer'}"
            ):
                st.markdown(f"**Question:** {question['question']}")
                st.write(f"**Your answer:** {selected or 'Not answered'}")
                st.success(f"**Correct answer:** {question['answer']}")
                st.write(f"**Explanation:** {question['explanation']}")
                st.caption(f"Hint: {question['hint']}")

        st.markdown("---")

        if st.button(
            "🔄 Create Another Quiz",
            type="primary",
            use_container_width=True
        ):
            st.session_state.quiz = None
            st.session_state.answers = {}
            st.session_state.submitted = False
            st.rerun()

# ---------------- FOOTER ----------------
st.markdown("---")
st.markdown(
    "<div style='text-align:center; color:#94a3b8;'>"
    "QuizCraft AI · Learn • Practice • Improve"
    "</div>",
    unsafe_allow_html=True
)
