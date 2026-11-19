from flask import Flask, render_template, request, send_file, flash, redirect, url_for
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable
from reportlab.lib.units import mm
from xml.sax.saxutils import escape
import re

app = Flask(__name__)
app.secret_key = "change-this-secret-key"

def clean(value):
    return (value or "").strip()

def paragraph_text(value):
    return escape(clean(value)).replace("\n", "<br/>")

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        data = {key: clean(value) for key, value in request.form.items()}
        required = ["full_name", "email", "phone", "career_objective"]
        missing = [field for field in required if not data.get(field)]
        if missing:
            flash("Please fill in your name, email, phone number and career objective.")
            return render_template("index.html", data=data)
        return render_template("preview.html", data=data)
    return render_template("index.html", data={})

@app.route("/download", methods=["POST"])
def download():
    data = {key: clean(value) for key, value in request.form.items()}
    required = ["full_name", "email", "phone", "career_objective"]
    if any(not data.get(field) for field in required):
        flash("Some required details are missing. Please complete the form.")
        return redirect(url_for("index"))

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4, rightMargin=18*mm, leftMargin=18*mm,
        topMargin=16*mm, bottomMargin=16*mm
    )
    styles = getSampleStyleSheet()
    name_style = ParagraphStyle(
        "Name", parent=styles["Title"], fontName="Helvetica-Bold",
        fontSize=21, leading=25, textColor=colors.HexColor("#17365D"),
        alignment=TA_LEFT, spaceAfter=4
    )
    contact_style = ParagraphStyle(
        "Contact", parent=styles["Normal"], fontSize=9, leading=13,
        textColor=colors.HexColor("#555555"), spaceAfter=10
    )
    heading_style = ParagraphStyle(
        "Section", parent=styles["Heading2"], fontName="Helvetica-Bold",
        fontSize=11, leading=14, textColor=colors.HexColor("#17365D"),
        spaceBefore=10, spaceAfter=4
    )
    body_style = ParagraphStyle(
        "Body", parent=styles["BodyText"], fontSize=9.5, leading=13,
        spaceAfter=4
    )
    small_style = ParagraphStyle(
        "Small", parent=body_style, fontSize=9, leading=12
    )

    story = []
    story.append(Paragraph(escape(data["full_name"]), name_style))
    contact = " | ".join(filter(None, [
        escape(data.get("email", "")), escape(data.get("phone", "")),
        escape(data.get("location", "")), escape(data.get("linkedin", ""))
    ]))
    story.append(Paragraph(contact, contact_style))
    story.append(HRFlowable(width="100%", thickness=1.2, color=colors.HexColor("#2F75B5")))

    def add_section(title, value, bullets=False):
        value = clean(value)
        if not value:
            return
        story.append(Paragraph(escape(title.upper()), heading_style))
        if bullets:
            for item in value.splitlines():
                item = item.strip().lstrip("•-* ").strip()
                if item:
                    story.append(Paragraph("&#8226; " + paragraph_text(item), small_style))
        else:
            story.append(Paragraph(paragraph_text(value), body_style))

    add_section("Career Objective / Professional Summary", data.get("career_objective"))
    add_section("Education", data.get("education"), True)
    add_section("Work Experience", data.get("experience"), True)
    add_section("Projects", data.get("projects"), True)
    add_section("Technical Skills", data.get("skills"))
    add_section("Certifications", data.get("certifications"), True)
    add_section("Achievements", data.get("achievements"), True)
    add_section("Languages", data.get("languages"))

    doc.build(story)
    buffer.seek(0)
    filename = re.sub(r"[^A-Za-z0-9_-]+", "_", data["full_name"]).strip("_") or "CV"
    return send_file(buffer, as_attachment=True, download_name=f"{filename}_CV.pdf",
                     mimetype="application/pdf")

@app.errorhandler(413)
def too_large(error):
    return "The submitted form is too large.", 413

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
