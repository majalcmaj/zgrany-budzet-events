from dataclasses import dataclass

from flask import Blueprint, render_template, request, redirect, url_for, session
from src.constants import OFFICES
expenses_bp = Blueprint('expenses', __name__)

@dataclass
class Expense:
    chapter: int
    task_name: str
    financial_needs: int
    role: str

EXPENSES: dict[str, list[Expense]] = {
    'office1': [],
    'office2': []
}
EXPENSES_CLOSED = {
    'office1': False,
    'office2': False
}

from src.planning import planning_state, PlanningStatus


@expenses_bp.route('/add', methods=['GET', 'POST'])
def add_expense():
    if 'role' not in session or session['role'] not in OFFICES:
        return redirect(url_for('planning.index'))

    # Allow editing if status is IN_PROGRESS
    can_edit = planning_state.status == PlanningStatus.IN_PROGRESS
    
    if EXPENSES_CLOSED[session['role']] or not can_edit:
        return redirect(url_for('expenses.list_expenses'))
        
    if request.method == 'POST':
        expense = Expense(
            chapter = request.form.get('chapter'),
            task_name = request.form.get('task_name'),
            financial_needs = request.form.get('financial_needs', type=int),
            role = session['role']
        )
        EXPENSES[session['role']].append(expense)
        return redirect(url_for('expenses.list_expenses'))
    return render_template('add_expense.html')

@expenses_bp.route('/close', methods=['POST'])
def close_expenses():
    can_edit = planning_state.status in [PlanningStatus.IN_PROGRESS, PlanningStatus.NEEDS_CORRECTION]
    
    if not can_edit:
        return redirect(url_for('expenses.list_expenses'))
        
    if 'role' in session and session['role'] in EXPENSES_CLOSED:
        EXPENSES_CLOSED[session['role']] = True
    return redirect(url_for('expenses.list_expenses'))

@expenses_bp.route('/')
def list_expenses():
    if 'role' not in session or session['role'] not in OFFICES:
        return redirect(url_for('planning.index'))
    current_expenses = EXPENSES[session['role']]
    expenses_sum = sum(e.financial_needs for e in current_expenses if e.financial_needs is not None)
    return render_template('expenses_list.html', 
                         expenses=current_expenses, 
                         closed=EXPENSES_CLOSED[session['role']],
                         state=planning_state,
                         PlanningStatus=PlanningStatus,
                         expenses_sum=expenses_sum)
