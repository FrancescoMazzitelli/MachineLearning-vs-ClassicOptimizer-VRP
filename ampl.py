from amplpy import AMPL, Environment
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

def solve_vrptw_amplepy(customers, num_vehicles, capacity):
    env = Environment(r"C:\Users\simon\AMPL")
    ampl = AMPL(env)
    
    # Definizione del modello AMPL (senza il comando solve)
    ampl.eval('''
    set NODES;
    param xcoord {NODES};
    param ycoord {NODES};
    param demand {NODES};
    param ready_time {NODES};
    param due_date {NODES};
    param service_time {NODES};
    param capacity;
    param num_vehicles;
    param dist {NODES, NODES};
    
    var x {NODES, NODES, 1..num_vehicles} binary;
    var t {NODES} >= 0;
    
    minimize TotalDistance: 
        sum {i in NODES, j in NODES, k in 1..num_vehicles: i <> j} dist[i,j] * x[i,j,k];
    
    subject to VisitOnce {j in NODES diff {1}}:
        sum {i in NODES diff {j}, k in 1..num_vehicles} x[i,j,k] = 1;
    
    subject to VehicleStart {k in 1..num_vehicles}:
        sum {j in NODES diff {1}} x[1,j,k] <= 1;
    
    subject to FlowBalance {i in NODES, k in 1..num_vehicles}:
        sum {j in NODES diff {i}} x[i,j,k] = sum {j in NODES diff {i}} x[j,i,k];
    
    subject to CapacityConstraint {k in 1..num_vehicles}:
        sum {j in NODES diff {1}, i in NODES diff {j}} demand[j] * x[i,j,k] <= capacity;
    
    subject to TimeWindows {i in NODES diff {1}, j in NODES diff {1}, k in 1..num_vehicles: i <> j}:
        t[i] + service_time[i] + dist[i,j] - t[j] <= (1 - x[i,j,k]) * 1e6;
    
    subject to ReadyTime {i in NODES}:
        t[i] >= ready_time[i];
    
    subject to DueTime {i in NODES}:
        t[i] <= due_date[i];
    ''')
    
    node_ids = [c['id'] for c in customers]
    ampl.set['NODES'] = node_ids
    ampl.param['capacity'] = capacity
    ampl.param['num_vehicles'] = num_vehicles
    
    for c in customers:
        ampl.param['xcoord'][c['id']] = c['x']
        ampl.param['ycoord'][c['id']] = c['y']
        ampl.param['demand'][c['id']] = c['demand']
        ampl.param['ready_time'][c['id']] = c['ready_time']
        ampl.param['due_date'][c['id']] = c['due_date']
        ampl.param['service_time'][c['id']] = c['service_time']
    
    
    for i in node_ids:
        for j in node_ids:
            ampl.param['dist'][i, j] = distance(customers[i-1], customers[j-1]) if i != j else 0
    
    ampl.setOption("solver", "gurobi")
    ampl.setOption("solver_options", "MIPGap=0 FeasibilityTol=1e-9 IntFeasTol=1e-9")
    ampl.solve()
    
    x_result = ampl.getVariable('x').getValues()
    
    routes = [[] for _ in range(num_vehicles)]
    for row in x_result:
        i, j, k = int(row[0]), int(row[1]), int(row[2])
        if row[3] > 0.5:
            routes[k-1].append((i, j))
    
    return routes

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
                x_coords = [customers[i-1]['x'], customers[j-1]['x']]
                y_coords = [customers[i-1]['y'], customers[j-1]['y']]
                plt.plot(x_coords, y_coords, marker='o', color=color)
            legend_labels.append(f"Veicolo {idx+1}")
            legend_patches.append(plt.Line2D([0], [0], color=color, lw=2, label=f"Veicolo {idx+1}"))
    
    plt.xlabel("Coordinata X")
    plt.ylabel("Coordinata Y")
    plt.title("Soluzione VRPTW - AMPL")
    if legend_patches:
        plt.legend(handles=legend_patches, loc="upper right")
    plt.show()

customers = read_customers_from_file('c101.txt')
num_vehicles = 25
capacity = 200
routes = solve_vrptw_amplepy(customers, num_vehicles, capacity)
if routes:
    plot_solution(customers, routes)
else:
    print("Nessuna soluzione ottimale trovata.")
