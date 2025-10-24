"""
Database layer do sistema Munder Difflin.
Contém todas as funções de interação com o banco de dados SQLite.
"""

import ast
from dataclasses import dataclass
from datetime import datetime, timedelta

import numpy as np
import pandas as pd
from sqlalchemy import Engine, create_engine
from sqlalchemy.sql import text

from src.config import DATA_DIR, BusinessRules, db_config
from src.utils.logging_config import logger

# ============================================================================
# DATABASE ENGINE
# ============================================================================

db_engine = create_engine(db_config.url)
logger.info(f"Database engine criado: {db_config.url}")


# ============================================================================
# CONTEXTO COMPARTILHADO PARA OS AGENTS
# ============================================================================


@dataclass
class DatabaseContext:
    """
    Contexto compartilhado entre todos os agents e tools.

    Usado para dependency injection no Pydantic-AI.
    Garante que todas as tools tenham acesso ao banco e data atual.
    """

    db_engine: Engine
    current_date: str  # ISO format: YYYY-MM-DD

    def __post_init__(self):
        """Valida o formato da data."""
        try:
            datetime.fromisoformat(self.current_date)
        except ValueError:
            raise ValueError(
                f"current_date deve estar no formato ISO (YYYY-MM-DD), "
                f"recebido: {self.current_date}"
            )


# ============================================================================
# LISTA DE PRODUTOS (do project_starter.py)
# ============================================================================

paper_supplies = [
    # Paper Types (priced per sheet unless specified)
    {"item_name": "A4 paper", "category": "paper", "unit_price": 0.05},
    {"item_name": "Letter-sized paper", "category": "paper", "unit_price": 0.06},
    {"item_name": "Cardstock", "category": "paper", "unit_price": 0.15},
    {"item_name": "Colored paper", "category": "paper", "unit_price": 0.10},
    {"item_name": "Glossy paper", "category": "paper", "unit_price": 0.20},
    {"item_name": "Matte paper", "category": "paper", "unit_price": 0.18},
    {"item_name": "Recycled paper", "category": "paper", "unit_price": 0.08},
    {"item_name": "Eco-friendly paper", "category": "paper", "unit_price": 0.12},
    {"item_name": "Poster paper", "category": "paper", "unit_price": 0.25},
    {"item_name": "Banner paper", "category": "paper", "unit_price": 0.30},
    {"item_name": "Kraft paper", "category": "paper", "unit_price": 0.10},
    {"item_name": "Construction paper", "category": "paper", "unit_price": 0.07},
    {"item_name": "Wrapping paper", "category": "paper", "unit_price": 0.15},
    {"item_name": "Glitter paper", "category": "paper", "unit_price": 0.22},
    {"item_name": "Decorative paper", "category": "paper", "unit_price": 0.18},
    {"item_name": "Letterhead paper", "category": "paper", "unit_price": 0.12},
    {"item_name": "Legal-size paper", "category": "paper", "unit_price": 0.08},
    {"item_name": "Crepe paper", "category": "paper", "unit_price": 0.05},
    {"item_name": "Photo paper", "category": "paper", "unit_price": 0.25},
    {"item_name": "Uncoated paper", "category": "paper", "unit_price": 0.06},
    {"item_name": "Butcher paper", "category": "paper", "unit_price": 0.10},
    {"item_name": "Heavyweight paper", "category": "paper", "unit_price": 0.20},
    {"item_name": "Standard copy paper", "category": "paper", "unit_price": 0.04},
    {"item_name": "Bright-colored paper", "category": "paper", "unit_price": 0.12},
    {"item_name": "Patterned paper", "category": "paper", "unit_price": 0.15},
    # Product Types (priced per unit)
    {"item_name": "Paper plates", "category": "product", "unit_price": 0.10},
    {"item_name": "Paper cups", "category": "product", "unit_price": 0.08},
    {"item_name": "Paper napkins", "category": "product", "unit_price": 0.02},
    {"item_name": "Disposable cups", "category": "product", "unit_price": 0.10},
    {"item_name": "Table covers", "category": "product", "unit_price": 1.50},
    {"item_name": "Envelopes", "category": "product", "unit_price": 0.05},
    {"item_name": "Sticky notes", "category": "product", "unit_price": 0.03},
    {"item_name": "Notepads", "category": "product", "unit_price": 2.00},
    {"item_name": "Invitation cards", "category": "product", "unit_price": 0.50},
    {"item_name": "Flyers", "category": "product", "unit_price": 0.15},
    {"item_name": "Party streamers", "category": "product", "unit_price": 0.05},
    {
        "item_name": "Decorative adhesive tape (washi tape)",
        "category": "product",
        "unit_price": 0.20,
    },
    {"item_name": "Paper party bags", "category": "product", "unit_price": 0.25},
    {"item_name": "Name tags with lanyards", "category": "product", "unit_price": 0.75},
    {"item_name": "Presentation folders", "category": "product", "unit_price": 0.50},
    # Large-format items (priced per unit)
    {
        "item_name": "Large poster paper (24x36 inches)",
        "category": "large_format",
        "unit_price": 1.00,
    },
    {
        "item_name": "Rolls of banner paper (36-inch width)",
        "category": "large_format",
        "unit_price": 2.50,
    },
    # Specialty papers
    {"item_name": "100 lb cover stock", "category": "specialty", "unit_price": 0.50},
    {"item_name": "80 lb text paper", "category": "specialty", "unit_price": 0.40},
    {"item_name": "250 gsm cardstock", "category": "specialty", "unit_price": 0.30},
    {"item_name": "220 gsm poster paper", "category": "specialty", "unit_price": 0.35},
]


# ============================================================================
# FUNÇÕES DE INICIALIZAÇÃO (do project_starter.py)
# ============================================================================


def generate_sample_inventory(
    paper_supplies: list, coverage: float = 0.4, seed: int = 137
) -> pd.DataFrame:
    """
    Gera inventário para exatamente uma % especificada dos itens.

    Args:
        paper_supplies: Lista de dicts com item_name, category, unit_price
        coverage: Fração de itens a incluir (padrão 40%)
        seed: Seed para reprodutibilidade

    Returns:
        DataFrame com: item_name, category, unit_price, current_stock, min_stock_level
    """
    logger.debug(f"Gerando inventário: coverage={coverage}, seed={seed}")

    np.random.seed(seed)

    num_items = int(len(paper_supplies) * coverage)
    selected_indices = np.random.choice(range(len(paper_supplies)), size=num_items, replace=False)

    selected_items = [paper_supplies[i] for i in selected_indices]

    inventory = []
    for item in selected_items:
        inventory.append(
            {
                "item_name": item["item_name"],
                "category": item["category"],
                "unit_price": item["unit_price"],
                "current_stock": np.random.randint(200, 800),
                "min_stock_level": np.random.randint(50, 150),
            }
        )

    logger.info(f"Inventário gerado: {len(inventory)} itens")
    return pd.DataFrame(inventory)


def init_database(engine: Engine = None, seed: int = None) -> Engine:
    """
    Inicializa TODAS as tabelas do banco e carrega dados iniciais.

    ⚠️ ATENÇÃO: Esta função RESETA o banco completamente!

    Args:
        engine: SQLAlchemy engine (usa db_engine global se None)
        seed: Seed para geração de inventário (usa config se None)

    Returns:
        Engine do banco de dados
    """
    if engine is None:
        engine = db_engine
    if seed is None:
        seed = db_config.seed

    logger.warning("Inicializando database - TODOS OS DADOS SERÃO RESETADOS!")

    try:
        # 1. Criar tabela de transactions
        transactions_schema = pd.DataFrame(
            {
                "id": [],
                "item_name": [],
                "transaction_type": [],
                "units": [],
                "price": [],
                "transaction_date": [],
            }
        )
        transactions_schema.to_sql("transactions", engine, if_exists="replace", index=False)
        logger.debug("Tabela 'transactions' criada")

        initial_date = BusinessRules.INITIAL_DATE

        # 2. Carregar quote_requests
        quote_requests_path = DATA_DIR / "quote_requests.csv"
        quote_requests_df = pd.read_csv(quote_requests_path)
        quote_requests_df["id"] = range(1, len(quote_requests_df) + 1)
        quote_requests_df.to_sql("quote_requests", engine, if_exists="replace", index=False)
        logger.debug(f"Tabela 'quote_requests' carregada: {len(quote_requests_df)} registros")

        # 3. Carregar quotes
        quotes_path = DATA_DIR / "quotes.csv"
        quotes_df = pd.read_csv(quotes_path)
        quotes_df["request_id"] = range(1, len(quotes_df) + 1)
        quotes_df["order_date"] = initial_date

        if "request_metadata" in quotes_df.columns:
            quotes_df["request_metadata"] = quotes_df["request_metadata"].apply(
                lambda x: ast.literal_eval(x) if isinstance(x, str) else x
            )
            quotes_df["job_type"] = quotes_df["request_metadata"].apply(
                lambda x: x.get("job_type", "")
            )
            quotes_df["order_size"] = quotes_df["request_metadata"].apply(
                lambda x: x.get("order_size", "")
            )
            quotes_df["event_type"] = quotes_df["request_metadata"].apply(
                lambda x: x.get("event_type", "")
            )

        quotes_df = quotes_df[
            [
                "request_id",
                "total_amount",
                "quote_explanation",
                "order_date",
                "job_type",
                "order_size",
                "event_type",
            ]
        ]
        quotes_df.to_sql("quotes", engine, if_exists="replace", index=False)
        logger.debug(f"Tabela 'quotes' carregada: {len(quotes_df)} registros")

        # 4. Gerar e carregar inventário
        inventory_df = generate_sample_inventory(paper_supplies, seed=seed)

        initial_transactions = []

        # Cash inicial (transação dummy)
        initial_transactions.append(
            {
                "item_name": None,
                "transaction_type": "sales",
                "units": None,
                "price": BusinessRules.INITIAL_CASH,
                "transaction_date": initial_date,
            }
        )

        # Stock inicial para cada item
        for _, item in inventory_df.iterrows():
            initial_transactions.append(
                {
                    "item_name": item["item_name"],
                    "transaction_type": "stock_orders",
                    "units": item["current_stock"],
                    "price": item["current_stock"] * item["unit_price"],
                    "transaction_date": initial_date,
                }
            )

        pd.DataFrame(initial_transactions).to_sql(
            "transactions", engine, if_exists="append", index=False
        )
        logger.debug(f"Transações iniciais criadas: {len(initial_transactions)}")

        inventory_df.to_sql("inventory", engine, if_exists="replace", index=False)
        logger.debug(f"Tabela 'inventory' carregada: {len(inventory_df)} itens")

        logger.success("Database inicializado com sucesso!")
        return engine

    except Exception as e:
        logger.error(f"Erro ao inicializar database: {e}")
        raise


# ============================================================================
# FUNÇÕES DE TRANSAÇÃO (do project_starter.py)
# ============================================================================


def create_transaction(
    item_name: str,
    transaction_type: str,
    quantity: int,
    price: float,
    date: str | datetime,
    engine: Engine = None,
) -> int:
    """
    Registra uma transação de compra ou venda.

    Args:
        item_name: Nome do item
        transaction_type: 'stock_orders' (compra) ou 'sales' (venda)
        quantity: Quantidade de unidades
        price: Preço TOTAL da transação
        date: Data no formato ISO ou datetime
        engine: Engine do banco (usa global se None)

    Returns:
        ID da transação criada

    Raises:
        ValueError: Se transaction_type inválido
    """
    if engine is None:
        engine = db_engine

    date_str = date.isoformat() if isinstance(date, datetime) else date

    if transaction_type not in {"stock_orders", "sales"}:
        raise ValueError(
            f"transaction_type deve ser 'stock_orders' ou 'sales', recebido: {transaction_type}"
        )

    logger.debug(
        f"Criando transação: {transaction_type} | {item_name} | qty={quantity} | price=${price:.2f}"
    )

    try:
        transaction = pd.DataFrame(
            [
                {
                    "item_name": item_name,
                    "transaction_type": transaction_type,
                    "units": quantity,
                    "price": price,
                    "transaction_date": date_str,
                }
            ]
        )

        transaction.to_sql("transactions", engine, if_exists="append", index=False)

        result = pd.read_sql("SELECT last_insert_rowid() as id", engine)
        tx_id = int(result.iloc[0]["id"])

        logger.info(f"Transação criada: ID={tx_id}")
        return tx_id

    except Exception as e:
        logger.error(f"Erro ao criar transação: {e}")
        raise


# ============================================================================
# FUNÇÕES DE CONSULTA DE INVENTÁRIO (do project_starter.py)
# ============================================================================


def get_all_inventory(as_of_date: str, engine: Engine = None) -> dict[str, int]:
    """
    Retorna snapshot de TODOS os itens em estoque.

    Calcula: (SUM stock_orders) - (SUM sales) até a data.
    Retorna apenas itens com stock > 0.

    Args:
        as_of_date: Data no formato ISO (YYYY-MM-DD)
        engine: Engine do banco (usa global se None)

    Returns:
        Dict[item_name, quantidade] - Ex: {"A4 paper": 650, "Cardstock": 400}
    """
    if engine is None:
        engine = db_engine

    logger.debug(f"Consultando inventário completo em {as_of_date}")

    query = """
        SELECT
            item_name,
            SUM(CASE
                WHEN transaction_type = 'stock_orders' THEN units
                WHEN transaction_type = 'sales' THEN -units
                ELSE 0
            END) as stock
        FROM transactions
        WHERE item_name IS NOT NULL
        AND transaction_date <= :as_of_date
        GROUP BY item_name
        HAVING stock > 0
    """

    result = pd.read_sql(query, engine, params={"as_of_date": as_of_date})
    inventory = dict(zip(result["item_name"], result["stock"]))

    logger.debug(f"Inventário consultado: {len(inventory)} itens em estoque")
    return inventory


def get_stock_level(
    item_name: str, as_of_date: str | datetime, engine: Engine = None
) -> pd.DataFrame:
    """
    Retorna o nível de estoque de um item específico.

    Args:
        item_name: Nome exato do item
        as_of_date: Data no formato ISO ou datetime
        engine: Engine do banco (usa global se None)

    Returns:
        DataFrame com colunas: [item_name, current_stock]
    """
    if engine is None:
        engine = db_engine

    if isinstance(as_of_date, datetime):
        as_of_date = as_of_date.isoformat()

    logger.debug(f"Consultando stock de '{item_name}' em {as_of_date}")

    stock_query = """
        SELECT
            item_name,
            COALESCE(SUM(CASE
                WHEN transaction_type = 'stock_orders' THEN units
                WHEN transaction_type = 'sales' THEN -units
                ELSE 0
            END), 0) AS current_stock
        FROM transactions
        WHERE item_name = :item_name
        AND transaction_date <= :as_of_date
    """

    result = pd.read_sql(
        stock_query,
        engine,
        params={"item_name": item_name, "as_of_date": as_of_date},
    )

    stock = int(result["current_stock"].iloc[0]) if not result.empty else 0
    logger.debug(f"Stock de '{item_name}': {stock} unidades")

    return result


# ============================================================================
# FUNÇÕES FINANCEIRAS (do project_starter.py)
# ============================================================================


def get_cash_balance(as_of_date: str | datetime, engine: Engine = None) -> float:
    """
    Calcula saldo de caixa: (SUM sales) - (SUM stock_orders).

    Args:
        as_of_date: Data no formato ISO ou datetime
        engine: Engine do banco (usa global se None)

    Returns:
        Saldo de caixa em float
    """
    if engine is None:
        engine = db_engine

    if isinstance(as_of_date, datetime):
        as_of_date = as_of_date.isoformat()

    logger.debug(f"Calculando cash balance em {as_of_date}")

    try:
        transactions = pd.read_sql(
            "SELECT * FROM transactions WHERE transaction_date <= :as_of_date",
            engine,
            params={"as_of_date": as_of_date},
        )

        if not transactions.empty:
            total_sales = transactions.loc[
                transactions["transaction_type"] == "sales", "price"
            ].sum()
            total_purchases = transactions.loc[
                transactions["transaction_type"] == "stock_orders", "price"
            ].sum()
            balance = float(total_sales - total_purchases)
            logger.debug(f"Cash balance: ${balance:.2f}")
            return balance

        return 0.0

    except Exception as e:
        logger.error(f"Erro ao calcular cash balance: {e}")
        return 0.0


def generate_financial_report(as_of_date: str | datetime, engine: Engine = None) -> dict:
    """
    Gera relatório financeiro completo.

    Returns dict com:
    - as_of_date: Data do relatório
    - cash_balance: Saldo de caixa
    - inventory_value: Valor do estoque
    - total_assets: Cash + Inventory
    - inventory_summary: Lista detalhada por item
    - top_selling_products: Top 5 produtos
    """
    if engine is None:
        engine = db_engine

    if isinstance(as_of_date, datetime):
        as_of_date = as_of_date.isoformat()

    logger.debug(f"Gerando relatório financeiro em {as_of_date}")

    cash = get_cash_balance(as_of_date, engine)

    inventory_df = pd.read_sql("SELECT * FROM inventory", engine)
    inventory_value = 0.0
    inventory_summary = []

    for _, item in inventory_df.iterrows():
        stock_info = get_stock_level(item["item_name"], as_of_date, engine)
        stock = stock_info["current_stock"].iloc[0]
        item_value = stock * item["unit_price"]
        inventory_value += item_value

        inventory_summary.append(
            {
                "item_name": item["item_name"],
                "stock": stock,
                "unit_price": item["unit_price"],
                "value": item_value,
            }
        )

    top_sales_query = """
        SELECT item_name, SUM(units) as total_units, SUM(price) as total_revenue
        FROM transactions
        WHERE transaction_type = 'sales' AND transaction_date <= :date
        GROUP BY item_name
        ORDER BY total_revenue DESC
        LIMIT 5
    """
    top_sales = pd.read_sql(top_sales_query, engine, params={"date": as_of_date})
    top_selling_products = top_sales.to_dict(orient="records")

    report = {
        "as_of_date": as_of_date,
        "cash_balance": cash,
        "inventory_value": inventory_value,
        "total_assets": cash + inventory_value,
        "inventory_summary": inventory_summary,
        "top_selling_products": top_selling_products,
    }

    logger.info(
        f"Relatório gerado: Cash=${cash:.2f}, "
        f"Inventory=${inventory_value:.2f}, "
        f"Total=${cash + inventory_value:.2f}"
    )

    return report


# ============================================================================
# FUNÇÕES DE SUPORTE (do project_starter.py)
# ============================================================================


def get_supplier_delivery_date(input_date_str: str, quantity: int) -> str:
    """
    Estima data de entrega do FORNECEDOR baseado na quantidade.

    Regras:
    - ≤ 10 units: same day (0 dias)
    - 11-100 units: 1 dia
    - 101-1000 units: 4 dias
    - > 1000 units: 7 dias

    Args:
        input_date_str: Data de pedido (ISO format)
        quantity: Quantidade pedida

    Returns:
        Data de entrega estimada (ISO format)
    """
    logger.debug(f"Calculando delivery date: qty={quantity}, date={input_date_str}")

    try:
        input_date_dt = datetime.fromisoformat(input_date_str.split("T")[0])
    except (ValueError, TypeError):
        logger.warning(f"Data inválida '{input_date_str}', usando data atual")
        input_date_dt = datetime.now()

    if quantity <= 10:
        days = 0
    elif quantity <= 100:
        days = 1
    elif quantity <= 1000:
        days = 4
    else:
        days = 7

    delivery_date_dt = input_date_dt + timedelta(days=days)
    delivery_date = delivery_date_dt.strftime("%Y-%m-%d")

    logger.debug(f"Delivery date: {delivery_date} ({days} dias)")
    return delivery_date


def search_quote_history(
    search_terms: list[str], limit: int = 5, engine: Engine = None
) -> list[dict]:
    """
    Busca cotações históricas similares por keywords.

    Args:
        search_terms: Lista de termos de busca
        limit: Máximo de resultados
        engine: Engine do banco (usa global se None)

    Returns:
        Lista de dicts com cotações similares
    """
    if engine is None:
        engine = db_engine

    logger.debug(f"Buscando quotes com termos: {search_terms}")

    conditions = []
    params = {}

    for i, term in enumerate(search_terms):
        param_name = f"term_{i}"
        conditions.append(
            f"(LOWER(qr.response) LIKE :{param_name} OR "
            f"LOWER(q.quote_explanation) LIKE :{param_name})"
        )
        params[param_name] = f"%{term.lower()}%"

    where_clause = " AND ".join(conditions) if conditions else "1=1"

    query = f"""
        SELECT
            qr.response AS original_request,
            q.total_amount,
            q.quote_explanation,
            q.job_type,
            q.order_size,
            q.event_type,
            q.order_date
        FROM quotes q
        JOIN quote_requests qr ON q.request_id = qr.id
        WHERE {where_clause}
        ORDER BY q.order_date DESC
        LIMIT {limit}
    """

    with engine.connect() as conn:
        result = conn.execute(text(query), params)
        quotes = [dict(row) for row in result]

    logger.debug(f"Quotes encontradas: {len(quotes)}")
    return quotes


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    # Context
    "DatabaseContext",
    "db_engine",
    "paper_supplies",
    # Init
    "generate_sample_inventory",
    "init_database",
    # Transactions
    "create_transaction",
    # Inventory
    "get_all_inventory",
    "get_stock_level",
    # Finance
    "get_cash_balance",
    "generate_financial_report",
    # Support
    "get_supplier_delivery_date",
    "search_quote_history",
]
