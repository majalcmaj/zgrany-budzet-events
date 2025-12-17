from flask import Flask

from flaskr.planning.planning_aggregate import planning_scheduled_listener

from .constants import OFFICES
from .db import db
from .events import events, init_event_extension

__all__ = ["app", "db"]

app = Flask(__name__, template_folder="web/templates", static_folder="web/static")
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///zgrany_budget.db"
app.secret_key = "super_secret_key_for_demo_only"

db.init_app(app)
with app.app_context() as ctx:
    init_event_extension(app)
    from flaskr.extensions import init_context_extension

    init_context_extension(app)

    from .planning.planning_aggregate import PlanningScheduled
    from .planning.views import planning_bp

    app.register_blueprint(planning_bp, url_prefix="/")

    events().add_subscriber("planning_scheduled", planning_scheduled_listener)
    events().emit(
        [
            PlanningScheduled(
                stream_id="planning_scheduled", planning_year=2025, offices=OFFICES
            )
        ]
    )


@app.route("/health")
def health() -> tuple[str, int]:
    return "OK", 200


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
