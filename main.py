from data_simulator import DataSimulator
from optimizer import Optimizer

if __name__ == '__main__':
    # create simulator
    ds = DataSimulator(
        num_transactions=1000,
        num_products=20,
        num_customers=15,
        num_product_drivers=2,
        max_product_attributes=3,
        num_customer_drivers=2,
        max_customer_attributes=3,
        factor_lower_bound=0,
        factor_upper_bound=0.15,
        max_abs_corridor=1,
        max_abs_deviation=0,
        gross_revenue_lower_bound=10,
        gross_revenue_upper_bound=1000
    )

    # generate data
    transactions = ds.generate_transactions()
    drivers = ds.product_drivers + ds.customer_drivers

    # create optimizer
    optimizer = Optimizer(
        transaction=transactions,
        drivers=drivers
    )

    # solve
    result = optimizer.solve()

    # export
    # transactions.to_excel("03_Output/transactions.xlsx", index=False)