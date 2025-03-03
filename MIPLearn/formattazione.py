from dataclasses import dataclass
from typing import List
@dataclass
class Formattazione:
    capacity: int
    num_vehicles: int
    cust_no: List[int]
    x: List[int]
    y: List[int]
    demand: List[int]
    ready_time: List[int]
    due_date: List[int]
    service_time: List[int]
