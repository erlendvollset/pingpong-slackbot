from enum import Enum, EnumMeta
from typing import Any, Optional, Type, TypeVar


class EnumMetaExtension(EnumMeta):
    """
    >>> class MyEnum(Enum, metaclass=EnumMetaExtension):
    ...     A = 1
    >>> 1 in MyEnum
    True
    >>> 2 in MyEnum
    False
    """

    def __contains__(cls, item: Any) -> bool:
        try:
            cls(item)
        except ValueError:
            return False
        return True


T = TypeVar("T")


class BaseEnum(Enum, metaclass=EnumMetaExtension):
    """
    >>> class MyEnum(BaseEnum):
    ...     A = 1
    >>> MyEnum.of(1)
    <MyEnum.A: 1>
    >>> MyEnum.of(2) is None
    True
    """

    @classmethod
    def of(cls: Type[T], item: Any) -> Optional[T]:
        if item in cls:  # type: ignore
            return cls(item)  # type: ignore
        return None
