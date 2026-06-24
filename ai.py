
import os
from dotenv import load_dotenv
from groq import Groq

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))
def analyze_resume(resume_text, user_goal):
    prompt = f"""
You are an expert technical recruiter and career coach with 10+ years of experience.

A candidate wants to become: "{user_goal}"

Analyze their resume and return ONLY this JSON structure. No markdown, no extra text.

{{
  "score": 7,
  "summary": "2-3 line honest assessment of candidate fit for {user_goal}",
  "ats_score": {{
    "score": 72,
    "verdict": "Average",
    "reasons": ["reason1", "reason2", "reason3"],
    "improvements": ["tip1", "tip2", "tip3"]
  }},
  "skills": ["skill1", "skill2"],
  "missing_skills": ["skill1", "skill2"],
  "roadmap": [
    {{
      "skill": "Skill Name",
      "description": "Why this matters for {user_goal}",
      "resources": ["Resource 1", "Resource 2"]
    }}
  ],
  "interview_questions": ["question1?", "question2?"]
}}

RULES:
- skills: ONLY what is explicitly in the resume
- missing_skills: important for "{user_goal}" but absent from resume
- roadmap: max 6 items, resources always a list
- interview_questions: 5 specific questions for "{user_goal}"
- ats_score.score: 0-100 integer
- ats_score.verdict: one of "Poor", "Average", "Good", "Excellent"
- score: 1-10 overall fit rating

Resume:
{resume_text}
"""

    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            temperature=0.2,
            max_tokens=2048,
            messages=[
                {
                    "role": "system",
                    "content": f"You are a strict technical recruiter for {user_goal} roles. Respond with valid JSON only. No markdown. No explanation."
                },
                {"role": "user", "content": prompt}
            ]
        )

        content = response.choices[0].message.content.strip()

        # markdown fences clean karo
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]

        start = content.find("{")
        end = content.rfind("}") + 1
        parsed = json.loads(content[start:end])

        # roadmap resources normalize
        for item in parsed.get("roadmap", []):
            if isinstance(item.get("resources"), str):
                item["resources"] = [item["resources"]]
            elif not isinstance(item.get("resources"), list):
                item["resources"] = []

        # ats_score missing ho toh default
        if "ats_score" not in parsed:
            parsed["ats_score"] = {
                "score": 0,
                "verdict": "Could not evaluate",
                "reasons": [],
                "improvements": []
            }

        return parsed

    except json.JSONDecodeError as e:
        return {
            "score": 0,
            "summary": "Could not parse AI response.",
            "ats_score": {"score": 0, "verdict": "Error", "reasons": [], "improvements": []},
            "skills": [],
            "missing_skills": [],
            "roadmap": [],
            "interview_questions": [],
            "error": f"JSON parse error: {str(e)}"
        }
    except Exception as e:
        return {
            "score": 0,
            "summary": "An error occurred.",
            "ats_score": {"score": 0, "verdict": "Error", "reasons": [], "improvements": []},
            "skills": [],
            "missing_skills": [],
            "roadmap": [],
            "interview_questions": [],
            "error": str(e)
        }


if __name__ == "__main__":
    sample = "John Doe\nSkills: Python, SQL, Pandas\nExperience: 1 year Data Analyst internship"
    result = analyze_resume(sample, "Data Scientist")
    print(json.dumps(result, indent=2))