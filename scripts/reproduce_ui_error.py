import os
import subprocess
import sys
import time

import httpx


def test_run_sequence():
    print("Starting backend on port 8001...")
    env = os.environ.copy()
    env["PYTHONPATH"] = "src"
    # Use --no-reload for test process stability
    backend = subprocess.Popen(
        [sys.executable, "-m", "cine_forge.api", "--port", "8001", "--no-reload"],
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
                resp = httpx.get("http://127.0.0.1:8001/api/health")
                if resp.status_code == 200:
                    break
            except Exception:
                time.sleep(1)
        else:
            print("Backend failed to start")
            sys.exit(1)
        
        client = httpx.Client(base_url="http://127.0.0.1:8001", timeout=30.0)
        
        print("Creating project...")
        proj = client.post(
            "/api/projects/new", json={"project_path": "output/test_debug_run"}
        ).json()
        project_id = proj["project_id"]
        
        print("Uploading file...")
        files = {"file": ("test.fountain", b"INT. STUDIO - DAY\n\nARIA\nHello.", "text/plain")}
        upload = client.post(f"/api/projects/{project_id}/inputs/upload", files=files).json()
        input_file = upload["stored_path"]
        
        print(f"Starting run with input: {input_file}")
        # Test BOTH name variants (utility and sota)
        run = client.post("/api/runs/start", json={
            "project_id": project_id,
            "input_file": input_file,
            "default_model": "mock",
            "work_model": "mock",
            "verify_model": "mock",
            "escalate_model": "mock",
            "recipe_id": "world_building",
            "accept_config": True,
            "skip_qa": True
        }).json()
        run_id = run["run_id"]
        
        print(f"Polling run {run_id}...")
        for _ in range(20):
            state_resp = client.get(f"/api/runs/{run_id}/state").json()
            bg_error = state_resp.get("background_error")
            if bg_error:
                print(f"\n!!! CAUGHT BACKGROUND ERROR: {bg_error}")
                print(f"Full State: {state_resp}")
                sys.exit(1)
            
            stages = state_resp.get("state", {}).get("stages", {})
            if stages and all(s["status"] in ["done", "failed"] for s in stages.values()):
                if any(s["status"] == "failed" for s in stages.values()):
                    print("Run finished but some stages FAILED.")
                    sys.exit(1)
                print("Run finished successfully.")
                break
            time.sleep(1)
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
