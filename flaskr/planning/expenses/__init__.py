import json
import random
from pathlib import Path

from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from werkzeug.wrappers import Response

from ...auth import auth_required
from ...constants import OFFICES, OFFICES_GENITIVE
from ...db import Section, db
from ..planning_aggregate import (
    EXPENSES,
    EXPENSES_CLOSED,
    PlanningStatus,
    planning_aggregate,
)
from ..types import Expense
from .aggregate import expense_stream_id

print(f"expense_stream_id function loaded: {expense_stream_id}")

__all__ = ["expenses_bp", "create_expenses"]

expenses_bp = Blueprint("expenses", __name__)

assert planning_aggregate is not None


@expenses_bp.route("/")
@auth_required
def list_expenses() -> str | Response:
    if "role" not in session or session["role"] not in OFFICES:
        return redirect(url_for("planning.index"))
    current_expenses = EXPENSES[session["role"]]
    expenses_sum = sum(e.financial_needs for e in current_expenses)
    return render_template(
        "expenses_list.html",
        expenses=current_expenses,
        closed=EXPENSES_CLOSED[session["role"]],
        state=planning_aggregate,
        PlanningStatus=PlanningStatus,
        expenses_sum=expenses_sum,
        offices_genitive=OFFICES_GENITIVE,
    )


@expenses_bp.route("/add", methods=["GET", "POST"])
@auth_required
def add_expense() -> str | Response:
    if "role" not in session or session["role"] not in OFFICES:
        return redirect(url_for("planning.index"))

    # Allow editing if status is IN_PROGRESS
    can_edit = planning_aggregate.status == PlanningStatus.IN_PROGRESS

    if EXPENSES_CLOSED[session["role"]] or not can_edit:
        return redirect(url_for("planning.expenses.list_expenses"))

    if request.method == "POST":
        # Extract required fields
        chapter = request.form.get("chapter")  # Now a 5-digit string code
        task_name = request.form.get("task_name")
        budget_2026 = request.form.get("budget_2026", type=int)

        # Validate required fields
        if not chapter or not task_name or budget_2026 is None:
            flash("Wszystkie wymagane pola muszą być wypełnione!", "error")
            return render_template("add_expense.html")

        # Extract all optional fields
        expense = Expense(
            chapter=chapter,
            task_name=task_name,
            financial_needs=budget_2026,  # Use budget_2026 as financial_needs
            role=session["role"],
            # Additional fields
            departament=request.form.get("departament") or None,
            rodzaj_projektu=request.form.get("rodzaj_projektu") or None,
            opis_projektu=request.form.get("opis_projektu") or None,
            data_zlozenia=request.form.get("data_zlozenia") or None,
            program_operacyjny=request.form.get("program_operacyjny") or None,
            termin_realizacji=request.form.get("termin_realizacji") or None,
            zrodlo_fin=request.form.get("zrodlo_fin", type=int),
            beneficjent=request.form.get("beneficjent") or None,
            szczegolowe_uzasadnienie=request.form.get("szczegolowe_uzasadnienie")
            or None,
            budget_2025=request.form.get("budget_2025", type=int),
            budget_2026=budget_2026,
            budget_2027=request.form.get("budget_2027", type=int),
            budget_2028=request.form.get("budget_2028", type=int),
            budget_2029=request.form.get("budget_2029", type=int),
            etap_dzialan=request.form.get("etap_dzialan") or None,
            umowy=request.form.get("umowy") or None,
            nr_umowy=request.form.get("nr_umowy") or None,
            z_kim_zawarta=request.form.get("z_kim_zawarta") or None,
            uwagi=request.form.get("uwagi") or None,
        )
        EXPENSES[session["role"]].append(expense)
        return redirect(url_for("planning.expenses.list_expenses"))
    return render_template("add_expense.html")


@expenses_bp.route("/api/classifications", methods=["GET"])
@auth_required
def get_classifications() -> dict[str, object]:
    """Get działów and rozdziałów classification data."""
    data_dir = Path(__file__).parent.parent.parent / "data"

    # Load działów
    with open(data_dir / "dzialy.json", "r", encoding="utf-8") as f:
        dzialy = json.load(f)

    # Load rozdziały
    with open(data_dir / "rozdzialy.json", "r", encoding="utf-8") as f:
        rozdzialy = json.load(f)

    # Load dział-rozdział mapping
    with open(data_dir / "dzial_rozdzial_mapping.json", "r", encoding="utf-8") as f:
        dzial_rozdzial_mapping = json.load(f)

    return {
        "dzialy": dzialy,
        "rozdzialy": rozdzialy,
        "dzial_rozdzial_mapping": dzial_rozdzial_mapping,
    }


@expenses_bp.route("/fragment/section/chapter")
@auth_required
def sections() -> str | Response:
    chapter_id = request.args.get("chapter")
    sections = db.session.query(Section).filter_by(ChapterId=chapter_id).all()
    return render_template("sectionTemplate.html", sections=sections)


@expenses_bp.route("/close", methods=["POST"])
@auth_required
def close_expenses() -> str | Response:
    can_edit = planning_aggregate.status in [
        PlanningStatus.IN_PROGRESS,
        PlanningStatus.NEEDS_CORRECTION,
    ]

    if not can_edit:
        return redirect(url_for("planning.expenses.list_expenses"))

    if "role" in session and session["role"] in EXPENSES_CLOSED:
        EXPENSES_CLOSED[session["role"]] = True
    return redirect(url_for("planning.expenses.list_expenses"))


@expenses_bp.route("/import", methods=["POST"])
@auth_required
def import_data() -> str | Response:
    role = session["role"]

    for e in create_expenses(role, 10):
        EXPENSES[role].append(e)

    return redirect(url_for("planning.expenses.list_expenses"))


def create_expenses(role: str, n: int) -> list[Expense]:
    """Load expense data from JSON file and return n random expenses."""
    json_path = Path(__file__).parent.parent / "data" / "expenses_template.json"

    with open(json_path, "r", encoding="utf-8") as f:
        expenses_data = json.load(f)

    # Randomly select n expenses from the data
    selected = random.sample(expenses_data, min(n, len(expenses_data)))

    # Convert to Expense objects
    return [
        Expense(
            chapter=exp["chapter"],
            task_name=exp["task_name"],
            financial_needs=exp["financial_needs"],
            role=role,
            # Additional fields
            czesc=exp.get("czesc"),
            departament=exp.get("departament"),
            rodzaj_projektu=exp.get("rodzaj_projektu"),
            opis_projektu=exp.get("opis_projektu"),
            data_zlozenia=exp.get("data_zlozenia"),
            program_operacyjny=exp.get("program_operacyjny"),
            termin_realizacji=exp.get("termin_realizacji"),
            zrodlo_fin=exp.get("zrodlo_fin"),
            bz=exp.get("bz"),
            beneficjent=exp.get("beneficjent"),
            szczegolowe_uzasadnienie=exp.get("szczegolowe_uzasadnienie"),
            budget_2025=exp.get("budget_2025"),
            budget_2026=exp.get("budget_2026"),
            budget_2027=exp.get("budget_2027"),
            budget_2028=exp.get("budget_2028"),
            budget_2029=exp.get("budget_2029"),
            etap_dzialan=exp.get("etap_dzialan"),
            umowy=exp.get("umowy"),
            nr_umowy=exp.get("nr_umowy"),
            z_kim_zawarta=exp.get("z_kim_zawarta"),
            uwagi=exp.get("uwagi"),
        )
        for exp in selected
    ]
