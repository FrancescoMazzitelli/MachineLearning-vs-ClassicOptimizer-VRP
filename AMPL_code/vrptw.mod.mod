set NODES;
param numVehicles integer;
param capacity;
param demand{NODES};
param service_time{NODES};
param ready_time{NODES};
param due_date{NODES};
param dist{NODES, NODES};

var x{NODES, NODES, 1..numVehicles} binary;
var t{NODES} >= 0;

minimize TotalDistance:
    sum{i in NODES, j in NODES, k in 1..numVehicles: i != j} dist[i,j] * x[i,j,k];

subject to VisitOnce {j in NODES diff {1}}:
    sum{i in NODES, k in 1..numVehicles: i != j} x[i,j,k] = 1;

subject to VehicleStart {k in 1..numVehicles}:
    sum{j in NODES diff {1}} x[1,j,k] <= 1;

subject to FlowBalance {i in NODES, k in 1..numVehicles}:
    sum{j in NODES: i != j} x[i,j,k] = sum{j in NODES: i != j} x[j,i,k];

subject to CapacityConstraint {k in 1..numVehicles}:
    sum{j in NODES diff {1}} demand[j] * sum{i in NODES: i != j} x[i,j,k] <= capacity;

subject to TimeWindowConstraints {i in NODES, j in NODES, k in 1..numVehicles: i != j}:
    t[i] + service_time[i] + dist[i,j] - t[j] <= (1 - x[i,j,k]) * 1e6;

subject to TimeBounds {i in NODES}:
    ready_time[i] <= t[i] <= due_date[i];
