from flask import Blueprint, render_template, request, redirect, url_for

expenses_bp = Blueprint('expenses', __name__)

EXPENSES = []
EXPENSES_CLOSED = False

from src.planning import planning_state

@expenses_bp.route('/add', methods=['GET', 'POST'])
def add_expense():
    if EXPENSES_CLOSED or not planning_state.is_open:
        return redirect(url_for('expenses.list_expenses'))
        
    if request.method == 'POST':
        expense = {
            'chapter': request.form.get('chapter'),
            'task_name': request.form.get('task_name'),
            'financial_needs': request.form.get('financial_needs', type=int)
        }
        EXPENSES.append(expense)
        return redirect(url_for('expenses.list_expenses'))
    return render_template('add_expense.html')

@expenses_bp.route('/close', methods=['POST'])
def close_expenses():
    global EXPENSES_CLOSED
    EXPENSES_CLOSED = True
    return redirect(url_for('expenses.list_expenses'))

@expenses_bp.route('/')
def list_expenses():
    expenses_sum = sum(expense['financial_needs'] for expense in EXPENSES) 
    return render_template('expenses_list.html', expenses=EXPENSES, closed=EXPENSES_CLOSED, expenses_sum=expenses_sum)
