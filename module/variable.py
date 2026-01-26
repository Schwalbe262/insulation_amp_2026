"""
Variable setting functions for simulation design.
"""

import math
import pandas as pd


def set_variable(simulation, design):
    """
    Set random variables for the simulation design.
    
    Args:
        simulation: Simulation object to store variable values
        design: pyDesign object to set design variables
    """
    # # Tx variables
    # simulation.Tx_outer_x = design.random_variable(variable_name="Tx_outer_x", lower=0.8, upper=2.5, resolution=0.1, unit="mm")
    # simulation.Tx_ratio = design.random_variable(lower=0.4, upper=0.9, resolution=0.01)
    # simulation.Tx_outer_y = simulation.Tx_ratio * simulation.Tx_outer_x

    # Tx_inner_min = 0.4 * min(simulation.Tx_outer_x, simulation.Tx_outer_y)
    # Tx_inner_max = 0.8 * min(simulation.Tx_outer_x, simulation.Tx_outer_y)
    # simulation.Tx_inner = design.random_variable(variable_name="Tx_inner", lower=Tx_inner_min, upper=Tx_inner_max, resolution=0.01, unit="mm")

    # Tx_fillet_min = simulation.Tx_inner * (math.tan(75 * math.pi/180) - 1) / math.tan(75 * math.pi/180) * 1.1
    # Tx_fillet_max = simulation.Tx_inner * 0.8 if simulation.Tx_inner * 0.8 > Tx_fillet_min else simulation.Tx_inner * 0.9
    # simulation.Tx_fillet = design.random_variable(variable_name="Tx_fillet", lower=Tx_fillet_min, upper=Tx_fillet_max, resolution=0.01, unit="mm")

    # simulation.Tx_fill_factor = design.random_variable(variable_name="Tx_fill_factor", lower=0.3, upper=0.8, resolution=0.01, unit="")

    # # Rx variables
    # simulation.Tx_Rx_ratio = design.random_variable(lower=0.6, upper=1.5, resolution=0.01)  # x방향 기준으로 Rx가 Tx보다 몇배 더 큰지 설정
    # simulation.Rx_outer_x = simulation.Tx_outer_x * simulation.Tx_Rx_ratio

    # simulation.Rx_ratio = design.random_variable(lower=0.4, upper=0.9, resolution=0.01)
    # simulation.Rx_outer_y = simulation.Rx_ratio * simulation.Rx_outer_x

    """
    임시변경
    """

    # x 사이즈 제한 5mm
    # y 사이즈 제한 3.5mm

    simulation.Tx_outer_x = design.random_variable(variable_name="Tx_outer_x", lower=1.5, upper=2.5, resolution=0.01, unit="mm")
    simulation.Tx_outer_y = design.random_variable(variable_name="Tx_outer_y", lower=1.2, upper=2.0, resolution=0.01, unit="mm")
    simulation.Rx_outer_x = design.random_variable(variable_name="Rx_outer_x", lower=1.5, upper=2.5, resolution=0.01, unit="mm")
    simulation.Rx_outer_y = design.random_variable(variable_name="Rx_outer_y", lower=1.2, upper=2.0, resolution=0.01, unit="mm")
    simulation.Tx_ratio = simulation.Tx_outer_y / simulation.Tx_outer_x
    simulation.Rx_ratio = simulation.Rx_outer_y / simulation.Rx_outer_x

    Tx_inner_min = 0.4 * min(simulation.Tx_outer_x, simulation.Tx_outer_y)
    Tx_inner_max = 0.8 * min(simulation.Tx_outer_x, simulation.Tx_outer_y)
    simulation.Tx_inner = design.random_variable(variable_name="Tx_inner", lower=Tx_inner_min, upper=Tx_inner_max, resolution=0.01, unit="mm")

    Tx_fillet_min = simulation.Tx_inner * (math.tan(75 * math.pi/180) - 1) / math.tan(75 * math.pi/180) * 1.1
    Tx_fillet_max = simulation.Tx_inner * 0.8 if simulation.Tx_inner * 0.8 > Tx_fillet_min else simulation.Tx_inner * 0.9
    simulation.Tx_fillet = design.random_variable(variable_name="Tx_fillet", lower=Tx_fillet_min, upper=Tx_fillet_max, resolution=0.01, unit="mm")

    simulation.Tx_fill_factor = design.random_variable(variable_name="Tx_fill_factor", lower=0.3, upper=0.8, resolution=0.01, unit="")

    """
    임시변경
    """

    Rx_inner_min = 0.4 * min(simulation.Rx_outer_x, simulation.Rx_outer_y)
    Rx_inner_max = 0.8 * min(simulation.Rx_outer_x, simulation.Rx_outer_y)
    simulation.Rx_inner = design.random_variable(variable_name="Rx_inner", lower=Rx_inner_min, upper=Rx_inner_max, resolution=0.01, unit="mm")

    Rx_fillet_min = simulation.Rx_inner * (math.tan(75 * math.pi/180) - 1) / math.tan(75 * math.pi/180) * 1.1
    Rx_fillet_max = simulation.Rx_inner * 0.8 if simulation.Rx_inner * 0.8 > Rx_fillet_min else simulation.Rx_inner * 0.9
    simulation.Rx_fillet = design.random_variable(variable_name="Rx_fillet", lower=Rx_fillet_min, upper=Rx_fillet_max, resolution=0.01, unit="mm")

    simulation.Rx_fill_factor = design.random_variable(variable_name="Rx_fill_factor", lower=0.3, upper=0.8, resolution=0.01, unit="")

    # Turns and layers
    simulation.Tx_turns = design.random_variable(variable_name=None, lower=5, upper=12, resolution=1)
    simulation.Rx_turns = int(round(simulation.Tx_turns * design.random_variable(variable_name=None, lower=1.2, upper=2.5, resolution=0.01), 0))

    simulation.Tx_layer = design.random_variable(variable_name=None, lower=1, upper=2, resolution=1)
    simulation.Rx_layer = design.random_variable(variable_name=None, lower=2, upper=2, resolution=1)

    # PCB thickness
    thick_ratio = design.random_variable(lower=0.25, upper=1.0, resolution=0.01)  # unit : oz
    simulation.PCB_thickness = 0.035 * thick_ratio  # unit : mm

    # Gaps
    simulation.Tx_Tx_gap = design.random_variable(lower=0.020, upper=0.060, resolution=0.001)  # unit : mm
    simulation.Rx_Rx_gap = design.random_variable(lower=0.020, upper=0.060, resolution=0.001)  # unit : mm
    simulation.Tx_Rx_gap = design.random_variable(lower=0.050, upper=0.200, resolution=0.001)  # unit : mm

    # Set design variables
    design["Tx_turns"] = f"{simulation.Tx_turns}"
    design["Rx_turns"] = f"{simulation.Rx_turns}"
    design["Tx_layer"] = f"{simulation.Tx_layer}"
    design["Rx_layer"] = f"{simulation.Rx_layer}"

    design["Tx_outer_x"] = f"{simulation.Tx_outer_x}mm"
    design["Tx_outer_y"] = f"{simulation.Tx_ratio} * {simulation.Tx_outer_x}mm"
    design["Rx_outer_x"] = f"{simulation.Rx_outer_x}mm"
    design["Rx_outer_y"] = f"{simulation.Rx_ratio} * {simulation.Rx_outer_x}mm"

    design["Tx_inner"] = f"{simulation.Tx_inner}mm"
    design["Rx_inner"] = f"{simulation.Rx_inner}mm"
    design["Tx_fillet"] = f"{simulation.Tx_fillet}mm"
    design["Rx_fillet"] = f"{simulation.Rx_fillet}mm"

    design["Tx_fill_factor"] = f"{simulation.Tx_fill_factor}"
    design["Rx_fill_factor"] = f"{simulation.Rx_fill_factor}"

    design["Tx_theta1"] = "15*pi/180"
    design["Tx_theta2"] = "75*pi/180"
    design["Rx_theta1"] = "15*pi/180"
    design["Rx_theta2"] = "75*pi/180"

    design["PCB_thickness"] = f"{simulation.PCB_thickness}mm"

    design["Tx_Tx_gap"] = f"{simulation.Tx_Tx_gap}mm"
    design["Rx_Rx_gap"] = f"{simulation.Rx_Rx_gap}mm"
    design["Tx_Rx_gap"] = f"{simulation.Tx_Rx_gap}mm"

    # Create input DataFrame
    columns = [
        'Tx_turns', 'Rx_turns', 'Tx_layer', 'Rx_layer', 'Tx_outer_x', 'Tx_outer_y', 'Tx_ratio',
        'Rx_outer_x', 'Rx_outer_y', 'Rx_ratio', 'Tx_inner', 'Rx_inner', 'Tx_fillet', 'Rx_fillet',
        'Tx_fill_factor', 'Rx_fill_factor', 'PCB_thickness', 'Tx_Tx_gap', 'Rx_Rx_gap', 'Tx_Rx_gap',
    ]

    simulation.input_raw = [
        simulation.Tx_turns, simulation.Rx_turns, simulation.Tx_layer, simulation.Rx_layer, simulation.Tx_outer_x, simulation.Tx_outer_y, simulation.Tx_ratio,
        simulation.Rx_outer_x, simulation.Rx_outer_y, simulation.Rx_ratio, simulation.Tx_inner, simulation.Rx_inner, simulation.Tx_fillet, simulation.Rx_fillet,
        simulation.Tx_fill_factor, simulation.Rx_fill_factor, simulation.PCB_thickness, simulation.Tx_Tx_gap, simulation.Rx_Rx_gap, simulation.Tx_Rx_gap
    ]
    
    simulation.input = pd.DataFrame([simulation.input_raw], columns=columns)

    return simulation.input

