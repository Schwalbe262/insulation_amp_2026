import sys
import traceback
import logging
import portalocker
import os

# 경로 설정 - 플랫폼에 따라 다르게 처리
if os.name == 'nt':  # Windows
    sys.path.insert(0, r"Y:/git/pyaedt_library/src/")
else:  # Linux/Unix
    # Linux 서버 경로들 시도
    possible_paths = [
        # r"/gpfs/home1/r1jae262/jupyter/git/pyaedt_library/src/",
        r"../pyaedt_library/src/",
        os.path.join(os.path.dirname(__file__), "../git/pyaedt_library/src/"),
    ]
    for path in possible_paths:
        if os.path.exists(path):
            sys.path.insert(0, path)
            break

import pyaedt_module
from pyaedt_module.core import pyDesktop
import os
import time
from datetime import datetime

import math
import copy

import pandas as pd

from module.modeling import create_winding, create_port, create_PCB, create_region
from module.variable import set_variable
from module.HFSS_analyze import HFSS_analyze, get_HFSS_results, simulation_report
from module.circuit_analyze import create_HFSS_link_model, simulation_setup, create_schematic, create_output_variables, create_report, change_R

import platform
import csv

from scipy.signal import find_peaks




class Simulation() :

    def __init__(self, desktop=None) :

        self.NUM_CORE = 4
        self.NUM_TASK = 1

        # Desktop은 바깥에서 생성(with 포함)해서 주입하는 것을 권장
        # (루프 중 프로젝트 close/delete가 Desktop 핸들을 무효화시키는 문제를 줄이기 위함)
        self.desktop = desktop

    

    def create_simulation_name(self):

        file_path = "./simulation_num.txt"

        # 파일이 존재하지 않으면 생성
        if not os.path.exists(file_path):
            with open(file_path, "w", encoding="utf-8") as file:
                file.write("1")

        # 읽기/쓰기 모드로 파일 열기
        with open(file_path, "r+", encoding="utf-8") as file:
            # 파일 잠금: LOCK_EX는 배타적 잠금,  블로킹 모드로 실행 (Windows/Linux 호환)
            portalocker.lock(file, portalocker.LOCK_EX)

            # 파일에서 값 읽기
            content = int(file.read().strip())
            self.num = content
            self.PROJECT_NAME = f"simulation{content}"
            content += 1

            # 파일 포인터를 처음으로 되돌리고, 파일 내용 초기화 후 새 값 쓰기
            file.seek(0)
            file.truncate()
            file.write(str(content))


    def set_variable(self, design):
        return set_variable(self, design)

    def create_winding(self, design, name, up=True, *args, **kwargs):
        return create_winding(design, name, up, *args, **kwargs)

    def create_port(self, design, name, ter_ref, ter_face):
        return create_port(design, name, ter_ref, ter_face)

    def create_PCB(self, design):
        return create_PCB(design)

    def create_region(self, design):    
        return create_region(design)

    def HFSS_analyze(self, project, design):
        return HFSS_analyze(self, project, design)

    def get_HFSS_results(self, project, design):
        return get_HFSS_results(project, design)

    def simulation_report(self, design, start_time):    
        return simulation_report(design, start_time)

    def create_HFSS_link_model(self, link_name="HFSS_link_model", project=None, HFSS_design=None, circuit_design=None, Tx_port=None, Rx_port=None):
        return create_HFSS_link_model(link_name=link_name, project=project, HFSS_design=HFSS_design, circuit_design=circuit_design, Tx_port=Tx_port, Rx_port=Rx_port)

    def simulation_setup(self, circuit_design=None):
        return simulation_setup(circuit_design=circuit_design)

    def create_schematic(self, circuit_design=None):
        return create_schematic(circuit_design=circuit_design)

    def create_output_variables(self, circuit_design=None):
        return create_output_variables(circuit_design=circuit_design)

    def create_report(self, project, circuit_design=None, name=""):
        return create_report(project=project, circuit_design=circuit_design, name=name)

    def change_R(self, circuit_design=None, R=None):
        return change_R(circuit_design=circuit_design, R=R)



def run(simulation=None):
    """시뮬레이션을 실행합니다."""
    sim1 = simulation

    sim1.create_simulation_name()

    # simulation 디렉토리 생성 (존재하지 않으면)
    simulation_dir = "./simulation"
    if not os.path.exists(simulation_dir):
        os.makedirs(simulation_dir, exist_ok=True)
    
    # 절대 경로로 변환
    project_path = os.path.abspath(os.path.join(simulation_dir, sim1.PROJECT_NAME))
    
    # desktop이 None이거나 유효하지 않은지 확인
    if sim1.desktop is None:
        raise RuntimeError("Desktop instance is None. Cannot create project.")
    
    try:
        project1 = sim1.desktop.create_project(path=project_path, name=sim1.PROJECT_NAME)
    except Exception as e:
        error_msg = f"Failed to create project '{sim1.PROJECT_NAME}' at path '{project_path}': {e}\n"
        print(error_msg, file=sys.stderr)
        sys.stderr.flush()
        raise
    
    design1 = project1.create_design(name="HFSS_design", solver="HFSS", solution=None)

    sim1.project = project1


    input_data = sim1.set_variable(design1)

    print(input_data)



    coil_variable = {
        "color": [255, 10, 10],
        "turns": int(design1.variables["Tx_turns"]),
        "layer": int(design1.variables["Tx_layer"]),
        "outer_x": "Tx_outer_x",
        "outer_y": "Tx_outer_y",
        "fillet": "Tx_fillet",
        "inner": "Tx_inner",
        "fill_factor": "Tx_fill_factor",
        "theta1": "Tx_theta1",
        "theta2": "Tx_theta2",
        "PCB_thickness": "PCB_thickness",
        "coil_gap": "Tx_Tx_gap",
        "move": "(PCB_thickness + Tx_Rx_gap)/2",
    }

    Tx_winding, Tx_ter1, Tx_ter2, Tx_ter_face, Tx_width = sim1.create_winding(design1, name="Tx", up=True, **coil_variable)
    design1.modeler.mirror(assignment=[Tx_winding, Tx_ter1, Tx_ter2, Tx_ter_face], origin=[0,0,0], vector=[-1,0,0])
    Tx_port = sim1.create_port(design=design1, name="Tx", ter_ref=Tx_ter1, ter_face=Tx_ter_face)


    coil_variable = {
        "color": [10, 10, 255],
        "turns": int(design1.variables["Rx_turns"]),
        "layer": int(design1.variables["Rx_layer"]),
        "outer_x": "Rx_outer_x",
        "outer_y": "Rx_outer_y",
        "fillet": "Rx_fillet",
        "inner": "Rx_inner",
        "fill_factor": "Rx_fill_factor",
        "theta1": "Rx_theta1",
        "theta2": "Rx_theta2",
        "PCB_thickness": "PCB_thickness",
        "coil_gap": "Rx_Rx_gap",
        "move": "-((PCB_thickness + Tx_Rx_gap)/2)",
    }

    Rx_winding, Rx_ter1, Rx_ter2, Rx_ter_face, Rx_width = sim1.create_winding(design1, name="Rx", up=False, **coil_variable)
    Rx_port = sim1.create_port(design=design1, name="Rx", ter_ref=Rx_ter1, ter_face=Rx_ter_face)

    PCB = sim1.create_PCB(design1)

    design1.modeler.subtract(blank_list=PCB, tool_list=[Tx_winding, Tx_ter1, Tx_ter2, Rx_winding, Rx_ter1, Rx_ter2], keep_originals=True)

    region = sim1.create_region(design1)

    start_time = time.time()

    setup = sim1.HFSS_analyze(project1, design1)

    HFSS_results = sim1.get_HFSS_results(project1, design1)

    simulation_report = sim1.simulation_report(design1, start_time)

    design2 = project1.create_design(name="circuit_design", solver="Circuit", solution=None)

    # link name 중요함 (HFSS_design 숫자 형태여야 제대로 link 됨)
    sim1.create_HFSS_link_model(link_name="HFSS_design1", project=project1, HFSS_design=design1, circuit_design=design2, Tx_port=Tx_port, Rx_port=Rx_port)

    sim1.simulation_setup(circuit_design=design2)

    sim1.create_schematic(circuit_design=design2)


    sim1.create_output_variables(circuit_design=design2)


    sim1.change_R(circuit_design=design2, R=28)
    design2.Analyze("LinearFrequency")
    circuit_data1 = sim1.create_report(project=project1, circuit_design=design2, name="28")

    sim1.change_R(circuit_design=design2, R=50)
    design2.Analyze("LinearFrequency")
    circuit_data2 = sim1.create_report(project=project1, circuit_design=design2, name="50")

    sim1.change_R(circuit_design=design2, R=100)
    design2.Analyze("LinearFrequency")
    circuit_data3 = sim1.create_report(project=project1, circuit_design=design2, name="100")

    sim1.change_R(circuit_design=design2, R=200)
    design2.Analyze("LinearFrequency")
    circuit_data4 = sim1.create_report(project=project1, circuit_design=design2, name="200")

    sim1.change_R(circuit_design=design2, R=1000)
    design2.Analyze("LinearFrequency")
    circuit_data5 = sim1.create_report(project=project1, circuit_design=design2, name="1000")


    sim_time = time.time() - start_time
    pd_sim_time = pd.DataFrame({"sim_time": [sim_time]})


    output_data = pd.concat([input_data, HFSS_results, circuit_data1, circuit_data2, circuit_data3, circuit_data4, circuit_data5, simulation_report, pd_sim_time], axis=1)

    current_dir = os.getcwd()
    csv_file = os.path.join(current_dir, f"output_data_insulation_amp_2026_v1.csv")

    if os.path.isfile(csv_file):
        output_data.to_csv(csv_file, mode='a', index=False, header=False)
    else:
        output_data.to_csv(csv_file, mode='w', index=False, header=True)

    print("simulation done", flush=True)


    project1.close()

    print("project close", flush=True)

    time.sleep(1)

    project1.delete()

    print("project delete", flush=True)

    # Desktop 종료/kill은 main loop의 finally에서만 수행 (중복 kill로 다음 Desktop init이 불안정해질 수 있음)
    # sim1.desktop.close()
    # sim1.desktop.kill_process()
    # print("desktop close", flush=True)



"""
if __name__ == "__main__":
    import traceback
    import sys
    
    # 초기 에러 로깅 설정
    try:
        # 표준 출력과 에러를 모두 파일로 리다이렉트 (디버깅용)
        log_dir = "./simul_log"
        if not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)
        
        # 초기 import 에러 확인
        try:
            sim = Simulation()
        except Exception as e:
            error_msg = f"Failed to create Simulation instance: {traceback.format_exc()}\n"
            print(error_msg, file=sys.stderr)
            sys.stderr.flush()
            sys.exit(1)
        
        for i in range(5000):
            try:
                sim.run()
            except Exception as e:
                error_msg = f"Error in iteration {i}:\n{traceback.format_exc()}\n"
                print(error_msg, file=sys.stderr)
                sys.stderr.flush()
                
                # 안전하게 정리
                try:
                    if hasattr(sim, 'project') and sim.project is not None:
                        sim.project.delete()
                except:
                    pass
                
                try:
                    if hasattr(sim, 'desktop') and sim.desktop is not None:
                        sim.desktop.kill_process()
                except:
                    pass
                
                try:
                    del sim
                except:
                    pass
                
                # 새 인스턴스 생성
                try:
                    sim = Simulation()
                except Exception as e2:
                    error_msg = f"Failed to create new Simulation instance at iteration {i}:\n{traceback.format_exc()}\n"
                    print(error_msg, file=sys.stderr)
                    sys.stderr.flush()
                    break
                    
    except Exception as e:
        # 최상위 레벨 에러 처리
        error_msg = f"Fatal error in main:\n{traceback.format_exc()}\n"
        print(error_msg, file=sys.stderr)
        sys.stderr.flush()
        sys.exit(1)
"""


if __name__ == "__main__":
    import traceback
    import sys

    # SLURM(out 파일)에서는 stdout/stderr가 block-buffering이라 print가 바로 안 찍히는 경우가 많음
    # 가능하면 라인 버퍼링으로 전환 + print flush 사용
    try:
        sys.stdout.reconfigure(line_buffering=True)
        sys.stderr.reconfigure(line_buffering=True)
    except Exception:
        pass

    os_name = platform.system()
    if os_name == "Windows":
        GUI = False
    else:
        GUI = True

    # 1회 실행을 1만 번 반복
    for itr in range(100000):
        desktop = None
        try:
            # close_on_exit=True인 상태에서 __exit__가 블로킹되어 다음 루프로 못 넘어가는 케이스가 있어
            # 컨텍스트 exit에서는 release만 하고, 종료는 finally에서 kill_process로 확실히 정리한다.
            # 이전 loop에서 강제 kill 시 /tmp/aedt_grpc.lock 이 남을 수 있어, init 전에 제거 시도
            try:
                import tempfile
                from pathlib import Path
                lock_file = Path(tempfile.gettempdir()) / "aedt_grpc.lock"
                if lock_file.exists():
                    lock_file.unlink()
            except Exception:
                pass

            print("================================================", flush=True)
            print(f"loop {itr} : desktop init start", flush=True)
            print("================================================", flush=True)
            with pyDesktop(version=None, non_graphical=GUI, close_on_exit=False, new_desktop=True) as desktop:
                print(f"loop {itr} : desktop init done (pid={getattr(desktop, 'pid', None)})", flush=True)
                print(f"loop {itr} : simulation start!!", flush=True)
                sim = Simulation(desktop=desktop)
                run(simulation=sim)
                print("================================================", flush=True)
                print(f"loop {itr} : simulation {sim.PROJECT_NAME} success!!", flush=True)
                print("================================================", flush=True)
        except Exception:
            error_msg = f"Error in iteration {itr}:\n{traceback.format_exc()}"
            print("================================================", flush=True)
            print(error_msg, file=sys.stderr)
            print("================================================", flush=True)
            sys.stderr.flush()
            print("================================================", flush=True)
            print(f"loop {itr} : simulation failed!!", flush=True)
            print("================================================", flush=True)
            # 실패해도 다음 iteration 진행
        finally:
            # Linux에서 1회 실행 후 AEDT 프로세스가 남아 다음 실행을 깨는 케이스가 있어,
            # 컨텍스트 종료와 별개로 프로세스를 확실히 종료한다.
            if desktop is not None:
                # 주의: desktop.close()는 일부 환경에서 블로킹되어 다음 루프로 못 넘어갈 수 있음
                # (close_on_exit=False로 둔 만큼 여기서는 호출하지 않음)
                try:
                    print(f"[cleanup] killing AEDT pid={getattr(desktop, 'pid', None)}", flush=True)
                    desktop.kill_process()
                    print("[cleanup] kill done", flush=True)
                    # kill 후 pid를 리셋해서, 다음 로직에서 죽은 pid를 재사용하지 않도록 한다
                    try:
                        desktop.aedt_process_id = None
                    except Exception:
                        pass
                except Exception:
                    pass
            # PyAEDT Desktop init은 /tmp/aedt_grpc.lock 을 사용함. 강제 kill 시 lock 파일이 남아
            # 다음 init이 꼬일 수 있어 cleanup에서 제거 시도.
            try:
                import tempfile
                from pathlib import Path
                lock_file = Path(tempfile.gettempdir()) / "aedt_grpc.lock"
                if lock_file.exists():
                    lock_file.unlink()
            except Exception:
                pass
            # kill 이전/이후 상관없이 flush 보장
            try:
                sys.stdout.flush()
                sys.stderr.flush()
            except Exception:
                pass
            print("[cleanup] sleep 2s", flush=True)
            # AEDT/UDS 리소스 해제에 시간이 걸릴 수 있어 여유를 둔다
            time.sleep(8)
        

