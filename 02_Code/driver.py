from typing import List, Dict


class Attribute(object):

    def __init__(self, attribute_name: str, lower_bound: float, upper_bound: float, corridor_lower_bound: float = None,
                 corridor_upper_bound: float = None, factor: float = None):
        self.attribute_name = attribute_name
        self.lower_bound = lower_bound
        self.upper_bound = upper_bound
        self.corridor_lower_bound = corridor_lower_bound
        self.corridor_upper_bound = corridor_upper_bound
        self.factor = factor


class Driver(object):

    def __init__(self, driver_name: str, attributes: List[Attribute], order: Dict[Attribute, int]):
        self.driver_name = driver_name
        self.attributes = attributes
        self.order = order
