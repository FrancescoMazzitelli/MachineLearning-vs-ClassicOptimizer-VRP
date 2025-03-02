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
    param num_vehicles;
    param capacity;  # Capacità del veicolo

    # Dati dei clienti (coordinata X, Y, domanda, tempo di servizio, finestra temporale)
    param xcoord {NODES};
    param ycoord {NODES};
    param demand {NODES};
    param ready_time {NODES};
    param due_date {NODES};
    param service_time {NODES};

# Distanza tra i nodi
param distance {i in NODES, j in NODES} = sqrt((xcoord[i] - xcoord[j])^2 + (ycoord[i] - ycoord[j])^2);

# Variabili di decisione
var x {i in NODES, j in NODES, k in 1..num_vehicles} binary;  # 1 se il veicolo k va dal nodo i al nodo j
var y {k in 1..num_vehicles} binary;  # 1 se il veicolo k è utilizzato
var t {i in NODES} >= 0;  # Tempo di arrivo al nodo i

# Coefficiente di ponderazione per bilanciare la distanza e il numero di veicoli
param alpha := 1;  # Ponderazione della distanza
param beta := 1;   # Ponderazione del numero di veicoli

# Funzione obiettivo: minimizzare la distanza percorsa e il numero di veicoli
minimize TotalObjective:
    alpha * sum {i in NODES, j in NODES, k in 1..num_vehicles} distance[i,j] * x[i,j,k]
    + beta * sum {k in 1..num_vehicles} y[k];

# Ogni veicolo deve partire dal deposito (nodo 0) e andare verso un altro nodo
subject to StartFromDepot {k in 1..num_vehicles}:
    sum {j in NODES} x[1,j,k] <= 1;

        
# Vincolo di visita esattamente una volta per ciascun nodo (escluso il deposito)
subject to VisitOnce {j in NODES diff {1}}:
    sum {i in NODES diff {j}, k in 1..num_vehicles} x[i,j,k] = 1;

# Vincolo per il bilanciamento del flusso (ogni nodo deve essere visitato una volta e lasciato)
subject to FlowBalance {i in NODES, k in 1..num_vehicles}:
    sum {j in NODES diff {i}} x[i,j,k] = sum {j in NODES diff {i}} x[j,i,k];

# Capacità del veicolo
subject to CapacityConstraint {k in 1..num_vehicles}:
    sum {i in NODES diff {1}, j in NODES diff {1}} demand[j] * x[i,j,k] <= capacity;

# Vincolo di finestre temporali (il tempo di arrivo deve essere coerente con la finestra temporale)
subject to TimeWindows {i in NODES diff {1}, j in NODES diff {1}, k in 1..num_vehicles: i != j}:
    t[i] + service_time[i] + distance[i,j] - t[j] <= (1 - x[i,j,k]) * 1e6;

# Vincoli di ready time e due date per ciascun nodo
subject to ReadyTime {i in NODES diff {1}}:
    t[i] >= ready_time[i];

subject to DueDate {i in NODES diff {1}}:
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
    
    
    ampl.setOption("solver", "gurobi")
    ampl.setOption("solver_options", "MIPGap=0")
    ampl.setOption("solver_options", "FeasibilityTol=1e-9")
    ampl.setOption("solver_options", "IntFeasTol=1e-9")

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

customers = read_customers_from_file('c102.txt')
num_vehicles = 25
capacity = 200
routes = solve_vrptw_amplepy(customers, num_vehicles, capacity)
if routes:
    plot_solution(customers, routes)
else:
    print("Nessuna soluzione ottimale trovata.")
