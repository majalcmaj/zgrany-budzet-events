from flask import Blueprint, render_template, request, redirect, url_for, session

expenses_bp = Blueprint('expenses', __name__)

EXPENSES = {
    'office1': [],
    'office2': []
}
EXPENSES_CLOSED = {
    'office1': False,
    'office2': False
}

from src.planning import planning_state

@expenses_bp.route('/add', methods=['GET', 'POST'])
def add_expense():
    if 'role' not in session or session['role'] not in ['office1', 'office2']:
        return redirect(url_for('planning.index'))

    if EXPENSES_CLOSED[session['role']] or not planning_state.is_open:
        return redirect(url_for('expenses.list_expenses'))
        
    if request.method == 'POST':
        expense = {
            'chapter': request.form.get('chapter'),
            'task_name': request.form.get('task_name'),
            'financial_needs': request.form.get('financial_needs', type=int),
            'role': session['role']
        }
        EXPENSES[session['role']].append(expense)
        return redirect(url_for('expenses.list_expenses'))
    return render_template('add_expense.html')

@expenses_bp.route('/close', methods=['POST'])
def close_expenses():
    if not planning_state.is_open:
        return redirect(url_for('expenses.list_expenses'))
        
    if 'role' in session and session['role'] in EXPENSES_CLOSED:
        EXPENSES_CLOSED[session['role']] = True
    return redirect(url_for('expenses.list_expenses'))

@expenses_bp.route('/')
def list_expenses():
    if 'role' not in session or session['role'] not in ['office1', 'office2']:
        return redirect(url_for('planning.index'))
    current_expenses = EXPENSES[session['role']]
    expenses_sum = sum(e['financial_needs'] for e in current_expenses if e['financial_needs'] is not None)
    return render_template('expenses_list.html', 
                         expenses=current_expenses, 
                         closed=EXPENSES_CLOSED[session['role']],
                         is_open=planning_state.is_open,
                         expenses_sum=expenses_sum)
