from dataclasses import dataclass
from typing import Optional
from fprime_python_model.fpp_ast.fpp_locations import Location
from fprime_python_model.semantics.port_instance_identifier import (
    PortInstanceIdentifier,
)


@dataclass
class Endpoint:
    """
    A connection endpoint

    :param loc: The location where the endpoint is defined
    :type loc: Location
    :param port: The port instance identifier
    :type port: PortInstanceIdentifier
    :param port_number: The port number
    :type port_number: Optional[int]
    """

    loc: Location
    port: PortInstanceIdentifier
    port_number: Optional[int] = None

    def __str__(self):
        """
        String representation of the endpoint

        :return: Endpoint string
        :rtype: str
        """
        if self.port_number is not None:
            return f"{str(self.port)}[{self.port_number}]"
        else:
            return f"{str(self.port)}"


@dataclass
class Connection:
    """
    An FPP connection

    :param from_endpoint: The from endpoint
    :type from_endpoint: Endpoint
    :param to_endpoint: The to endpoint
    :type to_endpoint: Endpoint
    :param is_unmatched: Whether the connection is unmatched
    :type is_unmatched: bool
    """

    from_endpoint: Endpoint
    to_endpoint: Endpoint
    is_unmatched: bool = False

    def __str__(self):
        """
        String representation of the connection

        :return: Connection string
        :rtype: str
        """
        return f"{str(self.from_endpoint)} -> {str(self.to_endpoint)}"

    def __hash__(self):
        """
        Gets the hash value of the connection based on the connection string

        :return: Hash of the connection
        :rtype: str
        """
        return hash(self.__str__())
