"""
CLI entry point — runs the renewal flow for all residents and prints traces.
"""
import json
from dotenv import load_dotenv
from orchestrator import process_renewal

load_dotenv()


def main():
    with open("data/residents.json") as f:
        residents = json.load(f)["residents"]

    for r in residents:
        print(f"\n{'='*60}\nProcessing: {r['name']} ({r['resident_id']})\n{'='*60}")
        trace = process_renewal(r)
        for step in trace["steps"]:
            print(f"\n--- {step['agent']} ---")
            print(json.dumps(step["output"], indent=2))
        print(f"\nFINAL STATUS: {trace['final_status']}")


if __name__ == "__main__":
    main()