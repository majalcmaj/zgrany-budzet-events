from flask import Blueprint, render_template, request, redirect, url_for, session
from src.auth import auth_required

planning_bp = Blueprint('planning', __name__)

class PlanningState:
    def __init__(self):
        self.deadline = None
        self.is_open = False

    def set_deadline(self, date_str):
        self.deadline = date_str

    def open_process(self):
        self.is_open = True

    def close_process(self):
        self.is_open = False

# Singleton instance
planning_state = PlanningState()

@planning_bp.route('/chief_dashboard', methods=['GET', 'POST'])
@auth_required
def chief_dashboard():
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'open':
            deadline = request.form.get('deadline')
            if deadline:
                planning_state.set_deadline(deadline)
                planning_state.open_process()
        elif action == 'close':
            planning_state.close_process()
        return redirect(url_for('planning.chief_dashboard'))
    
    from src.expenses import EXPENSES, EXPENSES_CLOSED
    
    offices_status = []
    for office in ['office1', 'office2']:
        expenses = EXPENSES.get(office, [])
        total_needs = sum(e['financial_needs'] for e in expenses if e['financial_needs'] is not None)
        task_count = len(expenses)
        is_submitted = EXPENSES_CLOSED.get(office, False)
        
        offices_status.append({
            'name': office,
            'status': 'Submitted' if is_submitted else 'Open',
            'total_needs': total_needs,
            'task_count': task_count
        })

    return render_template('chief_dashboard.html', state=planning_state, offices_status=offices_status)

@planning_bp.route('/')
def index():
    return render_template('role_selection.html')

@planning_bp.route('/set_role', methods=['POST'])
def set_role():
    role = request.form.get('role')
    if role:
        session['role'] = role
        if role == 'chief':
            return redirect(url_for('planning.chief_dashboard'))
        elif role in ['office1', 'office2']:
            return redirect(url_for('expenses.list_expenses'))
    return redirect(url_for('planning.index'))
