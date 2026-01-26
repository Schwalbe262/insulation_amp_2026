import sys
import traceback
import logging
import portalocker

sys.path.insert(0, r"/gpfs/home1/r1jae262/jupyter/git/pyaedt_library/src/")
sys.path.insert(0, r"Y:/git/pyaedt_library/src/")

import pyaedt_module
from pyaedt_module.core import pyDesktop
import os
import time
from datetime import datetime

import math
import copy

import pandas as pd

from module.modeling import create_winding, create_PCB, create_region
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


        