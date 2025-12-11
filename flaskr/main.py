from datetime import datetime
from pathlib import Path
from flask import (
    Flask,
    render_template,
    request,
)
from .db import db, Section
from .auth import auth_required
from .events import init_event_extension

app = Flask(__name__, template_folder="web/templates", static_folder="web/static")
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16MB max file size
app.config["UPLOAD_FOLDER"] = Path(__file__).parent / "static" / "uploads"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///zgrany_budget.db"
app.secret_key = "super_secret_key_for_demo_only"

db.init_app(app)
with app.app_context():
    init_event_extension(app)
    from .planning.expenses import expenses_bp
    from .planning import planning_bp

    app.register_blueprint(expenses_bp, url_prefix="/expenses")
    app.register_blueprint(planning_bp, url_prefix="/")


# Ensure upload folder exists
app.config["UPLOAD_FOLDER"].mkdir(parents=True, exist_ok=True)

ALLOWED_EXTENSIONS = {"xlsx", "pdf"}


def get_uploaded_files():
    """Get list of uploaded files with metadata."""
    files = []
    upload_folder = app.config["UPLOAD_FOLDER"]

    if upload_folder.exists():
        for file_path in upload_folder.iterdir():
            if file_path.is_file():
                stat = file_path.stat()
                files.append(
                    {
                        "name": file_path.name,
                        "extension": file_path.suffix[1:].lower(),
                        "size": get_file_size(stat.st_size),
                        "uploaded_at": datetime.fromtimestamp(stat.st_mtime).strftime(
                            "%Y-%m-%d %H:%M"
                        ),
                    }
                )

    # Sort by upload time (newest first)
    files.sort(key=lambda x: x["uploaded_at"], reverse=True)
    return files


@app.route("/health")
def health():
    return "OK", 200


@app.route("/fragment/section/chapter")
@auth_required
def sections():
    chapter_id = request.args.get("chapter")
    sections = db.session.query(Section).filter_by(ChapterId=chapter_id).all()
    return render_template("sectionTemplate.html", sections=sections)


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
