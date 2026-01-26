import subprocess
import sys
import time
from pathlib import Path


def run_many(
    num_iterations: int = 10000,
    sleep_sec: float = 1.0,
    stop_on_fail: bool = False,
) -> None:
    """
    simulation_script.py를 '그냥 여러 번 실행'만 합니다.
    (import 해서 run()/Simulation()에 접근하지 않음)
    """
    here = Path(__file__).resolve().parent
    target = here / "simulation_script.py"

    for itr in range(num_iterations):
        print("================================================")
        print(f"loop {itr} : simulation start!!")
        print("================================================")

        # 현재 파이썬 인터프리터로 simulation_script.py 실행
        proc = subprocess.run(
            [sys.executable, str(target)],
            cwd=str(here),
            capture_output=True,
            text=True,
        )

        if proc.returncode == 0:
            # simulation_script.py 자체 출력 그대로 보여주기
            if proc.stdout:
                print(proc.stdout, end="")
            print("================================================")
            print(f"loop {itr} : simulation success!!")
            print("================================================")
        else:
            if proc.stdout:
                print(proc.stdout, end="")
            if proc.stderr:
                print(proc.stderr, file=sys.stderr, end="")
                sys.stderr.flush()
            print("================================================")
            print(f"loop {itr} : simulation failed!! (exit={proc.returncode})")
            print("================================================")
            if stop_on_fail:
                break

        time.sleep(sleep_sec)


if __name__ == "__main__":
    run_many()


