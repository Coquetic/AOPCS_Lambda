from enum import Enum, unique

import aws_cdk as cdk


@unique
class BaseEnvironment(Enum):
    """Enum representing the environment to deploy to."""

    def __str__(self) -> str:
        """Return lower-case string representation of member name."""
        return self.name.lower()

    @property
    def cdk_value(self) -> cdk.Environment:
        """Get the environment's CDK environment."""
        if not isinstance(self.value, cdk.Environment):
            raise ValueError("Value of enum is not a CDK environment.")
        return self.value

    @property
    def region(self) -> str:
        """Get the environment's AWS region."""
        if not isinstance(self.cdk_value.region, str):
            raise ValueError("Value of enum is not a CDK environment region.")
        return self.cdk_value.region

    @property
    def account(self) -> str:
        """Get the environment's AWS account."""
        if not isinstance(self.cdk_value.account, str):
            raise ValueError("Value of enum is not a CDK environment account.")
        return self.cdk_value.account

    @classmethod
    def _missing_(cls, value: str):  # type: ignore
        """Get enum value ignoring case of member name.

        Args:
            value (str): name of member.

        Returns:
            _type_: value of enum member.
        """
        for member in cls:
            if member._name_ == value.upper():  # pylint: disable=protected-access
                return member
        raise ValueError("Invalid value provided to Atlas environment.")
