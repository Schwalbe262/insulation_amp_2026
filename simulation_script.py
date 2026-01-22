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
from module.HFSS_analyze import HFSS_analyze, get_HFSS_results

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
        """Set variables using the variable module."""
        return set_variable(self, design)


    def create_winding(self, design, name, up=True, *args, **kwargs):
        """Create a winding using the modeling module."""
        return create_winding(design, name, up, *args, **kwargs)


    def create_PCB(self, design):
        """Create a PCB using the modeling module."""
        return create_PCB(design)

    def create_region(self, design):    
        """Create a region in the design."""
        return create_region(design)

    def HFSS_analyze(self, project, design):
        """Set up and execute HFSS analysis using the HFSS_analyze module."""
        return HFSS_analyze(self, project, design)

    def get_HFSS_results(self, project, design):
        """Get HFSS results using the HFSS_analyze module."""
        return get_HFSS_results(project, design)