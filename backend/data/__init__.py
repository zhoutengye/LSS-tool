"""数据访问层

提供统一的数据访问接口，支持多维度查询。
"""

from .providers import (
    DataProvider,
    PersonDataProvider,
    BatchDataProvider,
    ProcessDataProvider,
    WorkshopDataProvider,
    TimeDataProvider,
    DataProviderFactory,
    DataContext,
    query_data_by_dimension,
)

__all__ = [
    "DataProvider",
    "PersonDataProvider",
    "BatchDataProvider",
    "ProcessDataProvider",
    "WorkshopDataProvider",
    "TimeDataProvider",
    "DataProviderFactory",
    "DataContext",
    "query_data_by_dimension",
]
