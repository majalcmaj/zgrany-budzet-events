from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from auth import auth_required
from .chief import chief_bp
from .planning_workflow import PlanningState, PlanningStatus
from constants import OFFICES, CHIEF, OFFICES_NAME, OFFICES_SINGLE

# from expenses import EXPENSES, EXPENSES_CLOSED # Moved to inside functions to avoid circular import

planning_bp = Blueprint("planning", __name__)
planning_bp.register_blueprint(chief_bp)

# Singleton instance of PlanningState - will be stored in db later
planning_state = PlanningState()


@planning_bp.route("/minister_dashboard", methods=["GET", "POST"])
@auth_required
def minister_dashboard():
    from .expenses import EXPENSES, EXPENSES_CLOSED

    if request.method == "POST":
        action = request.form.get("action")
        if action == "request_correction":
            comment = request.form.get("comment")
            planning_state.request_correction(comment)
        elif action == "approve":
            planning_state.approve()

        return redirect(url_for("planning.minister_dashboard"))

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


@planning_bp.route("/")
@auth_required
def index():
    return render_template(
        "role_selection.html",
        OFFICES=OFFICES,
        CHIEF=CHIEF,
        OFFICES_NAME=OFFICES_NAME,
        OFFICES_SINGLE=OFFICES_SINGLE,
    )


@planning_bp.route("/set_role", methods=["POST"])
@auth_required
def set_role():
    role = request.form.get("role")
    if role:
        session["role"] = role
        if role == CHIEF:
            return redirect(url_for("planning.chief.chief_dashboard"))
        elif role in OFFICES:
            return redirect(url_for("expenses.list_expenses"))
        elif role == "minister":
            return redirect(url_for("planning.minister_dashboard"))
    return redirect(url_for("planning.index"))


@planning_bp.route("/file_import", methods=["POST"])
@auth_required
def import_file():
    from .expenses import EXPENSES, Expense
    from random import randrange
    from .expenses import create_expenses

    for role, expense_list in EXPENSES.items():
        for new_expense in create_expenses(role, randrange(1, 40)):
            expense_list.append(new_expense)

    return redirect(url_for("planning.chief.chief_dashboard"))
