import math
import random
import string

import pandas as pd

from driver import Attribute, Driver


def generate_names(num_names: int, prefix: str = "", length: int = 5):
    # set to store names
    names = set()

    while len(names) < num_names:
        names.add(prefix + ''.join(random.choice(list(string.ascii_uppercase)) for _ in range(length)))

    return names


def generate_ids(num_ids: int, prefix: str = "", length: int = 5):
    # set to store names
    ids = set()

    while len(ids) < num_ids:
        ids.add(prefix + ''.join(str(random.choice(list(range(10)))) for _ in range(length)))

    return ids


class DataSimulator(object):

    def __init__(self, num_transactions: int, num_products: int, num_customers: int,
                 num_product_drivers: int, max_product_attributes: int,
                 num_customer_drivers: int, max_customer_attributes: int,
                 factor_lower_bound: float, factor_upper_bound: float,
                 max_abs_corridor: float, max_abs_deviation: float,
                 gross_revenue_lower_bound: int, gross_revenue_upper_bound: int):
        self.num_transactions = num_transactions
        self.num_products = num_products
        self.num_customers = num_customers
        self.num_product_drivers = num_product_drivers
        self.max_product_attributes = max_product_attributes
        self.num_customer_drivers = num_customer_drivers
        self.max_customer_attributes = max_customer_attributes
        self.factor_lower_bound = factor_lower_bound
        self.factor_upper_bound = factor_upper_bound
        self.max_abs_corridor = max_abs_corridor
        self.max_abs_deviation = max_abs_deviation
        self.product_drivers = None
        self.customer_drivers = None
        self.products = None
        self.customers = None
        self.transactions = None
        self.gross_revenue_lower_bound = gross_revenue_lower_bound
        self.gross_revenue_upper_bound = gross_revenue_upper_bound

    def generate_attributes(self, num_attributes: int):
        attributes = []
        attribute_names = generate_names(num_names=num_attributes)
        for _ in range(num_attributes):
            # generate factor
            factor = random.uniform(self.factor_lower_bound, self.factor_upper_bound)

            # generate attribute
            attributes.append(
                Attribute(
                    attribute_name=attribute_names.pop(),
                    lower_bound=max(factor - random.uniform(0, 0.2), 0),
                    upper_bound=factor + random.uniform(0, 0.2),
                    corridor_lower_bound=random.uniform(0, self.max_abs_corridor),
                    corridor_upper_bound=random.uniform(0, self.max_abs_corridor),
                    factor=factor
                )
            )

        return attributes

    def generate_drivers(self, num_drivers: int, driver_name_prefix: str):
        drivers = []
        driver_names = generate_names(num_names=num_drivers, prefix=driver_name_prefix)
        for _ in range(num_drivers):
            # generate attributes
            num_attributes = random.randint(2, self.max_product_attributes)
            attributes = self.generate_attributes(num_attributes=num_attributes)

            # order
            attributes.sort(key=lambda attribute: attribute.factor)
            order = {attributes[i]: i for i in range(num_attributes)}

            # generate driver
            drivers.append(
                Driver(
                    driver_name=driver_names.pop(),
                    attributes=attributes,
                    order=order
                )
            )

        return drivers

    def generate_products(self):
        # check if already exists
        if self.products is not None:
            return self.products

        # generate product drivers
        if self.product_drivers is None:
            self.product_drivers = self.generate_drivers(
                num_drivers=self.num_product_drivers,
                driver_name_prefix="P"
            )

        # generate ids
        product_ids = generate_ids(num_ids=self.num_products, prefix="P")

        # generate data in a list
        products = []
        for product_id in product_ids:
            # create a list to store all information about the current product
            temp_product = [product_id]

            # factor
            factor = 0

            # random select attribute from each driver
            for driver in self.product_drivers:
                attribute = random.choice(driver.attributes)
                factor += attribute.factor
                temp_product.append(attribute.attribute_name)

            # add factor as last column
            temp_product.append(factor)

            # add to product list
            products.append(temp_product)

        # create data frame
        self.products = pd.DataFrame(
            data=products,
            columns=["Product ID"] + [driver.driver_name for driver in self.product_drivers] + ["Product Factor"]
        )

        return self.products

    def generate_customers(self):
        # check if already exists
        if self.customers is not None:
            return self.customers

        # generate customer drivers
        if self.customer_drivers is None:
            self.customer_drivers = self.generate_drivers(
                num_drivers=self.num_customer_drivers,
                driver_name_prefix="C"
            )

        # generate ids
        customer_ids = generate_ids(num_ids=self.num_customers, prefix="C")

        # generate data in a list
        customers = []
        for customer_id in customer_ids:
            # create a list to store all information about the current customer
            temp_customer = [customer_id]

            # factor
            factor = 0

            # random select attribute from each driver
            for driver in self.customer_drivers:
                attribute = random.choice(driver.attributes)
                factor += attribute.factor
                temp_customer.append(attribute.attribute_name)

            # add factor as last column
            temp_customer.append(factor)

            # add to product list
            customers.append(temp_customer)

        # create data frame
        self.customers = pd.DataFrame(
            data=customers,
            columns=["Customer ID"] + [driver.driver_name for driver in self.customer_drivers] + ["Customer Factor"]
        )

        return self.customers

    def generate_transactions(self):
        # check if already exists
        if self.transactions is not None:
            return self.transactions

        # generate products and customers
        products = self.generate_products().values.tolist()
        customers = self.generate_customers().values.tolist()

        # generate ids
        transaction_ids = generate_ids(
            num_ids=self.num_transactions,
            prefix="T",
            length=math.ceil(math.log10(self.num_transactions)) * 2
        )

        # generate data in a list
        transactions = []
        for transaction_id in transaction_ids:
            temp_transaction = [transaction_id]

            # random select product and customer
            product = random.choice(products)
            temp_transaction += product
            customer = random.choice(customers)
            temp_transaction += customer

            # calculate factor
            factor = product[-1] + customer[-1]

            # generate gross revenue
            gross_revenue = random.randint(self.gross_revenue_lower_bound, self.gross_revenue_upper_bound)

            # random deviation
            deviation = random.uniform(-self.max_abs_deviation, self.max_abs_deviation)

            # generate net revenue
            net_revenue = gross_revenue * (1 - factor + deviation)

            # add to list
            temp_transaction += [gross_revenue, net_revenue]

            # add to transaction list
            transactions.append(temp_transaction)

        # create dataframe
        product_columns = list(self.products.columns)
        customer_columns = list(self.customers.columns)
        self.transactions = pd.DataFrame(
            data=transactions,
            columns=["Transaction ID"] + product_columns + customer_columns + ["Gross Revenue", "Net Revenue"]
        )

        return self.transactions

    def export_driver_df(self):
        pass

    def export_data(self):
        pass


if __name__ == '__main__':
    da = DataSimulator(1000, 10, 2, 2, 2, 2, 2, 0.01, 0.2, 0.1, 0.3, 10, 1000)
    transaction = da.generate_transactions()
