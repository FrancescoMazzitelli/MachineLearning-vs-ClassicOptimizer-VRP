set NODES := 0..100;

param xcoord {NODES};
param ycoord {NODES};
param demand {NODES};
param ready_time {NODES};
param due_date {NODES};
param service_time {NODES};
param capacity := 200;
param num_vehicles := 25;

param distance {i in NODES, j in NODES} = sqrt((xcoord[i] - xcoord[j])^2 + (ycoord[i] - ycoord[j])^2);

var x {i in NODES, j in NODES, k in 1..num_vehicles} binary;
var t {i in NODES} >= 0;

minimize TotalDistance:
    sum {i in NODES, j in NODES, k in 1..num_vehicles} distance[i,j] * x[i,j,k];

subject to VisitOnce {j in NODES diff {1}}:
    sum {i in NODES diff {j}, k in 1..num_vehicles} x[i,j,k] = 1;

subject to VehicleStart {k in 1..num_vehicles}:
    sum {j in NODES diff {1}} x[1,j,k] <= 1;

subject to FlowBalance {i in NODES, k in 1..num_vehicles}:
    sum {j in NODES diff {i}} x[i,j,k] = sum {j in NODES diff {i}} x[j,i,k];

subject to CapacityConstraint {k in 1..num_vehicles}:
    sum {i in NODES diff {1}, j in NODES diff {1}} demand[j] * x[i,j,k] <= capacity;

subject to TimeWindows {i in NODES diff {1}, j in NODES diff {1}, k in 1..num_vehicles: i != j}:
    t[i] + service_time[i] + distance[i,j] - t[j] <= (1 - x[i,j,k]) * 1e6;

subject to ReadyTime {i in NODES}:
    t[i] >= ready_time[i];

subject to DueTime {i in NODES}:
    t[i] <= due_date[i];

