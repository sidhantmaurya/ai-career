from flask import Flask,render_template,request,redirect,session
from db import Base, engine, SessionLocal
import PyPDF2
import model
import docx
import json
from ai import analyze_resume
app = Flask(__name__)
app.secret_key = "secret123"

Base.metadata.create_all(bind=engine)

#HOME 
@app.route("/")
def home():
    if "user" in session:
        return redirect("/dashboard")
    return redirect("/login")

#signup
@app.route("/signup", methods=["GET", "POST"])
def signup():
    db = SessionLocal()
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        existing_user = db.query(model.user).filter_by(email=email).first()

        if existing_user:
            return render_template("signup.html", error="User already exists")

        user = model.user(email=email, password=password)
        db.add(user)
        db.commit()
        return redirect("/login")
    return render_template("signup.html")

#login
@app.route("/login", methods=["GET", "POST"])
def login():
    db = SessionLocal()
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        user = db.query(model.user).filter_by(email=email, password=password).first()

        if user:
            session["user"] = user.email
            return redirect("/dashboard")
        else:
            return render_template("login.html", error="Invalid credentials")

    return render_template("login.html")

#dashboard
@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():
    if "user" not in session:
        return redirect("/login")

    result = None

    if request.method == "POST":
        user_goal = request.form.get("role")
        resume_text = request.form.get("resume")
        file = request.files.get("file")

        if file and file.filename != "":
            if file.filename.endswith(".pdf"):
                try:
                    pdf_reader = PyPDF2.PdfReader(file)
                    text = ""
                    for page in pdf_reader.pages:
                        text += page.extract_text() or ""
                    resume_text = text
                except Exception as e:
                    result = {"error": f"PDF error: {str(e)}"}

            elif file.filename.endswith(".docx"):
                try:
                    doc = docx.Document(file)
                    text = ""
                    for para in doc.paragraphs:
                        text += para.text + "\n"
                    resume_text = text
                except Exception as e:
                    result = {"error": f"Docx error: {str(e)}"}

        if resume_text and user_goal and result is None:
            try:
                result = analyze_resume(resume_text, user_goal)

                db = SessionLocal()
                user = db.query(model.user).filter_by(email=session["user"]).first()

                report = model.reports(
                    user_id=user.id,
                    resume_text=resume_text,
                    result=json.dumps(result)
                )
                db.add(report)
                db.commit()
            except Exception as e:
                result = {"error": f"AI error: {str(e)}"}

    # result sanitize karo
    if not result:
        result = {}
    if not result.get("ats_score"):
        result["ats_score"] = {
            "score": 0,
            "verdict": "Could not evaluate",
            "reasons": [],
            "improvements": []
        }

    return render_template(
        "dashboard.html",
        user=session.get("user"),
        result=result
    )

#forgot password
@app.route("/forgot_password", methods=["GET", "POST"])
def forgot_password():
    error = None
    if request.method == "POST":
        email = request.form.get("email")
        if not email or "@" not in email:
            error = "Please enter a valid email address."
    return render_template("forgot_password.html", error=error)

#history
@app.route("/history")
def history():
    if "user" not in session:
        return redirect("/login")

    db = SessionLocal()
    user = db.query(model.user).filter_by(email=session["user"]).first()
    reports = db.query(model.reports).filter_by(user_id=user.id).all()

    parsed_reports = []
    for r in reports:
        try:
            parsed_result = json.loads(r.result)
        except:
            parsed_result = {}

        parsed_reports.append({
            "resume": r.resume_text,
            "result": parsed_result
        })

    return render_template("history.html", reports=parsed_reports)

#logout
@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect("/login")

if __name__ == "__main__":
    app.run(debug=True)