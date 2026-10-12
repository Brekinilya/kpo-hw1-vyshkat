from abc import ABC, abstractmethod


class IInventory(ABC):
    @property
    @abstractmethod
    def inventory_number(self) -> int: ...

    @property
    @abstractmethod
    def name(self) -> str: ...

    @property
    @abstractmethod
    def kind(self) -> str: ...


class IEnergyConsumer(ABC):
    @property
    @abstractmethod
    def daily_energy_kwh(self) -> float: ...
