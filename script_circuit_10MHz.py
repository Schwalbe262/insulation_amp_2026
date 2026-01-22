import sys
import traceback
import logging
import portalocker
import fcntl

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

import platform
import csv

from scipy.signal import find_peaks




class Simulation() :

    def __init__(self) :

        self.NUM_CORE = 1
        self.NUM_TASK = 1

        
        os_name = platform.system()
        if os_name == "Windows":
            GUI = False
        else :
            GUI = True

        self.desktop = pyDesktop(version=None, non_graphical=GUI)

        file_path = "simulation_num.txt"

        # 파일이 존재하지 않으면 생성
        if not os.path.exists(file_path):
            with open(file_path, "w", encoding="utf-8") as file:
                file.write("1")

        # 읽기/쓰기 모드로 파일 열기
        with open(file_path, "r+", encoding="utf-8") as file:
            # 파일 잠금: LOCK_EX는 배타적 잠금,  블로킹 모드로 실행
            fcntl.flock(file, fcntl.LOCK_EX)

            # 파일에서 값 읽기
            content = int(file.read().strip())
            self.num = content
            self.PROJECT_NAME = f"simulation{content}"
            content += 1

            # 파일 포인터를 처음으로 되돌리고, 파일 내용 초기화 후 새 값 쓰기
            file.seek(0)
            file.truncate()
            file.write(str(content))

            # 파일은 with 블록 종료 시 자동으로 닫히며, 잠금도 해제됨



        log_simulation(number=self.num, pid=self.desktop.pid)




        # simulation_log 폴더에 로그 파일 생성 및 FileHandler 설정
        log_folder = "simulation_log"
        os.makedirs(log_folder, exist_ok=True)
        log_file_path = os.path.join(log_folder, f"{self.PROJECT_NAME}_log.txt")

        # FileHandler를 생성해서 로거에 추가
        file_handler = logging.FileHandler(log_file_path, mode="a", encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)

        # root logger 또는 원하는 로거에 핸들러 추가
        logger = logging.getLogger()  # 또는 logging.getLogger(self.PROJECT_NAME)
        logger.setLevel(logging.DEBUG)
        logger.addHandler(file_handler)


    def simulation(self):
        self.start_time = time.time()
        

        

        self.create_design(name="HFSS_design")
        print("manual log : set variable start")
        self.set_variable(self.design)
        print("manual log : create model start")
        self.create_model(self.design)
        print("manual log : analyze start")
        self.analyze()


    def create_design(self, name) : 
    
        self.project = self.desktop.create_project()
        self.design = self.project.create_design(name=name, solver="HFSS", solution=None)


    
    def detect_Speak(self, freq=None, data=None) :

        peaks_prom, properties = find_peaks(data, prominence=1)

        if freq is not None :
            peak_freqs_prom = freq[peaks_prom].values
            peak_vals_prom = data[peaks_prom].values
            return peak_freqs_prom, peak_vals_prom
        
        elif freq is None :
            peak_vals_prom = data[peaks_prom].values
            return peak_vals_prom
        

    def set_variable(self, design) :

        

        # self.Tx_outer_x = design.random_variable(variable_name="Tx_outer_x", lower=1.5, upper=3, resolution=0.1, unit="mm")
        self.Tx_outer_x = design.random_variable(variable_name="Tx_outer_x", lower=0.8, upper=2.5, resolution=0.1, unit="mm")
        self.Tx_ratio = design.random_variable(lower=0.4, upper=0.9, resolution=0.01)
        # design["Tx_outer_y"] = f"{self.Tx_ratio} * {self.Tx_outer_x}mm"
        self.Tx_outer_y = self.Tx_ratio * self.Tx_outer_x

        Tx_inner_min = 0.4*min(self.Tx_outer_x, self.Tx_outer_y)
        Tx_inner_max = 0.8*min(self.Tx_outer_x, self.Tx_outer_y)
        self.Tx_inner = design.random_variable(variable_name="Tx_inner", lower=Tx_inner_min, upper=Tx_inner_max, resolution=0.01, unit="mm")

        Tx_fillet_min = self.Tx_inner * (math.tan(75 * math.pi/180)  - 1) / math.tan(75 * math.pi/180)  * 1.1
        Tx_fillet_max = self.Tx_inner * 0.8 if self.Tx_inner * 0.8 > Tx_fillet_min else self.Tx_inner * 0.9
        self.Tx_fillet = design.random_variable(variable_name="Tx_fillet", lower=Tx_fillet_min, upper=Tx_fillet_max, resolution=0.01, unit="mm")

        self.Tx_fill_factor = design.random_variable(variable_name="Tx_fill_factor", lower=0.3, upper=0.8, resolution=0.01, unit=None)

        # design["Tx_theta1"] = "15*pi/180"
        # design["Tx_theta2"] = "75*pi/180"


        self.Tx_Rx_ratio = design.random_variable(lower=0.6, upper=1.5, resolution=0.01)
        # design["Rx_outer_x"] = f"{self.Tx_outer_x} * {self.Tx_Rx_ratio}mm"
        self.Rx_outer_x = self.Tx_outer_x * self.Tx_Rx_ratio

        self.Rx_ratio = design.random_variable(lower=0.4, upper=0.9, resolution=0.01)
        # design["Rx_outer_y"] = f"{self.Rx_ratio} * {self.Rx_outer_x}mm"
        self.Rx_outer_y = self.Rx_ratio * self.Rx_outer_x

        Rx_inner_min = 0.4*min(self.Rx_outer_x, self.Rx_outer_y)
        Rx_inner_max = 0.8*min(self.Rx_outer_x, self.Rx_outer_y)
        self.Rx_inner = design.random_variable(variable_name="Rx_inner", lower=Rx_inner_min, upper=Rx_inner_max, resolution=0.01, unit="mm")

        Rx_fillet_min = self.Rx_inner * (math.tan(75 * math.pi/180)  - 1) / math.tan(75 * math.pi/180)  * 1.1
        Rx_fillet_max = self.Rx_inner * 0.8 if self.Rx_inner * 0.8 > Rx_fillet_min else self.Rx_inner * 0.9
        self.Rx_fillet = design.random_variable(variable_name="Rx_fillet", lower=Rx_fillet_min, upper=Rx_fillet_max, resolution=0.01, unit="mm")

        self.Rx_fill_factor = design.random_variable(variable_name="Rx_fill_factor", lower=0.3, upper=0.8, resolution=0.01, unit=None)

        # design["Rx_theta1"] = "15*pi/180"
        # design["Rx_theta2"] = "75*pi/180"


        # self.Tx_turns = design.random_variable(variable_name=None, lower=4, upper=8, resolution=1)
        self.Tx_turns = design.random_variable(variable_name=None, lower=5, upper=12, resolution=1)
        # self.Rx_turns = design.random_variable(variable_name=None, lower=4, upper=15, resolution=1)
        # self.Rx_turns = int(round(self.Tx_turns * design.random_variable(variable_name=None, lower=1.3, upper=1.7, resolution=0.01), 0))
        self.Rx_turns = int(round(self.Tx_turns * design.random_variable(variable_name=None, lower=0.6, upper=1.5, resolution=0.01), 0))

        preg = design.random_variable(lower=0.02, upper=0.06, resolution=0.001)


        self.Tx_preg = preg

        thick_ratio = design.random_variable(lower=0.25, upper=2.5, resolution=0.01)

        self.Tx_thick = 0.035 * thick_ratio

        self.Rx_preg = preg
        self.Rx_thick = 0.035 * thick_ratio


        self.Tx_Rx_gap = design.random_variable(lower=0.05, upper=0.25, resolution=0.01)

        self.Tx_shift = design.random_variable(lower=0, upper=0.5, resolution=0.01)
        self.Rx_shift = design.random_variable(lower=0, upper=0.5, resolution=0.01)

        self.Tx_shift = 0
        self.Rx_shift = 0

        # [
        #     self.Tx_turns, self.Rx_turns, self.Tx_outer_x, self.Tx_outer_y, self.Tx_ratio,
        #     self.Rx_outer_x, self.Rx_outer_y, self.Rx_ratio,
        #     self.Tx_inner, self.Rx_inner, self.Tx_fillet, self.Rx_fillet,
        #     self.Tx_fill_factor, self.Rx_fill_factor,
        #     self.Tx_preg, self.Rx_preg, self.Tx_thick, self.Rx_thick,
        #     self.Tx_Rx_gap, self.Tx_shift, self.Rx_shift
        # ] = [4.0, 7.0, 1.49, 1.34, 0.9, 1.45, 1.26, 0.87, 0.99, 0.56, 0.82, 0.46, 0.3, 0.3, 0.02, 0.02, 0.035/3, 0.035/3, 0.105, 0.0, 0.0]

        design["Tx_turns"] = f"{self.Tx_turns}"
        design["Rx_turns"] = f"{self.Rx_turns}"
        design["Tx_outer_x"] = f"{self.Tx_outer_x}mm"
        design["Tx_outer_y"] = f"{self.Tx_ratio} * {self.Tx_outer_x}mm"
        design["Rx_outer_x"] = f"{self.Rx_outer_x}mm"
        design["Rx_outer_y"] = f"{self.Rx_ratio} * {self.Rx_outer_x}mm"

        design["Tx_inner"] = f"{self.Tx_inner}mm"
        design["Rx_inner"] = f"{self.Rx_inner}mm"
        design["Tx_fillet"] = f"{self.Tx_fillet}mm"
        design["Rx_fillet"] = f"{self.Rx_fillet}mm"

        design["Tx_fill_factor"] = f"{self.Tx_fill_factor}"
        design["Rx_fill_factor"] = f"{self.Rx_fill_factor}"

        design["Tx_theta1"] = "15*pi/180"
        design["Tx_theta2"] = "75*pi/180"
        design["Rx_theta1"] = "15*pi/180"
        design["Rx_theta2"] = "75*pi/180"

        design["Tx_Rx_gap"] = f"{self.Tx_Rx_gap}mm"
        design["thick"] = f"{self.Tx_thick}mm"
        design["preg"] = f"{preg}mm"

        columns = [
            'Tx_turns', 'Rx_turns', 'Tx_outer_x', 'Tx_outer_y', 'Tx_ratio',
            'Rx_outer_x', 'Rx_outer_y', 'Rx_ratio', 'Tx_inner', 'Rx_inner',
            'Tx_fillet', 'Rx_fillet', 'Tx_fill_factor', 'Rx_fill_factor',
            'Tx_preg', 'Rx_preg', 'Tx_thick', 'Rx_thick', 'Tx_Rx_gap',
            'Tx_shift', 'Rx_shift'
        ]

        self.input_raw = [self.Tx_turns, self.Rx_turns, self.Tx_outer_x, self.Tx_outer_y, self.Tx_ratio, self.Rx_outer_x, self.Rx_outer_y, self.Rx_ratio, 
                      self.Tx_inner, self.Rx_inner, self.Tx_fillet, self.Rx_fillet, self.Tx_fill_factor, self.Rx_fill_factor,
                      self.Tx_preg, self.Rx_preg, thick_ratio, thick_ratio, self.Tx_Rx_gap, self.Tx_shift, self.Rx_shift]
        
        self.input = pd.DataFrame([self.input_raw], columns=columns)


    def create_model(self, design) :

        # Tx

        winding_variables = {"outer_x": "Tx_outer_x", "outer_y": "Tx_outer_y", "fillet": "Tx_fillet", "inner": "Tx_inner", "fill_factor": "Tx_fill_factor", "theta1": "Tx_theta1", "theta2": "Tx_theta2"}
        Tx_coil1 = design.model3d.winding.coil_points(turns=self.Tx_turns, **winding_variables)
        Tx_coil1.points.insert(0, [f"0mm", f"{Tx_coil1.points[0][1]}", Tx_coil1.points[0][2]])

        coil_Tx1 = design.model3d.winding.create_polyline(name="Tx_winding1", points=Tx_coil1.points, width=Tx_coil1.width, height=f"{self.Tx_thick}mm")
        self.coil = coil_Tx1

        # coil_Tx1_box = design.model3d.create_box(origin=Tx_coil1[0], )

        coil_Tx1.move([0,0,-(self.Tx_thick+self.Tx_preg)/2])

        # Tx_coil2 = copy.deepcopy(Tx_coil1)

        # Tx_coil2.points[-1] = [f"({Tx_coil2.points[-1][0]}) - {self.Tx_shift}*({Tx_coil2.wg})",f"({Tx_coil2.points[-1][1]})",f"{Tx_coil2.points[-1][2]}"]
        # Tx_coil2.points.append([f"({Tx_coil2.points[-1][0]})",f"({Tx_coil2.points[-1][1]}) + {self.Tx_shift}*({Tx_coil2.wg})",f"{Tx_coil2.points[-1][2]}"])
        # Tx_coil2.points[0] = [f"({Tx_coil2.points[0][0]})",f"({Tx_coil2.points[0][1]}) + {self.Tx_shift}*({Tx_coil2.wg})",f"{Tx_coil2.points[0][2]}"]

        # coil_Tx2 = design.model3d.winding.create_polyline(name="Tx_winding2", points=Tx_coil2.points, width=Tx_coil2.width, height=f"{self.Tx_thick}mm")
        # coil_Tx2.mirror(origin=[0,0,0], vector=[1,0,0])
        # coil_Tx2.move([f"-{self.Tx_shift}*({Tx_coil2.wg})",f"-{self.Tx_shift}*({Tx_coil2.wg})",-(self.Tx_thick+self.Tx_preg)/2])

        # coil_Tx = design.model3d.unite(assignment=[coil_Tx1, coil_Tx2, Tx_via1])
        # design.modeler.subtract(blank_list=coil_Tx, tool_list=Tx_via2, keep_originals=False)

        coil_Tx = coil_Tx1

        coil_Tx.transparency = 0
        coil_Tx.color = [255, 10, 10]
        coil_Tx.material_name = "copper"


        point1 = [f"{Tx_coil1.points[0][0]}-{Tx_coil1.width}/2", Tx_coil1.points[0][1], f"({Tx_coil1.points[0][2]} - ({self.Tx_thick})/2)mm"]
        point2 = [f"{Tx_coil1.points[0][0]}-{Tx_coil1.width}/2", Tx_coil1.points[0][1], f"({Tx_coil1.points[0][2]} + ({self.Tx_preg}) + 3*({self.Tx_thick})/2)mm"]
        Tx_ter1 = design.model3d.winding.create_polyline(name="Tx_ter1", points=[point1, point2], width=Tx_coil1.width, height=Tx_coil1.width)
        point1 = [f"{Tx_coil1.points[-1][0]}+{Tx_coil1.width}/2", Tx_coil1.points[-1][1], f"({Tx_coil1.points[-1][2]} - ({self.Tx_thick})/2)mm"]
        point2 = [f"{Tx_coil1.points[-1][0]}+{Tx_coil1.width}/2", Tx_coil1.points[-1][1], f"({Tx_coil1.points[-1][2]} + ({self.Tx_preg}) + 3*({self.Tx_thick})/2)mm"]
        Tx_ter2 = design.model3d.winding.create_polyline(name="Tx_ter2", points=[point1, point2], width=Tx_coil1.width, height=Tx_coil1.width)

        Tx_ter1.material_name = "pec"
        Tx_ter2.material_name = "pec"

        
        Tx_ter1.move([0,0,-(self.Tx_thick+self.Tx_preg)/2])
        Tx_ter2.move([0,0,-(self.Tx_thick+self.Tx_preg)/2])


        Tx_ter_edge1 = Tx_ter1.top_face_y.top_edge_z
        Tx_ter_edge2 = Tx_ter2.bottom_face_y.top_edge_z

        Tx_ter_edges = design.modeler.create_object_from_edge([Tx_ter_edge1, Tx_ter_edge2], non_model=False)
        Tx_ter_face = design.modeler.connect(Tx_ter_edges)

        Tx_port = design.lumped_port(assignment=Tx_ter_face[0], reference=[Tx_ter1], create_port_sheet=False, port_on_plane=True, integration_line=0, impedance=50, name="Tx_port", renormalize=True, deembed=False, terminals_rename=True)



        # Rx

        winding_variables = {"outer_x": "Rx_outer_x", "outer_y": "Rx_outer_y", "fillet": "Rx_fillet", "inner": "Rx_inner", "fill_factor": "Rx_fill_factor", "theta1": "Rx_theta1", "theta2": "Rx_theta2"}
        Rx_coil1 = design.model3d.winding.coil_points(turns=self.Rx_turns, **winding_variables)
        Rx_coil1.points.insert(0, [f"{Rx_coil1.points[0][0]}", f"{Rx_coil1.points[0][1]} - 1mm", Rx_coil1.points[0][2]])

        Rx_via1 = design.model3d.winding.create_via(name="Rx_via", center=Rx_coil1.points[-1], outer_R=f"0.8*{Rx_coil1.width}/2", inner_R=f"0.6*{Rx_coil1.width}/2", height=f"{2*self.Rx_thick+self.Rx_preg}mm", via_pad_R=f"1.2*{Rx_coil1.width}/2", via_pad_thick=f"{self.Rx_thick}mm")
        Rx_via2 = design.model3d.winding.create_via(name="Rx_sub_via", center=Rx_coil1.points[-1], outer_R=f"0.6*{Rx_coil1.width}/2", height="1mm*2")
        Rx_via1.move([0,0,-(self.Tx_Rx_gap+self.Tx_thick+self.Rx_thick+self.Tx_preg/2+self.Rx_preg/2)])
        Rx_via2.move([0,0,-(self.Tx_Rx_gap+self.Tx_thick+self.Rx_thick+self.Tx_preg/2+self.Rx_preg/2)])

        coil_Rx1 = design.model3d.winding.create_polyline(name="Rx_winding1", points=Rx_coil1.points, width=Rx_coil1.width, height=f"{self.Rx_thick}mm")
        coil_Rx1.move([0,0,(self.Rx_thick+self.Rx_preg)/2 - (self.Tx_Rx_gap+self.Tx_thick+self.Rx_thick+self.Tx_preg/2+self.Rx_preg/2)])

        Rx_coil2 = copy.deepcopy(Rx_coil1)

        Rx_coil2.points[-1] = [f"({Rx_coil2.points[-1][0]}) - {self.Rx_shift}*({Rx_coil2.wg})",f"({Rx_coil2.points[-1][1]})",f"{Rx_coil2.points[-1][2]}"]
        Rx_coil2.points.append([f"({Rx_coil2.points[-1][0]})",f"({Rx_coil2.points[-1][1]}) + {self.Rx_shift}*({Rx_coil2.wg})",f"{Rx_coil2.points[-1][2]}"])
        Rx_coil2.points[0] = [f"({Rx_coil2.points[0][0]})",f"({Rx_coil2.points[0][1]}) + {self.Rx_shift}*({Rx_coil2.wg})",f"{Rx_coil2.points[0][2]}"]

        coil_Rx2 = design.model3d.winding.create_polyline(name="Rx_winding2", points=Rx_coil2.points, width=Rx_coil2.width, height=f"{self.Rx_thick}mm")
        coil_Rx2.mirror(origin=[0,0,0], vector=[1,0,0])
        coil_Rx2.move([f"-{self.Rx_shift}*({Rx_coil2.wg})",f"-{self.Rx_shift}*({Rx_coil2.wg})",-(self.Rx_thick+self.Rx_preg)/2 - (self.Tx_Rx_gap+self.Tx_thick+self.Rx_thick+self.Tx_preg/2+self.Rx_preg/2)])

        coil_Rx = design.model3d.unite(assignment=[coil_Rx1, coil_Rx2, Rx_via1])
        design.modeler.subtract(blank_list=coil_Rx, tool_list=Rx_via2, keep_originals=False)

        coil_Rx.transparency = 0
        coil_Rx.color = [10, 10, 255]
        coil_Rx.material_name = "copper"


        point1 = Rx_coil1.points[0]
        point2 = [point1[0], f"({point1[1]})-0.05mm", point1[2]]
        Rx_ter1 = design.model3d.winding.create_polyline(name="Rx_ter1", points=[point1, point2], width=Rx_coil1.width, height=f"{self.Rx_thick}mm")
        Rx_ter2 = design.model3d.winding.create_polyline(name="Rx_ter2", points=[point1, point2], width=Rx_coil1.width, height=f"{self.Rx_thick}mm")

        Rx_ter1.material_name = "pec"
        Rx_ter2.material_name = "pec"

        Rx_ter1.mirror(origin=[0,0,0], vector=[1,0,0])
        Rx_ter1.move([f"-{self.Rx_shift}*({Rx_coil2.wg})",0,-(self.Rx_thick+self.Rx_preg)/2 - (self.Tx_Rx_gap+self.Tx_thick+self.Rx_thick+self.Tx_preg/2+self.Rx_preg/2)])
        Rx_ter2.move([0,0,(self.Rx_thick+self.Rx_preg)/2 - (self.Tx_Rx_gap+self.Tx_thick+self.Rx_thick+self.Tx_preg/2+self.Rx_preg/2)])


        Rx_ter_edge1 = Rx_ter1.bottom_face_y.top_edge_x
        Rx_ter_edge2 = Rx_ter2.bottom_face_y.bottom_edge_x

        Rx_ter_edges = design.modeler.create_object_from_edge([Rx_ter_edge1, Rx_ter_edge2], non_model=False)
        Rx_ter_face = design.modeler.connect(Rx_ter_edges)

        Rx_port = design.lumped_port(assignment=Rx_ter_face[0], reference=[Rx_ter1], create_port_sheet=False, port_on_plane=True, integration_line=0, impedance=50, name="Rx_port", renormalize=True, deembed=False, terminals_rename=True)




        # PCB

        if self.Tx_outer_x > self.Rx_outer_x :
            outer_x = "Tx_outer_x"
        else :
            outer_x = "Rx_outer_x"

        if self.Tx_outer_y > self.Rx_outer_y :
            outer_y = "Tx_outer_y"
        else :
            outer_y = "Rx_outer_y"   

        origin = [f"-(1.4*{outer_x})", f"-(1.4*{outer_y})", f"-{(self.Tx_preg/2+self.Tx_thick+self.Tx_Rx_gap+2*self.Rx_thick+self.Rx_preg)}mm"]
        dimension = [f"2*(1.4*{outer_x})", f"2*(1.4*{outer_y})", f"{(self.Tx_preg+2*self.Tx_thick+self.Tx_Rx_gap+2*self.Rx_thick+self.Rx_preg)}mm"]
        PCB = design.modeler.create_box(
            origin = origin,
            sizes = dimension,
            name = "PCB",
            material = "FR4_epoxy"
        )

        PCB.color = [0 ,128 ,64]
        PCB.transparency = 0

        design.modeler.subtract(blank_list=PCB, tool_list=[coil_Tx, coil_Rx, Tx_ter1, Tx_ter2, Rx_ter1, Rx_ter2], keep_originals=True)



        region = design.modeler.create_air_region(x_pos="175",x_neg="175", y_pos="175",y_neg="175", z_pos = "3500", z_neg="3500")
        design.assign_material(assignment=region, material="vacuum")
        design.assign_radiation_boundary_to_objects(assignment=region, name="Radiation")



    def analyze(self) :

        setup = self.design.create_setup("Setup1")
        setup.props["Frequency"] = "10MHz"
        # setup["MaximumPasses"] = 15
        # setup["MaxDeltaS"] = 0.03
        setup["MaximumPasses"] = 10
        setup["MaxDeltaS"] = 0.001


        oDesign = self.project.SetActiveDesign(self.design.name)
        oModule = oDesign.GetModule("AnalysisSetup")

        sweep1 = oModule.InsertFrequencySweep("Setup1", 
            [
                "NAME:Sweep",
                "IsEnabled:="		, True,
                "RangeType:="		, "LinearCount",
                "RangeStart:="		, "50kHz",
                "RangeEnd:="		, "1MHz",
                "RangeCount:="		, 100,
                [
                    "NAME:SweepRanges",
                    [
                        "NAME:Subrange",
                        "RangeType:="		, "LinearCount",
                        "RangeStart:="		, "1MHz",
                        "RangeEnd:="		, "10MHz",
                        "RangeCount:="		, 100
                    ],
                    [
                        "NAME:Subrange",
                        "RangeType:="		, "LinearCount",
                        "RangeStart:="		, "10MHz",
                        "RangeEnd:="		, "500MHz",
                        "RangeCount:="		, 400
                    ]
                ],
                "Type:="		, "Fast",
                "SaveFields:="		, True,
                "SaveRadFields:="	, False,
                "GenerateFieldsForAllFreqs:=", False
            ])


        current_dir = os.getcwd()
        folder_path = os.path.join(current_dir, "simulation", f"{self.PROJECT_NAME}")
        os.makedirs(folder_path, exist_ok=True)  # 폴더가 없으면 생성
        file_path = os.path.join(folder_path, f"{self.PROJECT_NAME}.aedt")

        self.project.save_project(path=file_path)


        # design1.analyze(setup=f"{setup.name} : {sweep1.name}", cores=4, tasks=1)
        self.design.analyze(setup=f"{setup.name}", cores=self.NUM_CORE, tasks=self.NUM_TASK)




        result_expressions = []
        result_expressions.append(f"mag(Zt(Tx_port_T1,Tx_port_T1))")
        result_expressions.append(f"mag(Zt(Rx_port_T1,Rx_port_T1))")
        result_expressions.append(f"mag(Zt(Tx_port_T1,Rx_port_T1))")

        report1 = self.design.post.create_report(expressions=result_expressions, setup_sweep_name=None, domain='Sweep', 
                                        variations=None, primary_sweep_variable=None, secondary_sweep_variable=None, 
                                        report_category=None, plot_type='Rectangular Plot', context=None, subdesign_id=None, polyline_points=1001, plot_name="impedance_mag data")


        result_expressions = []
        result_expressions.append(f"re(Zt(Tx_port_T1,Tx_port_T1))")
        result_expressions.append(f"re(Zt(Rx_port_T1,Rx_port_T1))")
        result_expressions.append(f"re(Zt(Tx_port_T1,Rx_port_T1))")

        report2 = self.design.post.create_report(expressions=result_expressions, setup_sweep_name=None, domain='Sweep', 
                                        variations=None, primary_sweep_variable=None, secondary_sweep_variable=None, 
                                        report_category=None, plot_type='Rectangular Plot', context=None, subdesign_id=None, polyline_points=1001, plot_name="impedance_real data")


        result_expressions = []
        result_expressions.append(f"im(Zt(Tx_port_T1,Tx_port_T1))")
        result_expressions.append(f"im(Zt(Rx_port_T1,Rx_port_T1))")
        result_expressions.append(f"im(Zt(Tx_port_T1,Rx_port_T1))")
        result_expressions.append(f"im(Zt(Tx_port_T1,Rx_port_T1))/sqrt(im(Zt(Tx_port_T1,Tx_port_T1))*im(Zt(Rx_port_T1,Rx_port_T1)))")

        report3 = self.design.post.create_report(expressions=result_expressions, setup_sweep_name=None, domain='Sweep', 
                                        variations=None, primary_sweep_variable=None, secondary_sweep_variable=None, 
                                        report_category=None, plot_type='Rectangular Plot', context=None, subdesign_id=None, polyline_points=1001, plot_name="impedance_img data")



        result_expressions = []
        result_expressions.append(f"sqrt( im(Zt(Tx_port_T1,Tx_port_T1)) / im(Zt(Rx_port_T1,Rx_port_T1)) )")

        report4 = self.design.post.create_report(expressions=result_expressions, setup_sweep_name=None, domain='Sweep', 
                                        variations=None, primary_sweep_variable=None, secondary_sweep_variable=None, 
                                        report_category=None, plot_type='Rectangular Plot', context=None, subdesign_id=None, polyline_points=1001, plot_name="voltage_ratio data")
        


        result_expressions = []
        result_expressions.append(f"im(Zt(Tx_port_T1,Tx_port_T1))/2/pi/freq")
        result_expressions.append(f"im(Zt(Rx_port_T1,Rx_port_T1))/2/pi/freq")
        result_expressions.append(f"im(Zt(Tx_port_T1,Rx_port_T1))/2/pi/freq")

        report5 = self.design.post.create_report(expressions=result_expressions, setup_sweep_name=None, domain='Sweep', 
                                        variations=None, primary_sweep_variable=None, secondary_sweep_variable=None, 
                                        report_category=None, plot_type='Rectangular Plot', context=None, subdesign_id=None, polyline_points=1001, plot_name="inductance data")
        

        result_expressions = []
        result_expressions.append(f"dB(St(Tx_port_T1,Tx_port_T1))")
        result_expressions.append(f"dB(St(Rx_port_T1,Rx_port_T1))")
        result_expressions.append(f"dB(St(Tx_port_T1,Rx_port_T1))")

        report6 = self.design.post.create_report(expressions=result_expressions, setup_sweep_name=None, domain='Sweep', 
                                        variations=None, primary_sweep_variable=None, secondary_sweep_variable=None, 
                                        report_category=None, plot_type='Rectangular Plot', context=None, subdesign_id=None, polyline_points=1001, plot_name="return loss data")



        # project_dir = os.path.join(self.project.GetPath(), self.project.GetName())
        project_dir = self.project.GetPath()
        self.project_path = project_dir

        sim_data1 = self.design.post.export_report_to_csv(project_dir=project_dir, plot_name=report1.plot_name, uniform=False, start=None, end=None, step=None, use_trace_number_format=False)
        sim_data2 = self.design.post.export_report_to_csv(project_dir=project_dir, plot_name=report2.plot_name, uniform=False, start=None, end=None, step=None, use_trace_number_format=False)
        sim_data3 = self.design.post.export_report_to_csv(project_dir=project_dir, plot_name=report3.plot_name, uniform=False, start=None, end=None, step=None, use_trace_number_format=False)
        sim_data4 = self.design.post.export_report_to_csv(project_dir=project_dir, plot_name=report4.plot_name, uniform=False, start=None, end=None, step=None, use_trace_number_format=False)
        sim_data5 = self.design.post.export_report_to_csv(project_dir=project_dir, plot_name=report5.plot_name, uniform=False, start=None, end=None, step=None, use_trace_number_format=False)
        sim_data6 = self.design.post.export_report_to_csv(project_dir=project_dir, plot_name=report6.plot_name, uniform=False, start=None, end=None, step=None, use_trace_number_format=False)

        data1 = pd.read_csv(sim_data1)
        data2 = pd.read_csv(sim_data2)
        data3 = pd.read_csv(sim_data3)
        data4 = pd.read_csv(sim_data4)
        data5 = pd.read_csv(sim_data5)
        data6 = pd.read_csv(sim_data6)

        self.data1 = self.design.post_processing.data_preprocessing(data1)
        self.data2 = self.design.post_processing.data_preprocessing(data2)
        self.data3 = self.design.post_processing.data_preprocessing(data3)
        self.data4 = self.design.post_processing.data_preprocessing(data4)
        self.data5 = self.design.post_processing.data_preprocessing(data5)
        self.data6 = self.design.post_processing.data_preprocessing(data6)



        
        data1_freq = data1["Freq [Hz]"]
        data1_ZTT = data1["mag(Zt(Tx_port_T1,Tx_port_T1)) []"]
        data1_ZRR = data1["mag(Zt(Rx_port_T1,Rx_port_T1)) []"]
        data1_ZTR = data1["mag(Zt(Tx_port_T1,Rx_port_T1)) []"]

        data2_freq = data2["Freq [Hz]"]
        data2_RTT = data2["re(Zt(Tx_port_T1,Tx_port_T1)) []"]
        data2_RRR = data2["re(Zt(Rx_port_T1,Rx_port_T1)) []"]
        data2_RTR = data2["re(Zt(Tx_port_T1,Rx_port_T1)) []"]

        data3_freq = data3["Freq [Hz]"]
        data3_ZTT = data3["im(Zt(Tx_port_T1,Tx_port_T1)) []"]
        data3_ZRR = data3["im(Zt(Rx_port_T1,Rx_port_T1)) []"]
        data3_ZTR = data3["im(Zt(Tx_port_T1,Rx_port_T1)) []"]
        data3_k = data3["im(Zt(Tx_port_T1,Rx_port_T1))/sqrt(im(Zt(Tx_port_T1,Tx_port_T1))*im(Zt(Rx_port_T1,Rx_port_T1))) []"]

        data4_freq = data4["Freq [Hz]"]
        data4_voltate_ratio = data4["sqrt( im(Zt(Tx_port_T1,Tx_port_T1)) / im(Zt(Rx_port_T1,Rx_port_T1)) ) []"]

        data5_freq = data5["Freq [Hz]"]
        data5_LTT = data5["im(Zt(Tx_port_T1,Tx_port_T1))/2/pi/freq []"]
        data5_LRR = data5["im(Zt(Rx_port_T1,Rx_port_T1))/2/pi/freq []"]
        data5_LTR = data5["im(Zt(Tx_port_T1,Rx_port_T1))/2/pi/freq []"]
        

        data6_freq = data6["Freq [Hz]"]
        data6_S11 = data6["dB(St(Tx_port_T1,Tx_port_T1)) []"]
        data6_S22 = data6["dB(St(Rx_port_T1,Rx_port_T1)) []"]
        data6_S12 = data6["dB(St(Tx_port_T1,Rx_port_T1)) []"]



        # get ratio data

        ratio_10k = self.design.post_processing.get_frequency_data(10e+3, data4_freq, data4_voltate_ratio) 
        ratio_100k = self.design.post_processing.get_frequency_data(100e+3, data4_freq, data4_voltate_ratio) 
        ratio_1M = self.design.post_processing.get_frequency_data(1e+6, data4_freq, data4_voltate_ratio) 
        ratio_10M = self.design.post_processing.get_frequency_data(10e+6, data4_freq, data4_voltate_ratio) 
        ratio_100M = self.design.post_processing.get_frequency_data(100e+6, data4_freq, data4_voltate_ratio) 

        columns = ['ratio_10k', 'ratio_100k', 'ratio_1M', 'ratio_10M', 'ratio_100M']
        self.voltage_ratio_raw = [ratio_10k, ratio_100k, ratio_1M, ratio_10M, ratio_100M]
        self.voltage_ratio = pd.DataFrame([self.voltage_ratio_raw], columns=columns)

        # get resistance data

        RT_10k = self.design.post_processing.get_frequency_data(10e+3, data2_freq, data2_RTT)
        RT_100k = self.design.post_processing.get_frequency_data(100e+3, data2_freq, data2_RTT)
        RT_1M = self.design.post_processing.get_frequency_data(1e+6, data2_freq, data2_RTT)
        RT_10M = self.design.post_processing.get_frequency_data(10e+6, data2_freq, data2_RTT)
        RT_100M = self.design.post_processing.get_frequency_data(100e+6, data2_freq, data2_RTT)

        RR_10k = self.design.post_processing.get_frequency_data(10e+3, data2_freq, data2_RRR)
        RR_100k = self.design.post_processing.get_frequency_data(100e+3, data2_freq, data2_RRR)
        RR_1M = self.design.post_processing.get_frequency_data(1e+6, data2_freq, data2_RTR)
        RR_10M = self.design.post_processing.get_frequency_data(10e+6, data2_freq, data2_RRR)
        RR_100M = self.design.post_processing.get_frequency_data(100e+6, data2_freq, data2_RRR)

        columns = ['RT_10k', 'RT_100k', 'RT_1M', 'RT_10M', 'RT_100M', 'RR_10k', 'RR_100k', 'RR_1M', 'RR_10M', 'RR_100M']
        self.R_raw = [RT_10k, RT_100k, RT_1M, RT_10M, RT_100M, RR_10k, RR_100k, RR_1M, RR_10M, RR_100M]
        self.R = pd.DataFrame([self.R_raw], columns=columns)

        # get inductance data

        LT_10k = self.design.post_processing.get_frequency_data(10e+3, data5_freq, data5_LTT) * 1e+6
        LT_100k = self.design.post_processing.get_frequency_data(100e+3, data5_freq, data5_LTT) * 1e+6
        LT_1M = self.design.post_processing.get_frequency_data(1e+6, data5_freq, data5_LTT) * 1e+6
        LT_10M = self.design.post_processing.get_frequency_data(10e+6, data5_freq, data5_LTT) * 1e+6
        LT_100M = self.design.post_processing.get_frequency_data(100e+6, data5_freq, data5_LTT) * 1e+6

        LR_10k = self.design.post_processing.get_frequency_data(10e+3, data5_freq, data5_LRR) * 1e+6
        LR_100k = self.design.post_processing.get_frequency_data(100e+3, data5_freq, data5_LRR) * 1e+6
        LR_1M = self.design.post_processing.get_frequency_data(1e+6, data5_freq, data5_LRR) * 1e+6
        LR_10M = self.design.post_processing.get_frequency_data(10e+6, data5_freq, data5_LRR) * 1e+6
        LR_100M = self.design.post_processing.get_frequency_data(100e+6, data5_freq, data5_LRR) * 1e+6

        LM_10k = self.design.post_processing.get_frequency_data(10e+3, data5_freq, data5_LTR) * 1e+6
        LM_100k = self.design.post_processing.get_frequency_data(100e+3, data5_freq, data5_LTR) * 1e+6
        LM_1M = self.design.post_processing.get_frequency_data(1e+6, data5_freq, data5_LTR) * 1e+6
        LM_10M = self.design.post_processing.get_frequency_data(10e+6, data5_freq, data5_LTR) * 1e+6
        LM_100M = self.design.post_processing.get_frequency_data(100e+6, data5_freq, data5_LTR) * 1e+6

        k_10k = abs(self.design.post_processing.get_frequency_data(10e+3, data5_freq, data3_k))
        k_100k = abs(self.design.post_processing.get_frequency_data(100e+3, data5_freq, data3_k))
        k_1M = abs(self.design.post_processing.get_frequency_data(1e+6, data5_freq, data3_k))
        k_10M = abs(self.design.post_processing.get_frequency_data(10e+6, data5_freq, data3_k))
        k_100M = abs(self.design.post_processing.get_frequency_data(100e+6, data5_freq, data3_k))

        columns = ['LT_10k', 'LT_100k', 'LT_1M', 'LT_10M', 'LT_100M', 'LR_10k', 'LR_100k', 'LR_1M', 'LR_10M', 'LR_100M', 
                   'LM_10k', 'LM_100k', 'LM_1M', 'LM_10M', 'LM_100M', 'k_10k', 'k_100k', 'k_1M', 'k_10M', 'k_100M']
        self.L_raw = [LT_10k, LT_100k, LT_1M, LT_10M, LT_100M, LR_10k, LR_100k, LR_1M, LR_10M, LR_100M, LM_10k, LM_100k, LM_1M, LM_10M, LM_100M, k_10k, k_100k, k_1M, k_10M, k_100M]
        self.L = pd.DataFrame([self.L_raw], columns=columns)

        # detect peak impedance

        freq1, peak1 = self.design.post_processing.detect_peak(freq=data1_freq, data=data1_ZTT)
        freq2, peak2 = self.design.post_processing.detect_peak(freq=data1_freq, data=data1_ZRR)
        freq3, peak3 = self.design.post_processing.detect_peak(freq=data1_freq, data=data1_ZTR)

        columns = ['TT_resonant_freq', 'TT_resonant_Z', 'RR_resonant_freq', 'RR_resonant_Z', 'TR_resonant_freq', 'TR_resonant_Z']
        self.resonant_raw = [freq1, peak1, freq2, peak2, freq3, peak3]
        self.resonant = pd.DataFrame([self.resonant_raw], columns=columns)

        # detect zero crossing
        freq_zero1 = self.design.post_processing.detect_zero_crossing(freq=data3_freq, data=data3_ZTT)
        freq_zero2 = self.design.post_processing.detect_zero_crossing(freq=data3_freq, data=data3_ZRR)
        freq_zero3 = self.design.post_processing.detect_zero_crossing(freq=data3_freq, data=data3_ZTR)

        columns = ['TT_zero_freq', 'RR_zero_freq', 'TR_zero_freq']
        self.zero_raw = [freq_zero1, freq_zero2, freq_zero3]
        self.zero = pd.DataFrame([self.zero_raw], columns=columns)

        # detect resonance

        self.freq1 = freq1
        self.freq2 = freq2
        self.freq3 = freq3

        self.peak1 = peak1
        self.peak2 = peak2
        self.peak3 = peak3

        self.freq_zero1 = freq_zero1
        self.freq_zero2 = freq_zero2
        self.freq_zero3 = freq_zero3

        freq1, peak1 = self.design.post_processing.detect_resonant(freq=freq1, peak=peak1, freq_zero=freq_zero1, tolerance=5)
        freq2, peak2 = self.design.post_processing.detect_resonant(freq=freq2, peak=peak2, freq_zero=freq_zero2, tolerance=5)
        freq3, peak3 = self.design.post_processing.detect_resonant(freq=freq3, peak=peak3, freq_zero=freq_zero3, tolerance=5)

        columns = ['TT_resonant_freq_final', 'RR_resonant_freq_final', 'TR_resonant_freq_final']
        self.resonant_final_raw = [[int(x) for x in freq1], [int(x) for x in freq2], [int(x) for x in freq3]]
        self.resonant_final = pd.DataFrame([self.resonant_final_raw], columns=columns)


        # detect S-parameter peak

        freq1, peak1 = self.detect_Speak(freq=data6_freq, data=data6_S11)
        freq2, peak2 = self.detect_Speak(freq=data6_freq, data=data6_S22)
        freq3, peak3 = self.detect_Speak(freq=data6_freq, data=data6_S12)

        columns = ['S11_peak_freq', 'S11_peak_value', 'S22_peak_freq', 'S22_peak_value', 'S12_peak_freq', 'S12_peak_value']
        self.S_final_raw = [[int(x) for x in freq1], [round(abs(float(x)), 2) for x in peak1], [int(x) for x in freq2], [round(abs(float(x)), 2) for x in peak2], [int(x) for x in freq3], [round(abs(float(x)), 2) for x in peak3]]
        self.S_final = pd.DataFrame([self.S_final_raw], columns=columns)



        # get S-parameter value

        S11_10M = -self.design.post_processing.get_frequency_data(10e+6, data6_freq, data6_S11)
        S11_15M = -self.design.post_processing.get_frequency_data(15e+6, data6_freq, data6_S11)
        S11_20M = -self.design.post_processing.get_frequency_data(20e+6, data6_freq, data6_S11)
        S11_25M = -self.design.post_processing.get_frequency_data(25e+6, data6_freq, data6_S11)
        S11_30M = -self.design.post_processing.get_frequency_data(30e+6, data6_freq, data6_S11)
        S11_40M = -self.design.post_processing.get_frequency_data(40e+6, data6_freq, data6_S11)
        S11_50M = -self.design.post_processing.get_frequency_data(50e+6, data6_freq, data6_S11)

        S22_10M = -self.design.post_processing.get_frequency_data(10e+6, data6_freq, data6_S22)
        S22_15M = -self.design.post_processing.get_frequency_data(15e+6, data6_freq, data6_S22)
        S22_20M = -self.design.post_processing.get_frequency_data(20e+6, data6_freq, data6_S22)
        S22_25M = -self.design.post_processing.get_frequency_data(25e+6, data6_freq, data6_S22)
        S22_30M = -self.design.post_processing.get_frequency_data(30e+6, data6_freq, data6_S22)
        S22_40M = -self.design.post_processing.get_frequency_data(40e+6, data6_freq, data6_S22)
        S22_50M = -self.design.post_processing.get_frequency_data(50e+6, data6_freq, data6_S22)

        S12_10M = -self.design.post_processing.get_frequency_data(10e+6, data6_freq, data6_S12)
        S12_15M = -self.design.post_processing.get_frequency_data(15e+6, data6_freq, data6_S12)
        S12_20M = -self.design.post_processing.get_frequency_data(20e+6, data6_freq, data6_S12)
        S12_25M = -self.design.post_processing.get_frequency_data(25e+6, data6_freq, data6_S12)
        S12_30M = -self.design.post_processing.get_frequency_data(30e+6, data6_freq, data6_S12)
        S12_40M = -self.design.post_processing.get_frequency_data(40e+6, data6_freq, data6_S12)
        S12_50M = -self.design.post_processing.get_frequency_data(50e+6, data6_freq, data6_S12)

        columns = ['S11_10M', 'S11_15M', 'S11_20M', 'S11_25M', 'S11_30M', 'S11_40M', 'S11_50M',
                   'S22_10M', 'S22_15M', 'S22_20M', 'S22_25M', 'S22_30M', 'S22_40M', 'S22_50M',
                   'S12_10M', 'S12_15M', 'S12_20M', 'S12_25M', 'S12_30M', 'S12_40M', 'S12_50M']
        self.S_raw = [S11_10M, S11_15M, S11_20M, S11_25M, S11_30M, S11_40M, S11_50M,
                      S22_10M, S22_15M, S22_20M, S22_25M, S22_30M, S22_40M, S22_50M,
                      S12_10M, S12_15M, S12_20M, S12_25M, S12_30M, S12_40M, S12_50M]
        self.S = pd.DataFrame([self.S_raw], columns=columns)






        # get report data

        pass_number, tetrahedra, delta_S = self.design.get_report_data(setup=setup.name)

        end_time = time.time()
        execution_time = int(end_time - self.start_time)

        columns = ['time', 'pass_number', 'tetrahedra', 'delta_S']
        self.sim_result_raw = [execution_time, pass_number, tetrahedra, delta_S]
        self.sim_result = pd.DataFrame([self.sim_result_raw], columns=columns)


        print("manual log : circuit start")

        self.circuit = self.project.create_design(name="circuit_design", solver="Circuit", solution=None)

        print("manual log : circuit complete")

        # ─── 3) COM ModelManager 에 넘길 파라미터 리스트 구성 ────────────────────────────

        image_file = os.path.join(os.getcwd(), "image.gif")

        self.project.CopyDesign(self.design.name)

        ModTime = int(time.time())

        proj         = self.circuit._oproject
        def_mgr      = proj.GetDefinitionManager()
        model_mgr    = def_mgr.GetManager("Model")
        params = [
            "NAME:Link_model",
            "Name:=",               "Link_model",
            "ModTime:=",            ModTime,
            "Library:=",            "",
            "LibLocation:=",        "Project",
            "ModelType:=",          "hfss",
            "Description:=",        "",
            "ImageFile:=",          image_file,
            "SymbolPinConfiguration:=", 0,
            ["NAME:PortInfoBlk"],
            ["NAME:PortOrderBlk"],
            "DesignName:=",         "HFSS_design",
            "SolutionName:=",       "Setup1 : Sweep",
            "NewToOldMap:=",        [],              # **필수**
            "OldToNewMap:=",        [],              # **필수**
            "PinNames:=",           ["Rx_port_T1", "Tx_port_T1"],
            ["NAME:DesignerCustomization",
                "DCOption:=",       0,
                "InterpOption:=",   0,
                "ExtrapOption:=",   1,
                "Convolution:=",    0,
                "Passivity:=",      0,
                "Reciprocal:=",     False,
                "ModelOption:=",    "",
                "DataType:=",       1
            ],
            ["NAME:NexximCustomization",
                "DCOption:=",       3,
                "InterpOption:=",   1,
                "ExtrapOption:=",   3,
                "Convolution:=",    0,
                "Passivity:=",      0,
                "Reciprocal:=",     False,
                "ModelOption:=",    "",
                "DataType:=",       2
            ],
            ["NAME:HSpiceCustomization",
                "DCOption:=",       1,
                "InterpOption:=",   2,
                "ExtrapOption:=",   3,
                "Convolution:=",    0,
                "Passivity:=",      0,
                "Reciprocal:=",     False,
                "ModelOption:=",    "",
                "DataType:=",       3
            ],
            "NoiseModelOption:=",    "External",
            "WB_SystemID:=",         "HFSS_design",
            "IsWBModel:=",           False,
            "filename:=",            "",
            "numberofports:=",       2,
            "Simulate:=",            False,
            "CloseProject:=",        False,
            "SaveProject:=",         True,
            "InterpY:=",             True,
            "InterpAlg:=",           "auto",
            "IgnoreDepVars:=",       False,
            "Renormalize:=",         False,
            "RenormImpedance:=",     50
        ]


        # ─── 4) HFSS 링크 모델 추가 및 저장 ────────────────────────────────────────────
        model_mgr.Add(params)







        # ====================================================
        comp_mgr = def_mgr.GetManager("Component")

        params_comp = [
            "NAME:Link_model",
            "Info:="   , [
                "Type:=",         8,
                "NumTerminals:=", 2,
                "DataSource:=",   "",
                "ModifiedOn:=",   ModTime,
                "Manufacturer:=", "",
                "Symbol:=",       "",      # VBScript 기록과 동일하게 빈 문자열
                "ModelNames:=",   "",      # 역시 빈 문자열
                "Footprint:=",    "",
                "Description:=",  "",
                "InfoTopic:=",    "",
                "InfoHelpFile:=", "",
                "IconFile:=",     "hfss.bmp",
                "Library:=",      "",
                "OriginalLocation:=", "Project",
                "IEEE:=",         "",
                "Author:=",       "",
                "OriginalAuthor:=", "",
                "CreationDate:=", ModTime,
                "ExampleFile:=",  "",
                "HiddenComponent:=", 0,
                "CircuitEnv:=",       0,
                "GroupID:=",          0
            ],
            "CircuitEnv:=", 0,
            "Refbase:=",    "S",
            "NumParts:=",   1,
            "ModSinceLib:=", False,
            # 터미널: VBScript 기록과 동일한 인덱스(0,1)
            "Terminal:=", ["Rx_port_T1","Rx_port_T1","A",False,0,1,"","Electrical","0"],
            "Terminal:=", ["Tx_port_T1","Tx_port_T1","A",False,1,1,"","Electrical","0"],
            ["NAME:Properties",
                "TextProp:=", ["Owner","RD","","HFSS"]
            ],
            "CompExtID:=", 5,
            # Parameters 블록: **모든** VariableProp + TextProp + MenuProp + ButtonProp
            ["NAME:Parameters",
                # -- 16개의 VariableProp (예시로 몇 개만 넣고, 나머지도 동일 패턴) --
                "VariableProp:=", ["Tx_turns","D","",f'{self.Tx_turns}'],
                "VariableProp:=", ["Rx_turns","D","",f'{self.Rx_turns}'],
                "VariableProp:=", ["Tx_outer_x","D","",f'{self.Tx_outer_x}mm'],
                "VariableProp:=", ["Tx_outer_y","HD","",f'{self.Tx_ratio}*{self.Tx_outer_x}mm'],
                "VariableProp:=", ["Rx_outer_x","D","",f'{self.Rx_outer_x}mm'],
                "VariableProp:=", ["Rx_outer_y","HD","",f'{self.Rx_ratio}*{self.Rx_outer_x}mm'],
                "VariableProp:=", ["Tx_inner","D","",f'{self.Tx_inner}mm'],
                "VariableProp:=", ["Rx_inner","D","",f'{self.Rx_inner}mm'],
                "VariableProp:=", ["Tx_fillet","D","",f'{self.Tx_fillet}mm'],
                "VariableProp:=", ["Rx_fillet","D","",f'{self.Rx_fillet}mm'],
                "VariableProp:=", ["Tx_fill_factor","D","",f'{self.Tx_fill_factor}'],
                "VariableProp:=", ["Rx_fill_factor","D","",f'{self.Rx_fill_factor}'],
                "VariableProp:=", ["Tx_theta1","HD","","15*pi/180"],
                "VariableProp:=", ["Tx_theta2","HD","","75*pi/180"],
                "VariableProp:=", ["Rx_theta1","HD","","15*pi/180"],
                "VariableProp:=", ["Rx_theta2","HD","","75*pi/180"],
                "TextProp:=",     ["ModelName","RD","","FieldSolver"],
                "MenuProp:=",     ["CoSimulator","SD","","Default",0],
                "ButtonProp:=",   ["CosimDefinition","SD","","Edit","Edit",40501,
                                    "ButtonPropClientData:=", []]
            ],
            # CosimDefinitions: recorded 값 그대로
            ["NAME:CosimDefinitions",
                ["NAME:CosimDefinition",
                    "CosimulatorType:=",       103,
                    "CosimDefName:=",          "Default",
                    "IsDefinition:=",          True,
                    "Connect:=",               True,
                    "ModelDefinitionName:="	, "Link_model",
                    "ShowRefPin2:="		, 2,
                    "LenPropName:="		, ""
                ],
                "DefaultCosim:=",            "Default"
            ]
        ]

        comp_mgr.Add(params_comp)


        oDesign = self.project.SetActiveDesign("circuit_design")
        oDesign.AddCompInstance("Link_model")

        print("manual log : link model")


        oModule = oDesign.GetModule("SimSetup")
        oModule.AddLinearNetworkAnalysis(
            [
                "NAME:SimSetup",
                "DataBlockID:="		, 16,
                "OptionName:="		, "(Default Options)",
                "AdditionalOptions:="	, "",
                "AlterBlockName:="	, "",
                "FilterText:="		, "",
                "AnalysisEnabled:="	, 1,
                "HasTDRComp:="		, 0,
                [
                    "NAME:OutputQuantities"
                ],
                [
                    "NAME:NoiseOutputQuantities"
                ],
                "Name:="		, "LinearFrequency",
                "LinearFrequencyData:="	, [False,0.1,False,"",False],
                [
                    "NAME:SweepDefinition",
                    "Variable:="		, "Freq",
                    "Data:="		, "10MHz",
                    "OffsetF1:="		, False,
                    "Synchronize:="		, 0
                ]
            ])

        oEditor = oDesign.SetActiveEditor("SchematicEditor")

        oEditor.CreateIPort(
            [
                "NAME:IPortProps",
                "Name:="		, "Port1",
                "Id:="			, 3
            ], 
            [
                "NAME:Attributes",
                "Page:="		, 1,
                "X:="			, 0.0127,
                "Y:="			, 0.0127,
                "Angle:="		, 0,
                "Flip:="		, False
            ])
        oDesign.UpdateSources(
            [
                "NAME:NexximSources",
                [
                    "NAME:NexximSources",
                    [
                        "NAME:Data"
                    ]
                ]
            ], 
            [
                "NAME:ComponentConfigurationData",
                [
                    "NAME:ComponentConfigurationData",
                    [
                        "NAME:EnabledPorts"
                    ],
                    [
                        "NAME:EnabledMultipleComponents"
                    ],
                    [
                        "NAME:EnabledAnalyses",
                        [
                            "NAME:Port1",
                            "Port1:="		, ["LinearFrequency"]
                        ]
                    ]
                ]
            ])
        oDesign.ChangePortProperty("Port1", 
            [
                "NAME:Port1",
                "IIPortName:="		, "Port1",
                "SymbolType:="		, 1,
                "DoPostProcess:="	, False
            ], 
            [
                [
                    "NAME:Properties",
                    [
                        "NAME:ChangedProps",
                        [
                            "NAME:rz",
                            "Value:="		, "50ohm"
                        ],
                        [
                            "NAME:iz",
                            "Value:="		, "0ohm"
                        ],
                        [
                            "NAME:pnum",
                            "Value:="		, "1"
                        ],
                        [
                            "NAME:EnableNoise",
                            "Value:="		, False
                        ],
                        [
                            "NAME:noisetemp",
                            "Value:="		, "16.85cel"
                        ]
                    ]
                ]
            ])

        oDesign.UpdateSources(
            [
                "NAME:NexximSources",
                [
                    "NAME:NexximSources",
                    [
                        "NAME:Data",
                        [
                            "NAME:VoltageSinusoidal1",
                            "DataId:="		, "Source0",
                            "Type:="		, 1,
                            "Output:="		, 0,
                            "NumPins:="		, 2,
                            "Netlist:="		, "V@ID %0 %1 *DC(DC=@DC) SIN(?VO(@VO) ?VA(@VA) ?FREQ(@FREQ) ?TD(@TD) ?ALPHA(@ALPHA) ?THETA(@THETA)) *TONE(TONE=@TONE) *ACMAG(AC @ACMAG @ACPHASE)",
                            "CompName:="		, "Nexxim Circuit Elements\\Independent Sources:V_SIN",
                            "FDSFileName:="		, "",
                            "BtnPropFileName:="	, "",
                            [
                                "NAME:Properties",
                                "TextProp:="		, ["LabelID","HD","Property string for netlist ID","V@ID"],
                                "ValueProp:="		, ["ACMAG","OD","AC magnitude for small-signal analysis (Volts)","3.1*sqrt(2) V",0],
                                "ValuePropNU:="		, ["ACPHASE","D","AC phase for small-signal analysis","0deg",0,"deg",							"AdditionalPropInfo:="	, ""],
                                "ValueProp:="		, ["DC","D","DC voltage (Volts)","0V",0],
                                "ValueProp:="		, ["VO","D","Voltage offset from zero (Volts)","0V",0],
                                "ValueProp:="		, ["VA","D","Voltage amplitude (Volts)","0V",0],
                                "ValueProp:="		, ["FREQ","OD","Frequency (Hz)","10MHz",0],
                                "ValueProp:="		, ["TD","D","Delay to start of sine wave (seconds)","0s",0],
                                "ValueProp:="		, ["ALPHA","D","Damping factor (1/seconds)","0",0],
                                "ValuePropNU:="		, ["THETA","D","Phase delay","0deg",0,"deg",							"AdditionalPropInfo:="	, ""],
                                "ValueProp:="		, ["TONE","D","Frequency (Hz) to use for harmonic balance analysis, should be a submultiple of (or equal to) the driving frequency and should also be included in the HB analysis setup","0Hz",0],
                                "TextProp:="		, ["ModelName","SHD","","V_SIN"],
                                "ButtonProp:="		, ["CosimDefinition","D","","Edit","Edit",40501,							"ButtonPropClientData:=", []],
                                "MenuProp:="		, ["CoSimulator","D","","DefaultNetlist",0]
                            ]
                        ]
                    ]
                ]
            ], 
            [
                "NAME:ComponentConfigurationData",
                [
                    "NAME:ComponentConfigurationData",
                    [
                        "NAME:EnabledPorts",
                        "VoltageSinusoidal1:="	, ["Port1"]
                    ],
                    [
                        "NAME:EnabledMultipleComponents",
                        "VoltageSinusoidal1:="	, []
                    ],
                    [
                        "NAME:EnabledAnalyses",
                        [
                            "NAME:Port1",
                            "Port1:="		, ["LinearFrequency"]
                        ],
                        [
                            "NAME:VoltageSinusoidal1",
                            "Port1:="		, ["LinearFrequency"]
                        ]
                    ]
                ]
            ])
        oDesign.ChangePortProperty("Port1", 
            [
                "NAME:Port1",
                "IIPortName:="		, "Port1",
                "SymbolType:="		, 1,
                "DoPostProcess:="	, False
            ], 
            [
                [
                    "NAME:Properties",
                    [
                        "NAME:ChangedProps",
                        [
                            "NAME:rz",
                            "Value:="		, "1e-06ohm"
                        ],
                        [
                            "NAME:iz",
                            "Value:="		, "0ohm"
                        ],
                        [
                            "NAME:pnum",
                            "Value:="		, "1"
                        ],
                        [
                            "NAME:EnableNoise",
                            "Value:="		, False
                        ],
                        [
                            "NAME:noisetemp",
                            "Value:="		, "16.85cel"
                        ]
                    ]
                ]
            ])
        oEditor.CreateComponent(
            [
                "NAME:ComponentProps",
                "Name:="		, "Nexxim Circuit Elements\\Probes:IPROBE",
                "Id:="			, "23"
            ], 
            [
                "NAME:Attributes",
                "Page:="		, 1,
                "X:="			, 0.01524,
                "Y:="			, 0.00254,
                "Angle:="		, 0,
                "Flip:="		, False
            ])
        oEditor.Move(
            [
                "NAME:Selections",
                "Selections:="		, ["CompInst@IPROBE;23;12"]
            ], 
            [
                "NAME:MoveParameters",
                "xdelta:="		, -0.00254,
                "ydelta:="		, 0.00254,
                "Disconnect:="		, False,
                "Rubberband:="		, False
            ])
        oEditor.Rotate(
            [
                "NAME:Selections",
                "Selections:="		, ["CompInst@IPROBE;23;12"]
            ], 
            [
                "NAME:RotateParameters",
                "Degrees:="		, 90,
                "Disconnect:="		, False,
                "Rubberband:="		, False
            ])
        oEditor.Rotate(
            [
                "NAME:Selections",
                "Selections:="		, ["CompInst@IPROBE;23;12"]
            ], 
            [
                "NAME:RotateParameters",
                "Degrees:="		, 90,
                "Disconnect:="		, False,
                "Rubberband:="		, False
            ])
        oEditor.Rotate(
            [
                "NAME:Selections",
                "Selections:="		, ["CompInst@IPROBE;23;12"]
            ], 
            [
                "NAME:RotateParameters",
                "Degrees:="		, 90,
                "Disconnect:="		, False,
                "Rubberband:="		, False
            ])
        oEditor.ChangeProperty(
            [
                "NAME:AllTabs",
                [
                    "NAME:PassedParameterTab",
                    [
                        "NAME:PropServers", 
                        "CompInst@IPROBE;23;12:1"
                    ],
                    [
                        "NAME:ChangedProps",
                        [
                            "NAME:Name",
                            "Value:="		, "Iin"
                        ]
                    ]
                ]
            ])
        oEditor.CreateComponent(
            [
                "NAME:ComponentProps",
                "Name:="		, "Nexxim Circuit Elements\\Probes:IPROBE",
                "Id:="			, "24"
            ], 
            [
                "NAME:Attributes",
                "Page:="		, 1,
                "X:="			, -0.03302,
                "Y:="			, -0.00254,
                "Angle:="		, 0,
                "Flip:="		, False
            ])
        oEditor.Rotate(
            [
                "NAME:Selections",
                "Selections:="		, ["CompInst@IPROBE;24;19"]
            ], 
            [
                "NAME:RotateParameters",
                "Degrees:="		, 90,
                "Disconnect:="		, False,
                "Rubberband:="		, False
            ])
        oEditor.Rotate(
            [
                "NAME:Selections",
                "Selections:="		, ["CompInst@IPROBE;24;19"]
            ], 
            [
                "NAME:RotateParameters",
                "Degrees:="		, 90,
                "Disconnect:="		, False,
                "Rubberband:="		, False
            ])
        oEditor.ChangeProperty(
            [
                "NAME:AllTabs",
                [
                    "NAME:PassedParameterTab",
                    [
                        "NAME:PropServers", 
                        "CompInst@IPROBE;24;19:1"
                    ],
                    [
                        "NAME:ChangedProps",
                        [
                            "NAME:Name",
                            "Value:="		, "Iout"
                        ]
                    ]
                ]
            ])
        oEditor.CreateComponent(
            [
                "NAME:ComponentProps",
                "Name:="		, "Nexxim Circuit Elements\\Resistors:RES_",
                "Id:="			, "25"
            ], 
            [
                "NAME:Attributes",
                "Page:="		, 1,
                "X:="			, -0.0508,
                "Y:="			, -0.00254,
                "Angle:="		, 0,
                "Flip:="		, False
            ])
        oEditor.CreateWire(
            [
                "NAME:WireData",
                "Name:="		, "",
                "Id:="			, 26,
                "Points:="		, ["(-0.045720, -0.002540)","(-0.038100, -0.002540)"]
            ], 
            [
                "NAME:Attributes",
                "Page:="		, 1
            ])
        oEditor.CreateWire(
            [
                "NAME:WireData",
                "Name:="		, "",
                "Id:="			, 32,
                "Points:="		, ["(-0.027940, -0.002540)","(-0.010160, -0.002540)"]
            ], 
            [
                "NAME:Attributes",
                "Page:="		, 1
            ])
        oEditor.CreateWire(
            [
                "NAME:WireData",
                "Name:="		, "",
                "Id:="			, 38,
                "Points:="		, ["(0.000000, -0.002540)","(0.012700, -0.002540)","(0.012700, 0.000000)"]
            ], 
            [
                "NAME:Attributes",
                "Page:="		, 1
            ])
        oEditor.CreateGround(
            [
                "NAME:GroundProps",
                "Id:="			, 44
            ], 
            [
                "NAME:Attributes",
                "Page:="		, 1,
                "X:="			, -0.05588,
                "Y:="			, -0.01778,
                "Angle:="		, 0,
                "Flip:="		, False
            ])
        oEditor.CreateWire(
            [
                "NAME:WireData",
                "Name:="		, "",
                "Id:="			, 48,
                "Points:="		, ["(-0.055880, -0.015240)","(-0.055880, -0.002540)"]
            ], 
            [
                "NAME:Attributes",
                "Page:="		, 1
            ])
        oEditor.ChangeProperty(
            [
                "NAME:AllTabs",
                [
                    "NAME:PassedParameterTab",
                    [
                        "NAME:PropServers", 
                        "CompInst@RES_;25;24:1"
                    ],
                    [
                        "NAME:ChangedProps",
                        [
                            "NAME:R",
                            "Value:="		, "28"
                        ]
                    ]
                ]
            ])
        oEditor.CreateWire(
            [
                "NAME:WireData",
                "Name:="		, "",
                "Id:="			, 53,
                "Points:="		, ["(0.012700, 0.010160)","(0.012700, 0.012700)"]
            ], 
            [
                "NAME:Attributes",
                "Page:="		, 1
            ])
        oEditor.CreateComponent(
            [
                "NAME:ComponentProps",
                "Name:="		, "Nexxim Circuit Elements\\Probes:VPROBE",
                "Id:="			, "26"
            ], 
            [
                "NAME:Attributes",
                "Page:="		, 1,
                "X:="			, 0.0254,
                "Y:="			, -0.00508,
                "Angle:="		, 0,
                "Flip:="		, False
            ])
        oEditor.Move(
            [
                "NAME:Selections",
                "Selections:="		, ["CompInst@VPROBE;26;57"]
            ], 
            [
                "NAME:MoveParameters",
                "xdelta:="		, -0.06604,
                "ydelta:="		, 0.00762,
                "Disconnect:="		, False,
                "Rubberband:="		, False
            ])
        oEditor.ChangeProperty(
            [
                "NAME:AllTabs",
                [
                    "NAME:PassedParameterTab",
                    [
                        "NAME:PropServers", 
                        "CompInst@VPROBE;26;57:1"
                    ],
                    [
                        "NAME:ChangedProps",
                        [
                            "NAME:Name",
                            "Value:="		, "Vout"
                        ]
                    ]
                ]
            ])
        oDesign.Analyze("LinearFrequency")
        oModule = oDesign.GetModule("OutputVariable")
        oModule.CreateOutputVariable("Pin", "0.5*re(V(Port1)*conjg(I(Iin)))", "LinearFrequency", "Standard", 
            [
                "NAME:Context",
                "SimValueContext:="	, [3,0,2,0,False,False,-1,1,0,1,1,"",0,0]
            ])
        oModule.CreateOutputVariable("Pout", "0.5*re(V(Vout)*conjg(I(Iout)))", "LinearFrequency", "Standard", 
            [
                "NAME:Context",
                "SimValueContext:="	, [3,0,2,0,False,False,-1,1,0,1,1,"",0,0]
            ])
        oModule.CreateOutputVariable("Gv", "mag(V(Vout))/mag(V(Port1))", "LinearFrequency", "Standard", 
            [
                "NAME:Context",
                "SimValueContext:="	, [3,0,2,0,False,False,-1,1,0,1,1,"",0,0]
            ])
        oModule.CreateOutputVariable("Eff", "Pout/Pin*100", "LinearFrequency", "Standard", 
            [
                "NAME:Context",
                "SimValueContext:="	, [3,0,2,0,False,False,-1,1,0,1,1,"",0,0]
            ])
        


        oModule = oDesign.GetModule("ReportSetup")
        oModule.CreateReport("Return Loss Table 1", "Standard", "Data Table", "LinearFrequency", 
            [
                "NAME:Context",
                "SimValueContext:="	, [3,0,2,0,False,False,-1,1,0,1,1,"",0,0]
            ], 
            [
                "Freq:="		, ["All"]
            ], 
            [
                "X Component:="		, "Freq",
                "Y Component:="		, ["Pin","Pout","Gv","Eff","mag(V(Port1))","mag(V(Vout))","mag(I(Iin))","mag(I(Iout))"]
            ])



        project_dir = self.project.GetPath()

        sim_data_RL = self.circuit.post.export_report_to_csv(project_dir=project_dir, plot_name="Return Loss Table 1", uniform=False, start=None, end=None, step=None, use_trace_number_format=False)

        data_RL = pd.read_csv(sim_data_RL)
        self.data_RL = self.circuit.post_processing.data_preprocessing(data_RL)

        # 단위 변환 및 컬럼명 변경
        rename_dict = {}
        for col in data_RL.columns:
            if "[mV]" in col:
                data_RL[col] = data_RL[col] / 1000  # mV → V
                new_col = col.replace("[mV]", "[V]")
                rename_dict[col] = new_col
            elif "[mA]" in col:
                data_RL[col] = data_RL[col] / 1000  # mA → A
                new_col = col.replace("[mA]", "[A]")
                rename_dict[col] = new_col

        # 컬럼 이름 일괄 변경
        data_RL.rename(columns=rename_dict, inplace=True)

        data_Pin = round(data_RL["Pin []"].values[0],4)
        data_Pout = round(data_RL["Pout []"].values[0],4)
        data_Gv = round(data_RL["Gv []"].values[0],4)
        data_eff = round(data_RL["Eff []"].values[0],4)
        data_Vin = round(data_RL["mag(V(Port1)) [V]"].values[0],4)
        data_Vload = round(data_RL["mag(V(Vout)) [V]"].values[0],4)
        data_Iin = round(data_RL["mag(I(Iin)) [A]"].values[0],4)
        data_Iload = round(data_RL["mag(I(Iout)) [A]"].values[0],4)

        columns = ['Pin28', 'Pout28', 'Gv28', 'eff28', 'Vin28', 'Vload28', 'Iin28', 'Iload28']
        self.circuit_data_raw = [data_Pin, data_Pout, data_Gv, data_eff, data_Vin, data_Vload, data_Iin, data_Iload]
        self.circuit_data_28 = pd.DataFrame([self.circuit_data_raw], columns=columns)




        oEditor.ChangeProperty(
            [
                "NAME:AllTabs",
                [
                    "NAME:PassedParameterTab",
                    [
                        "NAME:PropServers", 
                        "CompInst@RES_;25;24"
                    ],
                    [
                        "NAME:ChangedProps",
                        [
                            "NAME:R",
                            "Value:="		, "50"
                        ]
                    ]
                ]
            ])
        oDesign.Analyze("LinearFrequency")

        sim_data_RL = self.circuit.post.export_report_to_csv(project_dir=project_dir, plot_name="Return Loss Table 1", uniform=False, start=None, end=None, step=None, use_trace_number_format=False)

        data_RL = pd.read_csv(sim_data_RL)
        self.data_RL = self.circuit.post_processing.data_preprocessing(data_RL)

        # 단위 변환 및 컬럼명 변경
        rename_dict = {}
        for col in data_RL.columns:
            if "[mV]" in col:
                data_RL[col] = data_RL[col] / 1000  # mV → V
                new_col = col.replace("[mV]", "[V]")
                rename_dict[col] = new_col
            elif "[mA]" in col:
                data_RL[col] = data_RL[col] / 1000  # mA → A
                new_col = col.replace("[mA]", "[A]")
                rename_dict[col] = new_col

        # 컬럼 이름 일괄 변경
        data_RL.rename(columns=rename_dict, inplace=True)

        data_Pin = round(data_RL["Pin []"].values[0],4)
        data_Pout = round(data_RL["Pout []"].values[0],4)
        data_Gv = round(data_RL["Gv []"].values[0],4)
        data_eff = round(data_RL["Eff []"].values[0],4)
        data_Vin = round(data_RL["mag(V(Port1)) [V]"].values[0],4)
        data_Vload = round(data_RL["mag(V(Vout)) [V]"].values[0],4)
        data_Iin = round(data_RL["mag(I(Iin)) [A]"].values[0],4)
        data_Iload = round(data_RL["mag(I(Iout)) [A]"].values[0],4)

        columns = ['Pin50', 'Pout50', 'Gv50', 'eff50', 'Vin50', 'Vload50', 'Iin50', 'Iload50']
        self.circuit_data_raw = [data_Pin, data_Pout, data_Gv, data_eff, data_Vin, data_Vload, data_Iin, data_Iload]
        self.circuit_data_50 = pd.DataFrame([self.circuit_data_raw], columns=columns)



        
        oEditor.ChangeProperty(
            [
                "NAME:AllTabs",
                [
                    "NAME:PassedParameterTab",
                    [
                        "NAME:PropServers", 
                        "CompInst@RES_;25;24"
                    ],
                    [
                        "NAME:ChangedProps",
                        [
                            "NAME:R",
                            "Value:="		, "100"
                        ]
                    ]
                ]
            ])
        oDesign.Analyze("LinearFrequency")

        sim_data_RL = self.circuit.post.export_report_to_csv(project_dir=project_dir, plot_name="Return Loss Table 1", uniform=False, start=None, end=None, step=None, use_trace_number_format=False)

        data_RL = pd.read_csv(sim_data_RL)
        self.data_RL = self.circuit.post_processing.data_preprocessing(data_RL)

        # 단위 변환 및 컬럼명 변경
        rename_dict = {}
        for col in data_RL.columns:
            if "[mV]" in col:
                data_RL[col] = data_RL[col] / 1000  # mV → V
                new_col = col.replace("[mV]", "[V]")
                rename_dict[col] = new_col
            elif "[mA]" in col:
                data_RL[col] = data_RL[col] / 1000  # mA → A
                new_col = col.replace("[mA]", "[A]")
                rename_dict[col] = new_col

        # 컬럼 이름 일괄 변경
        data_RL.rename(columns=rename_dict, inplace=True)

        data_Pin = round(data_RL["Pin []"].values[0],4)
        data_Pout = round(data_RL["Pout []"].values[0],4)
        data_Gv = round(data_RL["Gv []"].values[0],4)
        data_eff = round(data_RL["Eff []"].values[0],4)
        data_Vin = round(data_RL["mag(V(Port1)) [V]"].values[0],4)
        data_Vload = round(data_RL["mag(V(Vout)) [V]"].values[0],4)
        data_Iin = round(data_RL["mag(I(Iin)) [A]"].values[0],4)
        data_Iload = round(data_RL["mag(I(Iout)) [A]"].values[0],4)

        columns = ['Pin100', 'Pout100', 'Gv100', 'eff100', 'Vin100', 'Vload100', 'Iin100', 'Iload100']
        self.circuit_data_raw = [data_Pin, data_Pout, data_Gv, data_eff, data_Vin, data_Vload, data_Iin, data_Iload]
        self.circuit_data_100 = pd.DataFrame([self.circuit_data_raw], columns=columns)




        oEditor.ChangeProperty(
            [
                "NAME:AllTabs",
                [
                    "NAME:PassedParameterTab",
                    [
                        "NAME:PropServers", 
                        "CompInst@RES_;25;24"
                    ],
                    [
                        "NAME:ChangedProps",
                        [
                            "NAME:R",
                            "Value:="		, "200"
                        ]
                    ]
                ]
            ])
        oDesign.Analyze("LinearFrequency")

        sim_data_RL = self.circuit.post.export_report_to_csv(project_dir=project_dir, plot_name="Return Loss Table 1", uniform=False, start=None, end=None, step=None, use_trace_number_format=False)

        data_RL = pd.read_csv(sim_data_RL)
        self.data_RL = self.circuit.post_processing.data_preprocessing(data_RL)

        # 단위 변환 및 컬럼명 변경
        rename_dict = {}
        for col in data_RL.columns:
            if "[mV]" in col:
                data_RL[col] = data_RL[col] / 1000  # mV → V
                new_col = col.replace("[mV]", "[V]")
                rename_dict[col] = new_col
            elif "[mA]" in col:
                data_RL[col] = data_RL[col] / 1000  # mA → A
                new_col = col.replace("[mA]", "[A]")
                rename_dict[col] = new_col

        # 컬럼 이름 일괄 변경
        data_RL.rename(columns=rename_dict, inplace=True)

        data_Pin = round(data_RL["Pin []"].values[0],4)
        data_Pout = round(data_RL["Pout []"].values[0],4)
        data_Gv = round(data_RL["Gv []"].values[0],4)
        data_eff = round(data_RL["Eff []"].values[0],4)
        data_Vin = round(data_RL["mag(V(Port1)) [V]"].values[0],4)
        data_Vload = round(data_RL["mag(V(Vout)) [V]"].values[0],4)
        data_Iin = round(data_RL["mag(I(Iin)) [A]"].values[0],4)
        data_Iload = round(data_RL["mag(I(Iout)) [A]"].values[0],4)

        columns = ['Pin200', 'Pout200', 'Gv200', 'eff200', 'Vin200', 'Vload200', 'Iin200', 'Iload200']
        self.circuit_data_raw = [data_Pin, data_Pout, data_Gv, data_eff, data_Vin, data_Vload, data_Iin, data_Iload]
        self.circuit_data_200 = pd.DataFrame([self.circuit_data_raw], columns=columns)



        oEditor.ChangeProperty(
            [
                "NAME:AllTabs",
                [
                    "NAME:PassedParameterTab",
                    [
                        "NAME:PropServers", 
                        "CompInst@RES_;25;24"
                    ],
                    [
                        "NAME:ChangedProps",
                        [
                            "NAME:R",
                            "Value:="		, "1000"
                        ]
                    ]
                ]
            ])
        oDesign.Analyze("LinearFrequency")

        sim_data_RL = self.circuit.post.export_report_to_csv(project_dir=project_dir, plot_name="Return Loss Table 1", uniform=False, start=None, end=None, step=None, use_trace_number_format=False)

        data_RL = pd.read_csv(sim_data_RL)
        self.data_RL = self.circuit.post_processing.data_preprocessing(data_RL)

        # 단위 변환 및 컬럼명 변경
        rename_dict = {}
        for col in data_RL.columns:
            if "[mV]" in col:
                data_RL[col] = data_RL[col] / 1000  # mV → V
                new_col = col.replace("[mV]", "[V]")
                rename_dict[col] = new_col
            elif "[mA]" in col:
                data_RL[col] = data_RL[col] / 1000  # mA → A
                new_col = col.replace("[mA]", "[A]")
                rename_dict[col] = new_col

        # 컬럼 이름 일괄 변경
        data_RL.rename(columns=rename_dict, inplace=True)

        data_Pin = round(data_RL["Pin []"].values[0],4)
        data_Pout = round(data_RL["Pout []"].values[0],4)
        data_Gv = round(data_RL["Gv []"].values[0],4)
        data_eff = round(data_RL["Eff []"].values[0],4)
        data_Vin = round(data_RL["mag(V(Port1)) [V]"].values[0],4)
        data_Vload = round(data_RL["mag(V(Vout)) [V]"].values[0],4)
        data_Iin = round(data_RL["mag(I(Iin)) [A]"].values[0],4)
        data_Iload = round(data_RL["mag(I(Iout)) [A]"].values[0],4)

        columns = ['Pin1000', 'Pout1000', 'Gv1000', 'eff1000', 'Vin1000', 'Vload1000', 'Iin1000', 'Iload1000']
        self.circuit_data_raw = [data_Pin, data_Pout, data_Gv, data_eff, data_Vin, data_Vload, data_Iin, data_Iload]
        self.circuit_data_1000 = pd.DataFrame([self.circuit_data_raw], columns=columns)



        




        # output data
        
        self.output_data = pd.concat([self.input, self.voltage_ratio, self.L, self.R, self.resonant_final, self.S_final, self.S, self.circuit_data_28, self.circuit_data_50, self.circuit_data_100, self.circuit_data_200, self.circuit_data_1000, self.sim_result], axis=1)



        current_dir = os.getcwd()
        csv_file = os.path.join(current_dir, f"output_data_circuit.csv")

        if os.path.isfile(csv_file):
            self.output_data.to_csv(csv_file, mode='a', index=False, header=False)
        else:
            self.output_data.to_csv(csv_file, mode='w', index=False, header=True)


        # self.design.delete_project(self.PROJECT_NAME)


def loging(msg):

    file_path = "log.txt"
    max_attempts = 5
    attempt = 0

    # 파일이 없으면 새로 생성하고, 있으면 append 모드로 엽니다.
    while attempt < max_attempts:
        try:
            with open(file_path, "a", encoding="utf-8") as file:
                file.write(msg + "\n")
            break  # 성공하면 루프 탈출
        except Exception as e:
            attempt += 1
            print(f"파일 쓰기 오류 발생: {e}. 재시도 {attempt}/{max_attempts}...")
            time.sleep(1)
    else:
        print("파일 쓰기에 계속 실패했습니다.")
        




def safe_open(filename, mode, retries=5, delay=1):
    """
    filename: 열 파일명
    mode: 열기 모드 (예: 'r', 'w', 'a')
    retries: 재시도 횟수
    delay: 재시도 전 대기 시간(초)
    """
    for i in range(retries):
        try:
            return open(filename, mode, newline='')
        except (IOError, OSError) as e:
            if i == retries - 1:
                raise e
            time.sleep(delay)


def log_simulation(number, state=None, pid=None, filename='log.csv'):
    """
    number: 기록할 숫자 값
    state: None이면 초기 기록, "fail"이면 Error, 그 외는 Finished로 업데이트
    pid: 기록할 프로세스 아이디 값 (인자로 받음)
    filename: 로그 파일명 (기본 'log.csv')

    파일이 없으면 헤더( Number, Status, StartTime, PID )와 함께 생성한 후,
    초기 호출 시 새로운 레코드를 추가하고, state가 전달되면 기존 레코드의 Status를 업데이트합니다.
    """
    lock_timeout = 10  # 락 타임아웃 시간(초)

    # 파일이 없으면 헤더를 포함하여 생성
    if not os.path.exists(filename):
        with portalocker.Lock(filename, 'w', timeout=lock_timeout, newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['Number', 'Status', 'StartTime', 'PID', 'EndTime'])
    
    # 초기 기록인 경우: state가 None이면 해당 번호의 레코드가 있는지 확인 후 없으면 추가
    if state is None:
        exists = False
        with portalocker.Lock(filename, 'r', timeout=lock_timeout, newline='') as f:
            reader = csv.reader(f)
            for row in reader:
                if row and row[0] == str(number):
                    exists = True
                    break
        if not exists:
            start_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            with portalocker.Lock(filename, 'a', timeout=lock_timeout, newline='') as f:
                writer = csv.writer(f)
                writer.writerow([number, 'Simulation', start_time, pid, ""])
    else:
        # state가 전달된 경우: 기존 레코드의 상태 업데이트
        new_status = "Error" if state.lower() == "fail" else "Finished"
        end_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        with portalocker.Lock(filename, 'r+', timeout=lock_timeout, newline='') as f:
            # 파일의 모든 행을 읽고 리스트로 저장
            rows = list(csv.reader(f))
            updated_rows = []
            for row in rows:
                # 헤더나, 해당 번호의 상태가 "Simulation"인 경우만 업데이트
                if row and row[0] == str(number) and row[1] == "Simulation":
                    row[1] = new_status
                    row[4] = end_time
                updated_rows.append(row)
            # 파일 포인터를 맨 앞으로 돌리고 내용을 덮어씌운 후 파일 내용을 잘라냅니다.
            f.seek(0)
            writer = csv.writer(f)
            writer.writerows(updated_rows)
            f.truncate()




def save_error_log(project_name, error_info):
    error_folder = "error"
    if not os.path.exists(error_folder):
        os.makedirs(error_folder)
    error_file = os.path.join(error_folder, f"{project_name}_error.txt")
    with open(error_file, "w", encoding="utf-8") as f:
        f.write(error_info)



sim1 = Simulation()



for i in range(5000):

    info_handler = logging.FileHandler("info.log")
    info_handler.setLevel(logging.DEBUG)

    try:
        # 시뮬레이션 코드 실행
        sim1.simulation()


        


        pid = sim1.desktop.pid
        sim1.project.close()
        time.sleep(1)
        sim1.project.delete_project_folder(path=sim1.project_path)

        end_time = time.time()
        execution_time = end_time - sim1.start_time

        log_simulation(number=sim1.num, state="finished")
        loging(f"{sim1.PROJECT_NAME} : simulation success!! {i} ({execution_time:.1f} sec)")

    except Exception as e:

        pd.set_option('display.max_rows', None)
        pd.set_option('display.max_columns', None)
        pd.set_option('display.width', None)
        err_info = f"error : {sim1.PROJECT_NAME}\n"
        err_info = f"input : {sim1.input}\n"
        err_info += f"{str(e)}\n"
        err_info += traceback.format_exc()
        # 콘솔 stderr에 출력 및 플러시
        print(err_info, file=sys.stderr)
        
        sys.stderr.flush()
        # logging.error를 통해 simulation.log에도 기록
        logging.error(err_info, exc_info=True)
        # error 폴더에 에러 정보 저장
        save_error_log(sim1.PROJECT_NAME, err_info)
        # log.csv 업데이트 (fail 상태)
        log_simulation(number=sim1.num, state="fail")
        loging(f"{sim1.PROJECT_NAME} : {i} simulation Failed")
        sim1.desktop.kill_process()
        del sim1
        sim1 = Simulation()
        time.sleep(1)
