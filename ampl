from amplpy import AMPL, Environment
import pandas as pd

def read_c101_file(filename):
    df = pd.read_csv(filename, delim_whitespace=True, skiprows=1, 
                     names=["CUST_NO", "XCOORD", "YCOORD", "DEMAND", "READY_TIME", "DUE_DATE", "SERVICE"])
    return df

def solve_vrptw_ampl(data):
    env = Environment()
    ampl = AMPL(env)
    
    ampl.eval("""
    set CUSTOMERS;
    set VEHICLES;
    
    param capacity;
    param demand{CUSTOMERS};
    param ready_time{CUSTOMERS};
    param due_date{CUSTOMERS};
    param service_time{CUSTOMERS};
    param distance{CUSTOMERS, CUSTOMERS};
    
    var x{CUSTOMERS, CUSTOMERS, VEHICLES} binary;
    var arrival_time{CUSTOMERS} >= 0;
    
    minimize TotalDistance: sum{i in CUSTOMERS, j in CUSTOMERS, k in VEHICLES} distance[i,j] * x[i,j,k];
    
    s.t. OneVisit{i in CUSTOMERS}: sum{j in CUSTOMERS, k in VEHICLES} x[i,j,k] = 1;
    s.t. FlowConservation{k in VEHICLES, i in CUSTOMERS}: 
        sum{j in CUSTOMERS} x[i,j,k] - sum{j in CUSTOMERS} x[j,i,k] = 0;
    
    s.t. Capacity{k in VEHICLES}: 
        sum{i in CUSTOMERS} demand[i] * sum{j in CUSTOMERS} x[i,j,k] <= capacity;
    
    s.t. TimeWindows{i in CUSTOMERS, j in CUSTOMERS, k in VEHICLES}: 
        arrival_time[j] >= arrival_time[i] + service_time[i] + distance[i,j] * x[i,j,k] - (1 - x[i,j,k]) * 10000;
    
    s.t. ReadyTime{i in CUSTOMERS}: arrival_time[i] >= ready_time[i];
    s.t. DueDate{i in CUSTOMERS}: arrival_time[i] <= due_date[i];
    """)
    
    customers = list(data["CUST_NO"])
    vehicles = list(range(25))  # 25 veicoli
    capacity = 200
    
    ampl.set['CUSTOMERS'] = customers
    ampl.set['VEHICLES'] = vehicles
    ampl.param['capacity'] = capacity
    
    demand_dict = dict(zip(data["CUST_NO"], data["DEMAND"]))
    ready_time_dict = dict(zip(data["CUST_NO"], data["READY_TIME"]))
    due_date_dict = dict(zip(data["CUST_NO"], data["DUE_DATE"]))
    service_dict = dict(zip(data["CUST_NO"], data["SERVICE"]))
    
    ampl.param['demand'] = demand_dict
    ampl.param['ready_time'] = ready_time_dict
    ampl.param['due_date'] = due_date_dict
    ampl.param['service_time'] = service_dict
    
    # Creazione matrice distanza euclidea
    distances = {}
    for i in customers:
        for j in customers:
            dist = ((data.loc[i, "XCOORD"] - data.loc[j, "XCOORD"])**2 + 
                    (data.loc[i, "YCOORD"] - data.loc[j, "YCOORD"])**2) ** 0.5
            distances[i, j] = dist
    ampl.param['distance'] = distances
    
    # Impostazione solver Gurobi
    ampl.option['solver'] = 'gurobi'
    
    # Risoluzione
    ampl.solve()
    
    # Recupero soluzione
    solution = ampl.getVariable("x").getValues()
    print(solution)
    return solution

if __name__ == "__main__":
    filename = "c101.txt"
    data = read_c101_file(filename)
    solve_vrptw_ampl(data)
