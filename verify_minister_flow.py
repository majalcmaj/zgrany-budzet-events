import sys
import os

# Add src to path
sys.path.append(os.path.join(os.getcwd(), 'src'))

from src.planning import planning_state
from src.planning.planning_workflow import PlanningStatus
from src.expenses import EXPENSES_CLOSED, OFFICES

def verify():
    print("Starting Minister Workflow Verification...")
    
    # Reset state
    planning_state.reopen()
    for office in OFFICES:
        EXPENSES_CLOSED[office] = False
        
    # 1. Start Planning
    print("\n1. Start Planning")
    planning_state.start_planning()
    assert planning_state.status == PlanningStatus.IN_PROGRESS
    print("State: IN_PROGRESS")
    
    # 2. Submit to Minister
    print("\n2. Submit to Minister")
    planning_state.submit_to_minister()
    assert planning_state.status == PlanningStatus.IN_REVIEW
    print("State: IN_REVIEW")
    
    # Verify Side Effect: Offices should be closed
    print(f"Office1 Closed: {EXPENSES_CLOSED['office1']}")
    assert EXPENSES_CLOSED['office1'] is True
    
    # 3. Minister Requests Correction
    print("\n3. Minister Requests Correction")
    planning_state.request_correction()
    assert planning_state.status == PlanningStatus.NEEDS_CORRECTION
    print("State: NEEDS_CORRECTION")
    
    # Verify Side Effect: Offices should be OPEN (False)
    print(f"Office1 Closed: {EXPENSES_CLOSED['office1']}")
    if EXPENSES_CLOSED['office1'] is True:
        print("FAIL: Office1 is still closed! They cannot make corrections.")
        sys.exit(1)
    else:
        print("PASS: Office1 is open.")

    print("\nVerification Successful!")

if __name__ == "__main__":
    verify()
