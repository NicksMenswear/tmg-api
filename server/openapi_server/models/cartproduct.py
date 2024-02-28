from sqlalchemy.orm import relationship
from openapi_server.models.base_model_ import Model
from openapi_server import util

class CartProduct(Model):
    __tablename__ = "cartproducts"

    user = relationship('Cart', back_populates='cartproducts')


    def __init__(self, id=None, cart_id=None, product_id=None, category=None, quantity=None):
        """Cart - a model defined in OpenAPI

        :param quantity: The number of the cart item.
        :type quantity: int
        :param category: The category of the cart.
        :type category: str
        :param cart_id: The id of the cart.
        :type cart_id: str
        :param product_id: The id of the product.
        :type product_id: str
        """
        self.openapi_types = {
            'id': int,
            'cart_id': int,
            'product_id': int,
            'category': str,
            'quantity': int,
        }

        self.attribute_map = {
            'id': 'id',
            'cart_id': 'cart_id',
            'product_id': 'product_id',
            'category': 'category',
            'quantity': 'quantity'
        }

        # super(Cart, self).__init__()
        self._id = id
        self._cart_id = cart_id
        self._product_id = product_id
        self._category = category
        self._quantity = quantity

    @classmethod
    def from_dict(cls, dikt) -> 'CartProduct':
        """Returns the dict as a model

        :param dikt: A dict.
        :type: dict
        :return: The Cart of this Cart.  # noqa: E501
        """
        return util.deserialize_model(dikt, cls)

    @property
    def to_dict(self):
        """Convert the model instance to a dictionary."""
        result = self.openapi_types.copy()
        result['id'] = self.id
        result['cart_id'] = self.cart_id
        result['product_id'] = self.product_id
        result['category'] = self.category
        result['quantity'] = self.quantity
        return result
    
    @to_dict.setter
    def to_dict(self, values):
        """Set attributes based on a dictionary."""
        if 'id' in values:
            self.id = values['id']
        if 'cart_id' in values:
            self.cart_id = values['cart_id']
        if 'product_id' in values:
            self.product_id = values['product_id']
        if 'category' in values:
            self.category = values['category']
        if 'quantity' in values:
            self.quantity = values['quantity']

    @property
    def id(self) -> str:
        """Gets the id of this Cart.

        :return: The id of this Cart.
        :rtype: str
        """
        return self._id

    @id.setter
    def id(self, id: str):
        """Sets the id of this Cart.

        :param id: The id of this Cart.
        :type id: str
        """
        self._id = id

    @property
    def cart_id(self) -> str:
        """Gets the name of this Cart.

        :return: The name of this Cart.
        :rtype: str
        """
        return self._cart_id

    @cart_id.setter
    def cart_id(self, cart_id: str):
        """Sets the name of this Cart.

        :param cart_id: The name of this Cart.
        :type cart_id: str
        """
        if cart_id is None:
            raise ValueError("Invalid value for `cart_id`, must not be `None`")  # noqa: E501

        self._cart_id = cart_id

    @property
    def product_id(self) -> int:
        """Gets the name of this Cart.

        :return: The name of this Cart.
        :rtype: str
        """
        return self._product_id

    @product_id.setter
    def product_id(self, product_id: int):
        """Sets the name of this Cart.

        :param product_id: The name of this Cart.
        :type product_id: str
        """
        if product_id is None:
            raise ValueError("Invalid value for `product_id`, must not be `None`")  # noqa: E501

        self._product_id = product_id

    @property
    def category(self) -> str:
        """Gets the name of this Cart.

        :return: The name of this Cart.
        :rtype: str
        """
        return self._category

    @category.setter
    def category(self, category: str):
        """Sets the name of this Cart.

        :param category: The name of this category.
        :type category: str
        """
        if category is None:
            raise ValueError("Invalid value for `category`, must not be `None`")  # noqa: E501

        self._category = category

    @property
    def quantity(self) -> int:
        """Gets the name of this Cart.

        :return: The name of this Cart.
        :rtype: int
        """
        return self._quantity

    @quantity.setter
    def quantity(self, quantity: int):
        """Sets the name of this Cart.

        :param quantity: The name of this quantity.
        :type quantity: integer
        """
        if quantity is None:
            raise ValueError("Invalid value for `quantity`, must not be `None`")  # noqa: E501

        self._quantity = quantity
