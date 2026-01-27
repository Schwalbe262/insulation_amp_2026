import subprocess
import time
import logging
import os
import sys

# 로그 디렉토리 생성
log_dir = './simul_log'
if not os.path.exists(log_dir):
    os.makedirs(log_dir, exist_ok=True)

logging.basicConfig(filename='run_debug.log', level=logging.DEBUG)

script_name = "simulation_script.py"
script_path = os.path.join(os.getcwd(), script_name)

# 스크립트 존재 확인
if not os.path.exists(script_path):
    error_msg = f"Error: {script_path} not found!\n"
    print(error_msg, file=sys.stderr)
    sys.stderr.flush()
    sys.exit(1)

num_processes = 10

print(f"Starting {num_processes} processes...", file=sys.stderr)
sys.stderr.flush()

processes = []
for i in range(num_processes):
    log_file = open(f'./simul_log/process_{i}.log', 'w')
    try:
        p = subprocess.Popen(
            f'python {script_path}',
            shell=True,
            stdout=log_file,
            stderr=subprocess.STDOUT
        )
        processes.append((p, log_file))
        print(f"Started process {i} (PID: {p.pid})", file=sys.stderr)
        sys.stderr.flush()
    except Exception as e:
        error_msg = f"Failed to start process {i}: {e}\n"
        print(error_msg, file=sys.stderr)
        sys.stderr.flush()
        log_file.close()
    time.sleep(10)

for idx, (p, log_file) in enumerate(processes):
    try:
        p.wait()
        log_file.write(f"\nProcess {idx} finished with return code {p.returncode}\n")
        if p.returncode != 0:
            print(f"Process {idx} exited with non-zero code: {p.returncode}", file=sys.stderr)
            sys.stderr.flush()
    except Exception as e:
        error_msg = f"Error waiting for process {idx}: {e}\n"
        print(error_msg, file=sys.stderr)
        sys.stderr.flush()
    finally:
        log_file.close()

print("All processes finished.", file=sys.stderr)
sys.stderr.flush()
