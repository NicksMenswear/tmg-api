from server.app import init_logging


def lambda_handler_add_expedited_shipping_for_suit_bundles(event, context):
    from server.jobs.add_expedited_shipping_for_suit_bundles import add_expedited_shipping_for_suit_bundles

    init_logging(debug=True)

    add_expedited_shipping_for_suit_bundles()


if __name__ == "__main__":
    lambda_handler_add_expedited_shipping_for_suit_bundles(None, None)
