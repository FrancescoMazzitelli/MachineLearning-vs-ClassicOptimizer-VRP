set NODES := 0..3;  # 0 è il deposito, 1, 2, 3 sono i clienti
param num_vehicles := 1;
param capacity := 15;  # Capacità del veicolo

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
var t {i in NODES} >= 0;  # Tempo di arrivo al nodo i

# Funzione obiettivo: minimizzare la distanza percorsa
minimize TotalDistance:
    sum {i in NODES, j in NODES, k in 1..num_vehicles} distance[i,j] * x[i,j,k];

# Vincolo di visita esattamente una volta per ciascun nodo (escluso il deposito)
subject to VisitOnce {j in NODES diff {0}}:
    sum {i in NODES diff {j}, k in 1..num_vehicles} x[i,j,k] = 1;

# Vincolo per il bilanciamento del flusso (ogni nodo deve essere visitato una volta e lasciato)
subject to FlowBalance {i in NODES, k in 1..num_vehicles}:
    sum {j in NODES diff {i}} x[i,j,k] = sum {j in NODES diff {i}} x[j,i,k];

# Capacità del veicolo
subject to CapacityConstraint {k in 1..num_vehicles}:
    sum {i in NODES diff {0}, j in NODES diff {0}} demand[j] * x[i,j,k] <= capacity;

# Vincolo di finestre temporali (il tempo di arrivo deve essere coerente con la finestra temporale)
subject to TimeWindows {i in NODES diff {0}, j in NODES diff {0}, k in 1..num_vehicles: i != j}:
    t[i] + service_time[i] + distance[i,j] - t[j] <= (1 - x[i,j,k]) * 1e6;

# Vincoli di ready time e due date per ciascun nodo
subject to ReadyTime {i in NODES}:
    t[i] >= ready_time[i];

subject to DueDate {i in NODES}:
    t[i] <= due_date[i];
