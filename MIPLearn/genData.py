import random
import math

def genDataset(filename, j):
    random.seed(42+j) 
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

    # Costruzione di una rotta “di riferimento” per garantire la fattibilità
    # Creiamo una permutazione casuale degli id dei clienti
    route = list(range(1, num_customers + 1))
    random.shuffle(route)

    # Variabili per simulare l'orario lungo la rotta
    current_time = 0
    prev_x, prev_y = depot['x'], depot['y']

    # Per ogni cliente nella rotta, calcoliamo il tempo di arrivo e definiamo la finestra temporale
    for cid in route:
        cust = customers[cid]
        # Calcola il tempo di viaggio (arrotondato) dal nodo precedente
        travel_time = int(round(math.hypot(cust['x'] - prev_x, cust['y'] - prev_y)))
        arrival = current_time + travel_time
        # Imposta la finestra temporale:
        # - ready time pari al tempo di arrivo
        # - due date pari al ready time più uno slack casuale tra 50 e 100
        ready = arrival
        slack = random.randint(50, 100)
        due = ready + slack
        cust['ready'] = ready
        cust['due'] = due
        # Tempo di servizio fisso (90) come nell'esempio
        cust['service'] = 90
        # Aggiorna il tempo (servizio iniziato appena si arriva, con attesa eventuale già incorporata)
        current_time = arrival + 90
        prev_x, prev_y = cust['x'], cust['y']

    # (Opzionale) Verifica che il totale della domanda non ecceda la capacità totale dei veicoli
    total_demand = sum(cust['demand'] for cust in customers.values())
    if total_demand > vehicle_capacity * num_vehicles:
        print("Attenzione: il totale della domanda eccede la capacità complessiva dei veicoli!")
    else:
        print("Dataset generato: domanda totale =", total_demand)

    header = f"{'CUST NO.':>8} {'XCOORD.':>8} {'YCOORD.':>8} {'DEMAND':>8} {'READY TIME':>12} {'DUE DATE':>10} {'SERVICE':>8}"
    # print(header)

    print(f"{depot['id']:8d} {depot['x']:8d} {depot['y']:8d} {depot['demand']:8d} {depot['ready']:12d} {depot['due']:10d} {depot['service']:8d}")
    for i in range(1, num_customers + 1):
        cust = customers[i]
        print(f"{cust['id']:8d} {cust['x']:8d} {cust['y']:8d} {cust['demand']:8d} {cust['ready']:12d} {cust['due']:10d} {cust['service']:8d}")

    with open(filename, "w") as f:
            f.write(header + "\n")
            f.write(f"{depot['id']:8d} {depot['x']:8d} {depot['y']:8d} {depot['demand']:8d} {depot['ready']:12d} {depot['due']:10d} {depot['service']:8d}\n")
            for i in range(1, num_customers + 1):
                cust = customers[i]
                f.write(f"{cust['id']:8d} {cust['x']:8d} {cust['y']:8d} {cust['demand']:8d} {cust['ready']:12d} {cust['due']:10d} {cust['service']:8d}\n")


def main():
    output_num = 10
    for j in range(output_num):
        filename = f"addestramento/dataset{j}.txt" 
        genDataset(filename, j)

if __name__ == "__main__":
    main()