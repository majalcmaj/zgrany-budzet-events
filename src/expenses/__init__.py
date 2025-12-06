from flask import Blueprint, render_template, request, redirect, url_for

expenses_bp = Blueprint('expenses', __name__)

EXPENSES = []

@expenses_bp.route('/add', methods=['GET', 'POST'])
def add_expense():
    if request.method == 'POST':
        expense = {
            'chapter': request.form.get('chapter'),
            'task_name': request.form.get('task_name'),
            'financial_needs': request.form.get('financial_needs')
        }
        EXPENSES.append(expense)
        return redirect(url_for('expenses.list_expenses'))
    return render_template('add_expense.html')

@expenses_bp.route('/')
def list_expenses():
    return render_template('expenses_list.html', expenses=EXPENSES)
