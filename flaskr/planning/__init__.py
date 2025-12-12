from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from werkzeug.wrappers import Response
from ..auth import auth_required
from .chief import chief_bp
from .minister import minister_bp
from ..constants import OFFICES, CHIEF, OFFICES_NAME, OFFICES_SINGLE
from .expenses import expenses_bp, create_expenses
from .state import EXPENSES
from random import randrange

planning_bp = Blueprint("planning", __name__)
planning_bp.register_blueprint(chief_bp, url_prefix="/chief")
planning_bp.register_blueprint(minister_bp, url_prefix="/minister")
planning_bp.register_blueprint(expenses_bp, url_prefix="/expenses")


@planning_bp.route("/")
@auth_required
def index() -> str | Response:
    return render_template(
        "role_selection.html",
        OFFICES=OFFICES,
        CHIEF=CHIEF,
        OFFICES_NAME=OFFICES_NAME,
        OFFICES_SINGLE=OFFICES_SINGLE,
    )


@planning_bp.route("/role", methods=["POST"])
@auth_required
def set_role() -> str | Response:
    role = request.form.get("role")
    if role:
        session["role"] = role
        if role == CHIEF:
            return redirect(url_for("planning.chief.dashboard"))
        elif role in OFFICES:
            return redirect(url_for("planning.expenses.list_expenses"))
        elif role == "minister":
            return redirect(url_for("planning.minister.dashboard"))
    return redirect(url_for("planning.index"))


@planning_bp.route("/file_import", methods=["POST"])
@auth_required
def import_file() -> str | Response:
    for role, expense_list in EXPENSES.items():
        for new_expense in create_expenses(role, randrange(1, 40)):
            expense_list.append(new_expense)

    return redirect(url_for("planning.chief.chief_dashboard"))
