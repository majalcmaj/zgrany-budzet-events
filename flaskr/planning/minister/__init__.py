from flask import Blueprint, request, render_template, redirect, url_for, session, flash
from auth import auth_required
from planning.state import planning_state, PlanningStatus, EXPENSES, EXPENSES_CLOSED
from constants import OFFICES

minister_bp = Blueprint("minister", __name__)


@minister_bp.route("/dashboard", methods=["GET", "POST"])
@auth_required
def dashboard():
    if request.method == "POST":
        action = request.form.get("action")
        if action == "request_correction":
            comment = request.form.get("comment")
            planning_state.request_correction(comment)
        elif action == "approve":
            planning_state.approve()
        return redirect(url_for("planning.minister.dashboard"))

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
        "minister_dashboard.html",
        state=planning_state,
        offices_status=offices_status,
        total_all_needs=total_all_needs,
        PlanningStatus=PlanningStatus,
    )
