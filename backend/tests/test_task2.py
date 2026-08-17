import os
import sys

# Add parent directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from engine.sandbox import PythonSandbox, validate_code_safety
from agents.profiler import DataProfilerAgent

def test_sandbox_safety():
    unsafe_code = "import os\nos.system('echo hacked')"
    safe, violations = validate_code_safety(unsafe_code)
    assert not safe, "Sandbox failed to block forbidden module import!"
    print("[OK] Sandbox AST Safety Test Passed!")

def test_sandbox_execution():
    sandbox = PythonSandbox()
    code = "import json; print(json.dumps({'result': 42, 'status': 'success'}))"
    res = sandbox.execute_script(code)
    assert res["success"] == True, f"Sandbox failed execution: {res['error']}"
    assert res["parsed_result"]["result"] == 42
    print("[OK] Sandbox Execution Test Passed!")

def test_data_profiler():
    csv_path = os.path.abspath("data/sample_churn.csv")
    profiler = DataProfilerAgent()
    profile = profiler.profile_csv(csv_path)
    assert profile["num_rows"] == 50
    assert "churned" in profile["target_candidates"]
    assert "age" in profile["numerical_columns"]
    print(f"[OK] Data Profiler Test Passed! Profile Summary: {profile['num_rows']} rows, targets: {profile['target_candidates']}")

if __name__ == "__main__":
    test_sandbox_safety()
    test_sandbox_execution()
    test_data_profiler()
    print("ALL TASK 2 VERIFICATION TESTS PASSED SUCCESSFULLY!")
