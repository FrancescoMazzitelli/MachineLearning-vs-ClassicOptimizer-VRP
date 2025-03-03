from miplearn.collectors.basic import BasicCollector
import gurobipy as gp
from gurobipy import GRB
from miplearn.io import write_pkl_gz, read_pkl_gz
import random
import math
import pickle, gzip
from typing import List
import random, math, numpy as np
from scipy.stats import uniform
import numpy as np
import math
from typing import List, Dict
from miplearn.solvers.gurobi import GurobiModel
import random
import numpy as np
import math
from typing import List, Dict, Tuple
from formattazione import Formattazione
from typing import Union
import os


def random_vrptw_data(samples: int, n: int, seed: int = 42) -> List[Formattazione]:
    random.seed(seed)
    np.random.seed(seed)
    
    instances = []
    depot_x, depot_y = 40, 50
    
    for _ in range(samples):
        depot = {
            'id': 0,
            'x': depot_x,
            'y': depot_y,
            'demand': 0,
            'ready': 0,
            'service': 0
        }
        
        xs = np.random.randint(0, 101, size=n)
        ys = np.random.randint(0, 101, size=n)
        demands = np.random.choice([10, 20, 30, 40], size=n)
        
        customers = {}
        for j in range(1, n+1):
            customers[j] = {
                'id': j,
                'x': int(xs[j-1]),
                'y': int(ys[j-1]),
                'demand': int(demands[j-1])
            }
        
        route = list(range(1, n+1))
        random.shuffle(route)
        current_time = 0
        prev_x, prev_y = depot_x, depot_y
        max_due = 0
        
        for cid in route:
            cust = customers[cid]
            travel_time = int(round(math.hypot(cust['x'] - prev_x, cust['y'] - prev_y)))
            arrival = current_time + travel_time
            ready = arrival
            slack = random.randint(50, 100)
            due = ready + slack
            cust['ready'] = ready
            cust['due'] = due
            cust['service'] = 90
            current_time = arrival + 90
            prev_x, prev_y = cust['x'], cust['y']
            max_due = max(max_due, due)
        
        last_customer = customers[route[-1]]
        return_time = int(round(math.hypot(last_customer['x'] - depot_x, last_customer['y'] - depot_y)))
        depot_due = max_due + return_time + 50
        
        for cid in customers:
            customers[cid]['due'] = min(customers[cid]['due'], depot_due - 1)
        
        cust_no = [0] + [customers[i]['id'] for i in customers]
        x = [depot_x] + [customers[i]['x'] for i in customers]
        y = [depot_y] + [customers[i]['y'] for i in customers]
        demand = [depot['demand']] + [customers[i]['demand'] for i in customers]
        ready_time = [depot['ready']] + [customers[i]['ready'] for i in customers]
        due_date = [depot_due] + [customers[i]['due'] for i in customers]
        service_time = [depot['service']] + [customers[i]['service'] for i in customers]
        
        instances.append(Formattazione(
            capacity=200,
            num_vehicles=25,
            cust_no=cust_no,
            x=x,
            y=y,
            demand=demand,
            ready_time=ready_time,
            due_date=due_date,
            service_time=service_time
        ))
    
    return instances





def read_customers_from_file(filename):
    customers = []
    with open(filename, 'r') as file:
        lines = file.readlines()
        for line in lines:
            values = line.split()
            if not values or not values[0].isdigit():
                continue
            values = list(map(int, values))
            if len(values) >= 7:
                customer = {
                    'id': values[0],
                    'x': values[1],
                    'y': values[2],
                    'demand': values[3],
                    'ready_time': values[4],
                    'due_date': values[5],
                    'service_time': values[6]
                }
                customers.append(customer)
    return customers



def build_vrptw_model(data: Union[str, Formattazione]):
    if isinstance(data, str):
        data = read_pkl_gz(data)  # Assume che il file sia stato salvato e caricato correttamente

    cust_no = data.cust_no
    xcoord = data.x
    ycoord = data.y
    demand = data.demand
    ready_time = data.ready_time
    due_date = data.due_date
    service_time = data.service_time
    num_vehicles = data.num_vehicles
    capacity = data.capacity

    n = len(cust_no)
    depot = cust_no[0]  # Assumiamo che il deposito sia il primo elemento

    # Calcola le distanze euclidee
    def distance(i, j):
        return ((xcoord[i] - xcoord[j])**2 + (ycoord[i] - ycoord[j])**2)**0.5
    
    dist = {(i, j): distance(i, j) for i in range(n) for j in range(n) if i != j}

    model = gp.Model("VRPTW")
    x = model.addVars(n, n, num_vehicles, vtype=GRB.BINARY, name="x")
    t = model.addVars(n, vtype=GRB.CONTINUOUS, name="t")

    # Obiettivo: minimizzare la distanza totale percorsa
    model.setObjective(
        gp.quicksum(dist[i, j] * x[i, j, k] for i in range(n) for j in range(n) if i != j for k in range(num_vehicles)),
        GRB.MINIMIZE
    )

    # Vincolo: ogni cliente deve essere servito una volta (eccetto il deposito)
    for j in range(1, n):
        model.addConstr(gp.quicksum(x[i, j, k] for i in range(n) if i != j for k in range(num_vehicles)) == 1)

    # Vincolo: ogni veicolo può partire al massimo una volta dal deposito
    for k in range(num_vehicles):
        model.addConstr(gp.quicksum(x[0, j, k] for j in range(1, n)) <= 1)

    # Vincolo: bilancio del flusso
    for i in range(n):
        for k in range(num_vehicles):
            model.addConstr(gp.quicksum(x[i, j, k] for j in range(n) if i != j) ==
                            gp.quicksum(x[j, i, k] for j in range(n) if i != j))
    
    # Vincolo: capacità del veicolo
    for k in range(num_vehicles):
        model.addConstr(
            gp.quicksum(demand[j] * gp.quicksum(x[i, j, k] for i in range(n) if i != j) for j in range(1, n))
            <= capacity
        )
    
    # Vincoli sui time windows
    for i in range(1, n):
        for j in range(1, n):
            if i != j:
                for k in range(num_vehicles):
                    model.addConstr(t[i] + service_time[i] + dist[i, j] - t[j] <= (1 - x[i, j, k]) * 1e6)
    
    for i in range(n):
        model.addConstr(t[i] >= ready_time[i])
        model.addConstr(t[i] <= due_date[i])
    
    return GurobiModel(model)


def load_instance(filename):
    with gzip.open(filename, "rb") as f:
        instance = pickle.load(f)
    return instance


def main():
    data = random_vrptw_data(samples=500, n=100, seed=42)
    train_data = data[0:450]
    test_data = data[450:500]
    # test_name = name[450:500]
    write_pkl_gz(train_data, "vrptw\\train")
    write_pkl_gz(test_data, "vrptw\\test")
    bc = BasicCollector()

    # os.chdir("fileGen")
    filenames = os.listdir("vrptw\\train")
    paths = []
    os.path.abspath("vrptw\\train")
    for file in filenames:
        path = os.path.join("vrptw\\train", file)
        paths.append(path)
    # os.chdir("fileH5")
    bc.collect(paths, build_vrptw_model)
    # os.chdir("..")
    # instance = load_instance("vrptw/train/00000.pkl.gz")
    # print("Deposito:", instance["depot"])
    # print("Primi 5 clienti:")
    # for k in sorted(instance["customers"].keys())[0:100]:
    #     print(instance["customers"][k])


if __name__ == "__main__":
    main()


