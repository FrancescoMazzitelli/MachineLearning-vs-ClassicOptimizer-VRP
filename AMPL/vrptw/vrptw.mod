set NODES := 1..101;
param num_vehicles := 25;
param capacity := 200;  # Capacità del veicolo

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

