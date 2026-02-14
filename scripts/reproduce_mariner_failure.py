import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

import httpx


def test_run_sequence():
    project_path = "output/test_mariner_repro_final_v2"
    workspace_root = Path(__file__).resolve().parents[1]
    full_project_path = workspace_root / project_path
    
    if full_project_path.exists():
        print(f"Cleaning up existing project at {full_project_path}...")
        shutil.rmtree(full_project_path)

    print("Starting backend on port 8003...")
    env = os.environ.copy()
    env["PYTHONPATH"] = "src"
    backend = subprocess.Popen(
        [sys.executable, "-m", "cine_forge.operator_console", "--port", "8003", "--no-reload"],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    try:
        # Wait for health
        print("Waiting for health check...")
        for _ in range(10):
            try:
                resp = httpx.get("http://127.0.0.1:8003/api/health")
                if resp.status_code == 200:
                    break
            except Exception:
                time.sleep(1)
        else:
            print("Backend failed to start")
            sys.exit(1)
        
        client = httpx.Client(base_url="http://127.0.0.1:8003", timeout=900.0)
        
        print("Creating project...")
        proj = client.post("/api/projects/new", json={"project_path": project_path}).json()
        project_id = proj["project_id"]
        
        input_file = "/Users/cam/Documents/Projects/cine-forge/input/2023 Round 1 Screenwriting Challenge - The Mariner - No ID.md"  # noqa: E501
        
        print(f"Starting run with input: {input_file}")
        run = client.post("/api/runs/start", json={
            "project_id": project_id,
            "input_file": input_file,
            "default_model": "gpt-4o-mini",
            "work_model": "gpt-4o-mini",
            "verify_model": "gpt-4o-mini",
            "escalate_model": "gpt-4o-mini",
            "recipe_id": "mvp_ingest",
            "accept_config": True,
            "skip_qa": False
        }).json()
        run_id = run["run_id"]
        
        print(f"Polling run {run_id}...")
        for _ in range(180): # Up to 15 minutes
            state_resp = client.get(f"/api/runs/{run_id}/state").json()
            bg_error = state_resp.get("background_error")
            if bg_error:
                print(f"\n!!! REPRODUCED ERROR: {bg_error}")
                return
            
            stages = state_resp.get("state", {}).get("stages", {})
            if stages:
                progress = ", ".join([f"{k}: {v['status']}" for k, v in stages.items()])
                print(f"  Progress: {progress}")
                
                if all(s["status"] in ["done", "failed"] for s in stages.values()):
                    if any(s["status"] == "failed" for s in stages.values()):
                        events = client.get(f"/api/runs/{run_id}/events").json()
                        for event in events["events"]:
                            if event.get("event") == "stage_failed":
                                print(f"\n!!! REPRODUCED STAGE FAILURE: {event.get('error')}")
                                return
                    print("Run finished successfully.")
                    break
            time.sleep(10)
        else:
            print("Timeout waiting for run.")
            sys.exit(1)

    finally:
        print("Terminating backend...")
        backend.terminate()
        try:
            out, err = backend.communicate(timeout=5)
            if out:
                print(f"--- BACKEND STDOUT ---\n{out}")
            if err:
                print(f"--- BACKEND STDERR ---\n{err}")
        except Exception:  # noqa: BLE001
            backend.kill()

if __name__ == "__main__":
    test_run_sequence()
