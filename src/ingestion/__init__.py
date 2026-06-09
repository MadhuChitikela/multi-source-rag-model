from .ingest_spy import ingest_spy_data
from .ingest_products import (
    ingest_amazon_products,
    ingest_ecommerce_products,
    ingest_kindred_deals
)
from .ingest_documents import (
    ingest_northwind_purchase_orders,
    ingest_user_manual_links
)
from .ingest_news import ingest_financial_news

__all__ = [
    'ingest_spy_data',
    'ingest_amazon_products',
    'ingest_ecommerce_products',
    'ingest_kindred_deals',
    'ingest_northwind_purchase_orders',
    'ingest_user_manual_links',
    'ingest_financial_news'
]
