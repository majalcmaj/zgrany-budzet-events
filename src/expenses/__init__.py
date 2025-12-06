from flask import Blueprint, render_template

expenses_bp = Blueprint('expenses', __name__)

@expenses_bp.route('/add')
def add_expense():
    return render_template('add_expense.html')
