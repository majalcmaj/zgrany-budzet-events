from flask import Blueprint, render_template, request, redirect, url_for
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

@planning_bp.route('/', methods=['GET', 'POST'])
@auth_required
def dashboard():
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'open':
            deadline = request.form.get('deadline')
            if deadline:
                planning_state.set_deadline(deadline)
                planning_state.open_process()
        elif action == 'close':
            planning_state.close_process()
        return redirect(url_for('planning.dashboard'))
    
    return render_template('chief_dashboard.html', state=planning_state)
