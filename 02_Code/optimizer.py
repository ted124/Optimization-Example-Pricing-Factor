from typing import List

import pandas as pd
from ortools.linear_solver import pywraplp

from driver import Driver


class Optimizer(object):

    def __init__(self, transaction: pd.DataFrame, drivers: List[Driver],
                 column_gross_revenue: str = "Gross Revenue", column_net_revenue: str = "Net Revenue",
                 column_product_id: str = "Product ID", column_customer_id: str = "Customer ID"):
        self.transaction = transaction
        self.drivers = drivers
        self.column_gross_revenue = column_gross_revenue
        self.column_net_revenue = column_net_revenue
        self.column_product_id = column_product_id
        self.column_customer_id = column_customer_id
        self.column_drivers = [driver.driver_name for driver in drivers]

    def solve(self):
        # create a solver with the GLOP backend
        solver = pywraplp.Solver.CreateSolver("GLOP")
        parameters = pywraplp.MPSolverParameters()
        parameters.SetDoubleParam(pywraplp.MPSolverParameters.LP_ALGORITHM, pywraplp.MPSolverParameters.PRIMAL)
        parameters.SetDoubleParam(pywraplp.MPSolverParameters.PRESOLVE, pywraplp.MPSolverParameters.PRESOLVE_OFF)

        # create driver variables
        # driver variables
        driver_variables = {}
        for driver in self.drivers:

            # create a dictionary to store all variables in current driver
            temp_variable = {}

            # aggregate transaction by current driver
            groupby_column = [driver.driver_name]
            columns = groupby_column + [self.column_gross_revenue, self.column_net_revenue]
            discount_dict = {
                attribute_name: 1 - net_revenue / gross_revenue
                for attribute_name, gross_revenue, net_revenue in self.transaction[columns].groupby(
                    by=groupby_column,
                    as_index=False
                ).sum().values.tolist()
            }

            # attributes
            for attribute in driver.attributes:
                temp_variable[attribute.attribute_name] = solver.NumVar(
                    lb=attribute.lower_bound,
                    ub=attribute.upper_bound,
                    name=attribute.attribute_name
                )

                # add corridor constraint
                actual_discount = discount_dict[attribute.attribute_name]

                # lower bound
                if attribute.corridor_lower_bound is not None:
                    solver.Add(
                        actual_discount - temp_variable[attribute.attribute_name] <= attribute.corridor_lower_bound
                    )

                # upper bound
                if attribute.corridor_upper_bound is not None:
                    solver.Add(
                        temp_variable[attribute.attribute_name] - actual_discount <= attribute.corridor_upper_bound
                    )

            # add order constraints
            for attribute in driver.attributes:
                for other_attribute in driver.attributes:
                    if driver.order[attribute] > driver.order[other_attribute]:
                        solver.Add(
                            temp_variable[attribute.attribute_name] >= temp_variable[other_attribute.attribute_name]
                        )

            # add to dictionary
            driver_variables[driver.driver_name] = temp_variable

        # aggregate transaction into product customer level
        groupby_columns = self.column_drivers
        # groupby_columns = [self.column_product_id, self.column_customer_id] + self.column_drivers
        columns = groupby_columns + [self.column_gross_revenue, self.column_net_revenue]

        transaction_agg = self.transaction[columns].groupby(
            by=groupby_columns,
            as_index=False
        ).sum()

        # count how many combinations
        n = transaction_agg.shape[0]

        # total net revenue
        net_revenue = transaction_agg[self.column_net_revenue].sum()

        # discounts, difference between actual net revenue and simulated net revenue
        # and auxiliary variables for each product customer combination
        auxiliary_variables = []
        for row in transaction_agg.index:
            # current row
            temp_row = transaction_agg.loc[row].copy()

            # discount
            discount = None
            for driver_name in self.column_drivers:
                if discount is None:
                    discount = driver_variables[driver_name][temp_row[driver_name]]
                else:
                    discount += driver_variables[driver_name][temp_row[driver_name]]

            # revenue difference
            difference = temp_row[self.column_gross_revenue] * (1 - discount) - temp_row[self.column_net_revenue]

            # create two auxiliary variables for each product customer combination
            temp_positive = solver.NumVar(0, net_revenue, str(row) + " Positive")
            temp_negative = solver.NumVar(0, net_revenue, str(row) + " Negative")

            # add to list
            auxiliary_variables.append([temp_positive, temp_negative])

            # add constraint
            solver.Add(temp_positive - temp_negative == difference)

        # objective function
        solver.Minimize(sum(sum(auxiliary_variables[i]) for i in range(n)))

        # solve
        status = solver.Solve(parameters)

        if status == pywraplp.Solver.OPTIMAL:
            print("Solution:")
            print("Objective value =", solver.Objective().Value())
            for driver in driver_variables:
                for attribute in driver_variables[driver]:
                    print(driver_variables[driver][attribute].name() + " " + str(
                        driver_variables[driver][attribute].solution_value()))
            return driver_variables
        else:
            return None
