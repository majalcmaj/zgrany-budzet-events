from flask import Blueprint, redirect, render_template, request, url_for
from werkzeug.wrappers import Response

from ...auth import auth_required
from ...constants import OFFICES
from ..state import EXPENSES, EXPENSES_CLOSED, PlanningStatus, planning_state

chief_bp = Blueprint("chief", __name__)


@chief_bp.route("/dashboard", methods=["GET", "POST"])
@auth_required
def dashboard() -> str | Response:
    if request.method == "POST":
        action = request.form.get("action")

        if action == "start":
            deadline = request.form.get("deadline")
            if deadline:
                planning_state.start_planning(deadline)
        elif action == "submit_minister":
            planning_state.submit_to_minister()
        elif action == "reopen":
            planning_state.reopen()

        return redirect(url_for("planning.chief.dashboard"))

    offices_status: list[dict[str, object]] = []
    total_all_needs = 0
    for office in OFFICES:
        expenses = EXPENSES.get(office, [])
        total_needs = sum(e.financial_needs for e in expenses)
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
