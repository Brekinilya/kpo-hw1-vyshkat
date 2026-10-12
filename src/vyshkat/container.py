from dependency_injector import containers, providers

from vyshkat.application.catalog import DEFAULT_CATALOG
from vyshkat.application.intake import Intake
from vyshkat.domain.park import Park
from vyshkat.domain.service_center import ServiceCenter
from vyshkat.ui.console import ConsoleApp
from vyshkat.ui.delivery_file import DeliveryFileLoader


class Container(containers.DeclarativeContainer):
    service_center = providers.Singleton(ServiceCenter)
    park = providers.Singleton(Park, service_center=service_center)
    catalog = providers.Object(DEFAULT_CATALOG)
    intake = providers.Singleton(Intake, park=park, catalog=catalog)
    delivery_loader = providers.Singleton(DeliveryFileLoader, intake=intake)
    console = providers.Factory(
        ConsoleApp,
        park=park,
        intake=intake,
        loader=delivery_loader,
        catalog=catalog,
    )
