import sys
import traceback
import logging
import portalocker

# sys.path.insert(0, r"/gpfs/home1/r1jae262/jupyter/git/pyaedt_library/src/")
sys.path.insert(0, r"../git/pyaedt_library/src/")
sys.path.insert(0, r"Y:/git/pyaedt_library/src/")

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

    def __init__(self) :

        self.NUM_CORE = 8
        self.NUM_TASK = 1

        
        os_name = platform.system()
        if os_name == "Windows":
            GUI = False
        else :
            GUI = True

        self.desktop = pyDesktop(version=None, non_graphical=GUI)

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



        # self.desktop.create_project(name=self.PROJECT_NAME)




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



    def run(self):
        """시뮬레이션을 실행합니다."""
        sim1 = self

                
        project1 = sim1.desktop.create_project(path=f"./simulation/{sim1.PROJECT_NAME}", name=sim1.PROJECT_NAME)
        design1 = project1.create_design(name="HFSS_design", solver="HFSS", solution=None)

        sim1.project = project1


        input_data = sim1.set_variable(design1)


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


        project1.delete()



if __name__ == "__main__":
    import traceback
    import sys

    sim = Simulation()

    for i in range(5000):

        try :
            sim.run()
        except Exception as e:
            print(f"Error in iteration {i}:", file=sys.stderr)
            print(traceback.format_exc(), file=sys.stderr)

            sim.project.delete()
            del sim
            sim = Simulation()






        