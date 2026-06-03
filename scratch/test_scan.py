import sys
import os
import json
from config.rules import load_rules
from pipeline.graph import run_pipeline

def main():
    pdf_path = "tests/fixtures/demo_violations.pdf"
    if not os.path.exists(pdf_path):
        from create_test_pdf import create_test_pdf
        create_test_pdf()
    
    rules = load_rules()
    upload_id = "test_upload_123"
    
    print("Running pipeline...")
    generator = run_pipeline(pdf_path, "demo_violations.pdf", upload_id, rules)
    
    final_state = None
    for node_name, state in generator:
        print(f"Completed node: {node_name}")
        final_state = state
        
    print("\nScan completed!")
    print(f"Report Path: {final_state.get('report_path')}")
    print(f"Total Flags: {final_state.get('summary', {}).get('total_flags', 0)}")

if __name__ == "__main__":
    main()
