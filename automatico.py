import gurobipy as gp
from gurobipy import GRB
import matplotlib.pyplot as plt
import numpy as np
import matplotlib.colors as mcolors

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

def distance(c1, c2):
    return ((c1['x'] - c2['x'])**2 + (c1['y'] - c2['y'])**2)**0.5

def solve_vrptw_gurobi(customers, num_vehicles, capacity):
    n = len(customers)
    depot = customers[0]
    
    dist = {(i, j): distance(customers[i], customers[j]) for i in range(n) for j in range(n) if i != j}
    
    model = gp.Model("VRPTW")
    
    x = model.addVars(n, n, num_vehicles, vtype=GRB.BINARY, name="x")
    t = model.addVars(n, vtype=GRB.CONTINUOUS, name="t")
    model.setParam('MIPGap', 0)
    model.setParam('FeasibilityTol', 1e-9)
    model.setParam('IntFeasTol', 1e-9)

    model.setObjective(gp.quicksum(dist[i, j] * x[i, j, k] for i in range(n) for j in range(n) if i != j for k in range(num_vehicles)), GRB.MINIMIZE)
    
    for j in range(1, n):
        model.addConstr(gp.quicksum(x[i, j, k] for i in range(n) if i != j for k in range(num_vehicles)) == 1)
    
    for k in range(num_vehicles):
        model.addConstr(gp.quicksum(x[0, j, k] for j in range(1, n)) <= 1)
    
    for i in range(n):
        for k in range(num_vehicles):
            model.addConstr(gp.quicksum(x[i, j, k] for j in range(n) if i != j) == gp.quicksum(x[j, i, k] for j in range(n) if i != j))
    
    for k in range(num_vehicles):
        model.addConstr(gp.quicksum(customers[j]['demand'] * gp.quicksum(x[i, j, k] for i in range(n) if i != j) for j in range(1, n)) <= capacity)
    
    for i in range(1, n):
        for j in range(1, n):
            if i != j:
                for k in range(num_vehicles):
                    model.addConstr(t[i] + customers[i]['service_time'] + dist[i, j] - t[j] <= (1 - x[i, j, k]) * 1e6)
    
    for i in range(n):
        model.addConstr(t[i] >= customers[i]['ready_time'])
        model.addConstr(t[i] <= customers[i]['due_date'])
    
    model.optimize()
    
    if model.status == GRB.OPTIMAL:
        routes = [[] for _ in range(num_vehicles)]
        for k in range(num_vehicles):
            for i in range(n):
                for j in range(n):
                    if i != j and x[i, j, k].x > 0.5:
                        routes[k].append((i, j))
                used_vehicles = sum(1 for route in routes if route)
        upper_bound = model.objVal
        print(f"Numero di veicoli usati: {used_vehicles}")
        print(f"Upper Bound: {upper_bound}")
        return routes
    else:
        return None

def plot_solution(customers, routes):
    plt.figure(figsize=(10, 10))
    
    unique_colors = list(mcolors.TABLEAU_COLORS.values()) 
    used_colors = {}
    legend_labels = []
    legend_patches = []
    
    for idx, route in enumerate(routes):
        if route: 
            if idx not in used_colors:
                used_colors[idx] = unique_colors[len(used_colors) % len(unique_colors)]
            color = used_colors[idx]
            
            for (i, j) in route:
                x_coords = [customers[i]['x'], customers[j]['x']]
                y_coords = [customers[i]['y'], customers[j]['y']]
                plt.plot(x_coords, y_coords, marker='o', color=color)
            
            legend_labels.append(f"Veicolo {idx+1}")
            legend_patches.append(plt.Line2D([0], [0], color=color, lw=2, label=f"Veicolo {idx+1}"))
    
    plt.xlabel("Coordinata X")
    plt.ylabel("Coordinata Y")
    plt.title("Soluzione VRPTW - Gurobi")
    
    if legend_patches:
        plt.legend(handles=legend_patches, loc="upper right")
    
    plt.show()

for i in range(1,9):
    print("\n\n\n")
    print("File C10"+str(i))
    print("\n\n\n")
    customers = read_customers_from_file("MIPLearn\\Benchmark-alter\\C10"+str(i)+"-alter.txt")
    num_vehicles = 25
    capacity = 200
    routes = solve_vrptw_gurobi(customers, num_vehicles, capacity)
    print("\n\n\n")