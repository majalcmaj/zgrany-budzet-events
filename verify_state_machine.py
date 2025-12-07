import sys
import os

# Add src to path
sys.path.append(os.path.join(os.getcwd(), 'src'))

# Mock Flask session and request context if needed, but we might be able to test logic directly
# However, the side effects depend on EXPENSES_CLOSED which is in src.expenses
# Let's try to import the state and expenses module

from src.planning import planning_state, PlanningStatus
from src.expenses import EXPENSES_CLOSED

def verify():
    print("Starting verification...")
    
    # 1. Initial State
    print(f"Initial State: {planning_state.status}")
    assert planning_state.status == PlanningStatus.NOT_STARTED
    
    # 2. Start Planning
    print("Transitioning to IN_PROGRESS...")
    planning_state.start_planning()
    print(f"Current State: {planning_state.status}")
    assert planning_state.status == PlanningStatus.IN_PROGRESS
    
    # 3. Simulate Office Submission
    print("Simulating office submission...")
    EXPENSES_CLOSED['Departament A'] = True
    EXPENSES_CLOSED['Departament B'] = True
    print(f"Office1 Closed: {EXPENSES_CLOSED['Departament A']}")
    assert EXPENSES_CLOSED['Departament A'] is True
    
    # 4. Submit to Minister
    print("Transitioning to IN_REVIEW...")
    planning_state.submit_to_minister()
    print(f"Current State: {planning_state.status}")
    assert planning_state.status == PlanningStatus.IN_REVIEW
    
    # 5. Request NEEDS_CORRECTION (Side Effect Check)
    print("Transitioning to NEEDS_CORRECTION (should reset office approvals)...")
    planning_state.request_correction()
    print(f"Current State: {planning_state.status}")
    assert planning_state.status == PlanningStatus.NEEDS_CORRECTION
    
    print(f"Office1 Closed: {EXPENSES_CLOSED['Departament A']}")
    assert EXPENSES_CLOSED['Departament A'] is False
    assert EXPENSES_CLOSED['Departament B'] is False
    print("Side effect verified: Office approvals reset.")
    
    # 6. Submit Correction
    print("Transitioning to IN_REVIEW again...")
    planning_state.submit_correction()
    print(f"Current State: {planning_state.status}")
    assert planning_state.status == PlanningStatus.IN_REVIEW
    
    print("Verification Successful!")

if __name__ == "__main__":
    verify()
