import gurobipy as gp
from gurobipy import GRB
import os
import numpy as np
from miplearn.io import write_pkl_gz, read_pkl_gz
from miplearn.solvers.gurobi import GurobiModel
from miplearn.solvers.learning import LearningSolver
from miplearn.collectors.basic import BasicCollector
from dataclasses import dataclass
from typing import List, Union

from sklearn.neighbors import KNeighborsClassifier
from miplearn.components.primal.actions import SetWarmStart
from miplearn.components.primal.mem import (
    MemorizingPrimalComponent,
    MergeTopSolutions,
)
from miplearn.extractors.fields import H5FieldsExtractor

@dataclass
class CustomerData:
    customer_id: List[int]
    x: List[int]
    y: List[int]
    demand: List[int]
    ready_time: List[int]
    due_date: List[int]
    service_time: List[int]
    num_vehicles: int
    capacity: int

def distance(data, i, j):
    """Calcola la distanza tra due clienti dati gli indici i e j."""
    return ((data.x[i] - data.x[j]) ** 2 + (data.y[i] - data.y[j]) ** 2) ** 0.5


def read_customers_from_file(filename, num_vehicles: int, capacity: int) -> CustomerData:
    customer_ids = []
    x_coords = []
    y_coords = []
    demands = []
    ready_times = []
    due_dates = []
    service_times = []

    with open(filename, 'r') as file:
        lines = file.readlines()
        for line in lines:
            values = line.split()
            if not values or not values[0].isdigit():
                continue
            
            values = list(map(int, values))
            
            if len(values) >= 7:
                customer_ids.append(values[0])
                x_coords.append(values[1])
                y_coords.append(values[2])
                demands.append(values[3])
                ready_times.append(values[4])
                due_dates.append(values[5])
                service_times.append(values[6])

    return CustomerData(
        customer_id=customer_ids,
        x=x_coords,
        y=y_coords,
        demand=demands,
        ready_time=ready_times,
        due_date=due_dates,
        service_time=service_times,
        num_vehicles=num_vehicles, 
        capacity=capacity 
    )

def build_model(data: Union[str, CustomerData]) -> GurobiModel:
    if isinstance(data, str):
        data = read_pkl_gz(data)

    n = len(data.customer_id)
    num_vehicles = data.num_vehicles
    capacity = data.capacity
    
    model = gp.Model("VRPTW")
    
    x = model.addVars(n, n, num_vehicles, vtype=GRB.BINARY, name="x")
    t = model.addVars(n, vtype=GRB.CONTINUOUS, name="t")
    
    dist = {(i, j): distance(data, i, j) for i in range(n) for j in range(n) if i != j}
    
    model.setObjective(
        gp.quicksum(dist[i, j] * x[i, j, k] for i in range(n) for j in range(n) if i != j for k in range(num_vehicles)),
        GRB.MINIMIZE
    )
    
    for j in range(1, n):
        model.addConstr(gp.quicksum(x[i, j, k] for i in range(n) if i != j for k in range(num_vehicles)) == 1)
    
    for k in range(num_vehicles):
        model.addConstr(gp.quicksum(x[0, j, k] for j in range(1, n)) <= 1)

    for i in range(n):
        for k in range(num_vehicles):
            model.addConstr(
                gp.quicksum(x[i, j, k] for j in range(n) if i != j) == gp.quicksum(x[j, i, k] for j in range(n) if i != j)
            )
    
    for k in range(num_vehicles):
        model.addConstr(
            gp.quicksum(data.demand[j] * gp.quicksum(x[i, j, k] for i in range(n) if i != j) for j in range(1, n)) <= capacity
        )
    
    for i in range(1, n):
        for j in range(1, n):
            if i != j:
                for k in range(num_vehicles):
                    model.addConstr(
                        t[i] + data.service_time[i] + dist[i, j] - t[j] <= (1 - x[i, j, k]) * 1e6
                    )
    
    for i in range(n):
        model.addConstr(t[i] >= data.ready_time[i])
        model.addConstr(t[i] <= data.due_date[i])

    return GurobiModel(model)    
    

def main():
    train_data_list = []
    test_data_list = []

    num_vehicles = 25  # Numero di veicoli
    capacity = 200     # Capacità dei veicoli

    train_filenames = os.listdir("train")
    for train_file in train_filenames:
        train_data = read_customers_from_file(f"train/{train_file}", num_vehicles, capacity)
        train_data_list.append(train_data)
    
    train_data = write_pkl_gz(train_data_list, "models\\train")

    test_filenames = os.listdir("test")
    for test_file in test_filenames:
        test_data = read_customers_from_file(f"test/{test_file}", num_vehicles, capacity)
        test_data_list.append(test_data)

    test_data = write_pkl_gz(test_data_list, "models\\test")

    bc = BasicCollector()
    bc.collect(train_data, build_model)

    comp = MemorizingPrimalComponent(
        clf=KNeighborsClassifier(n_neighbors=25),
        extractor=H5FieldsExtractor(
            instance_fields=["static_constr_rhs"],
        ),
        constructor=MergeTopSolutions(25, [0.0, 1.0]),
        action=SetWarmStart(),
    )

    solver_ml = LearningSolver(components=[comp])
    solver_ml.fit(train_data)
    solver_ml.optimize(test_data[0], build_model)

if __name__ == "__main__":
    main()
