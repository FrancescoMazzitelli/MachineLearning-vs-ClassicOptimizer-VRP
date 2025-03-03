import random
import math
import pickle, gzip

# Se MIPLearn non fornisce write_pkl_gz, puoi definirla così:
def write_pkl_gz(data, filename):
    with gzip.open(filename, "wb") as f:
        pickle.dump(data, f)

def genDataset(filename, j):
    random.seed(42 + j)
    num_customers = 100
    vehicle_capacity = 200
    num_vehicles = 25

    depot = {
        'id': 0,
        'x': 40,
        'y': 50,
        'demand': 0,
        'ready': 0,
        'due': 1236,
        'service': 0
    }

    customers = {}
    for i in range(1, num_customers + 1):
        x = random.randint(0, 100)
        y = random.randint(0, 100)
        demand = random.choice([10, 20, 30, 40])
        customers[i] = {
            'id': i,
            'x': x,
            'y': y,
            'demand': demand
        }

    # Costruzione di una rotta di riferimento per garantire la fattibilità
    route = list(range(1, num_customers + 1))
    random.shuffle(route)

    current_time = 0
    prev_x, prev_y = depot['x'], depot['y']

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

    total_demand = sum(cust['demand'] for cust in customers.values())
    if total_demand > vehicle_capacity * num_vehicles:
        print("Attenzione: il totale della domanda eccede la capacità complessiva dei veicoli!")
    else:
        print("Dataset generato: domanda totale =", total_demand)

    # Costruisci l'istanza da salvare
    instance = {
        'depot': depot,
        'customers': customers,
        'vehicle_capacity': vehicle_capacity,
        'num_vehicles': num_vehicles
    }

    # Salva l'istanza in formato pickle compresso
    write_pkl_gz(instance, filename)
    print(f"Istanza salvata in {filename}")

def main():
    output_num = 500
    for j in range(output_num):
        # Genera file con nome ad es. addestramento/dataset00000.pkl.gz, addestramento/dataset00001.pkl.gz, ...
        filename = f"addestramento/dataset{j:05d}.pkl.gz"
        genDataset(filename, j)

if __name__ == "__main__":
    main()
