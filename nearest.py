import matplotlib.pyplot as plt
import numpy as np
import matplotlib.colors as mcolors
import time

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

def nearest_neighbor_vrptw(customers, num_vehicles, capacity):
    start_time = time.time()
    depot = customers[0]
    remaining_customers = customers[1:]
    routes = []
    total_distance = 0
    
    while remaining_customers:
        route = [depot]
        load = 0
        current_customer = depot
        
        while remaining_customers:
            nearest = None
            min_distance = float('inf')
            
            for customer in remaining_customers:
                if load + customer['demand'] <= capacity:
                    d = distance(current_customer, customer)
                    if d < min_distance:
                        min_distance = d
                        nearest = customer
            
            if nearest is None:
                break
            
            route.append(nearest)
            load += nearest['demand']
            remaining_customers.remove(nearest)
            current_customer = nearest
            total_distance += min_distance
        
        route.append(depot)
        total_distance += distance(current_customer, depot)
        routes.append(route)
    
    elapsed_time = time.time() - start_time
    print(f"Elapsed time: {elapsed_time:.4f} seconds")
    print(f"Upper Bound (total distance): {total_distance:.2f}")
    print(f"Number of vehicles used: {len(routes)}")
    
    return routes

def plot_solution(customers, routes):
    plt.figure(figsize=(10, 10))
    unique_colors = list(mcolors.TABLEAU_COLORS.values())
    
    for idx, route in enumerate(routes):
        color = unique_colors[idx % len(unique_colors)]
        x_coords = [customer['x'] for customer in route]
        y_coords = [customer['y'] for customer in route]
        plt.plot(x_coords, y_coords, marker='o', linestyle='-', color=color, label=f"Veicolo {idx+1}")
    
    plt.xlabel("Coordinata X")
    plt.ylabel("Coordinata Y")
    plt.title("Soluzione VRPTW - Nearest Neighbor")
    plt.legend()
    plt.show()

customers = read_customers_from_file('c101.txt')
num_vehicles = 25
capacity = 200
routes = nearest_neighbor_vrptw(customers, num_vehicles, capacity)

plot_solution(customers, routes)
