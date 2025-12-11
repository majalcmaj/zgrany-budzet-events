from flask import Blueprint, request, render_template, redirect, url_for, flash
from ...auth import auth_required

from ...constants import OFFICES
from ..state import planning_state, PlanningStatus, EXPENSES, EXPENSES_CLOSED

chief_bp = Blueprint("chief", __name__)


@chief_bp.route("/dashboard", methods=["GET", "POST"])
@auth_required
def dashboard():
    if request.method == "POST":
        action = request.form.get("action")

        if action == "start":
            deadline = request.form.get("deadline")
            if not deadline:
                flash("Termin jest wymagany!", "error")
            else:
                planning_state.start_planning()
        elif action == "submit_minister":
            planning_state.submit_to_minister()
        elif action == "reopen":
            planning_state.reopen()

        return redirect(url_for("planning.chief.dashboard"))

    offices_status = []
    total_all_needs = 0
    for office in OFFICES:
        expenses = EXPENSES.get(office, [])
        total_needs = sum(
            e.financial_needs for e in expenses if e.financial_needs is not None
        )
        task_count = len(expenses)
        is_submitted = EXPENSES_CLOSED.get(office, False)

        total_all_needs += total_needs

        offices_status.append(
            {
                "name": office,
                "status": "Submitted" if is_submitted else "Open",
                "total_needs": total_needs,
                "task_count": task_count,
                "expenses": expenses,
            }
        )

    return render_template(
        "chief_dashboard.html",
        state=planning_state,
        offices_status=offices_status,
        total_all_needs=total_all_needs,
        PlanningStatus=PlanningStatus,
    )
