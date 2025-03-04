import gurobipy as gp
from gurobipy import GRB
import os
import h5py
import numpy as np
from miplearn.io import write_pkl_gz
from miplearn.solvers.gurobi import GurobiModel

def distance(customer1, customer2):
    return ((customer1['x'] - customer2['x']) ** 2 + (customer1['y'] - customer2['y']) ** 2) ** 0.5

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
    
    return model    
    

def save_model_to_mps_gz(model, filename):
    model.write(filename) 

def save_optimal_solution_to_h5(model, customers, num_vehicles, filename):
    with h5py.File(filename, 'w') as f:
        customer_data = f.create_group('customers')
        for i, customer in enumerate(customers):
            customer_group = customer_data.create_group(str(i))
            customer_group.create_dataset('id', data=customer['id'])
            customer_group.create_dataset('x', data=customer['x'])
            customer_group.create_dataset('y', data=customer['y'])
            customer_group.create_dataset('demand', data=customer['demand'])
            customer_group.create_dataset('ready_time', data=customer['ready_time'])
            customer_group.create_dataset('due_date', data=customer['due_date'])
            customer_group.create_dataset('service_time', data=customer['service_time'])
        
        solution_data = f.create_group('solution')

        x_sol = np.array([
            [
                model.getVarByName(f'x[{i},{j},{k}]').x
                for i in range(len(customers))
                for j in range(len(customers)) if i != j
            ] for k in range(num_vehicles)
        ])

        t_sol = np.array([
            model.getVarByName(f't[{i}]').x
            for i in range(len(customers))
        ])

        solution_data.create_dataset('x', data=x_sol)
        solution_data.create_dataset('t', data=t_sol)


def generate_and_save_solved_models(customers_list, num_vehicles, capacity, output_dir):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    for idx, customers in enumerate(customers_list):
        model = solve_vrptw_gurobi(customers, num_vehicles, capacity)
        model.optimize()
        
        
        mps_filename = f"{output_dir}/model_{idx}_solved.mps"
        save_model_to_mps_gz(model, mps_filename)
        print(f"Modello {idx} risolto e salvato in {mps_filename}")
        
        h5_filename = f"{output_dir}/solution_{idx}.h5"
        save_optimal_solution_to_h5(model, customers, num_vehicles, h5_filename)
        print(f"Soluzione ottimale {idx} salvata in {h5_filename}")


def main():
    customers_list = []
    filenames = os.listdir("Benchmark-alter")
    for file in filenames:
        customer = read_customers_from_file(f"Benchmark-alter/{file}")
        customers_list.append(customer)
    num_vehicles = 25  # Numero di veicoli
    capacity = 200     # Capacità dei veicoli

    generate_and_save_solved_models(customers_list, num_vehicles, capacity, "models")

if __name__ == "__main__":
    main()
