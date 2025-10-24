"""
Customer Agent - Handles customer interactions and negotiations
"""

import sys
from datetime import datetime, timedelta
from typing import Any, Optional
from pydantic import BaseModel
from pydantic_ai import Agent, RunContext
from loguru import logger

from src.database import create_engine
from src.test_config import create_test_agent


class CustomerProfile(BaseModel):
    """Customer profile and preferences"""
    customer_id: str
    name: str
    company: Optional[str] = None
    customer_type: str = "standard"  # standard, premium, bulk
    negotiation_style: str = "cooperative"  # cooperative, aggressive, analytical
    budget_range: Optional[tuple[float, float]] = None
    preferred_delivery_time: int = 7  # days
    loyalty_discount: float = 0.0
    total_orders: int = 0
    total_spent: float = 0.0


class NegotiationContext(BaseModel):
    """Context for negotiation process"""
    original_request: str
    initial_quote: Optional[dict] = None
    counter_offers: list[dict] = []
    negotiation_round: int = 0
    max_rounds: int = 3
    customer_satisfaction: float = 0.5
    deal_probability: float = 0.5


class CustomerDependencies(BaseModel):
    """Dependencies for Customer Agent"""
    db_path: str = "munder_difflin.db"
    current_date: str = "2025-01-15"
    db_engine: Any = None


# Create Customer Agent
if "pytest" in sys.modules:
    customer_agent = create_test_agent(
        "You are the Customer Agent for Munder Difflin Paper Company. "
        "You represent the customer's interests and negotiate on their behalf. "
        "You analyze quotes, make counter-offers, and ensure the customer gets the best deal. "
        "You understand customer psychology and business needs.",
        CustomerDependencies
    )
else:
    customer_agent = Agent(
        model="openai:gpt-4o-mini",
        system_prompt="You are the Customer Agent for Munder Difflin Paper Company. "
        "You represent the customer's interests and negotiate on their behalf. "
        "You analyze quotes, make counter-offers, and ensure the customer gets the best deal. "
        "You understand customer psychology and business needs.",
        deps_type=CustomerDependencies,
    )


@customer_agent.tool
async def analyze_customer_profile(
    ctx: RunContext[CustomerDependencies], customer_id: str
) -> dict:
    """
    Analyze customer profile and history to understand their preferences and negotiation style.
    
    Args:
        customer_id: Customer identifier
        
    Returns:
        Customer profile with preferences and history
    """
    logger.info(f"🔍 Analyzing customer profile: {customer_id}")
    
    # In a real system, this would query customer database
    # For now, we'll create a realistic profile based on customer_id
    profiles = {
        "CUST001": CustomerProfile(
            customer_id="CUST001",
            name="Sarah Johnson",
            company="TechCorp Solutions",
            customer_type="premium",
            negotiation_style="analytical",
            budget_range=(5000, 15000),
            preferred_delivery_time=5,
            loyalty_discount=0.05,
            total_orders=12,
            total_spent=45000.0
        ),
        "CUST002": CustomerProfile(
            customer_id="CUST002",
            name="Mike Rodriguez",
            company="PrintWorks Inc",
            customer_type="bulk",
            negotiation_style="aggressive",
            budget_range=(20000, 50000),
            preferred_delivery_time=3,
            loyalty_discount=0.08,
            total_orders=8,
            total_spent=120000.0
        ),
        "CUST003": CustomerProfile(
            customer_id="CUST003",
            name="Lisa Chen",
            company="Event Planners Pro",
            customer_type="standard",
            negotiation_style="cooperative",
            budget_range=(1000, 5000),
            preferred_delivery_time=7,
            loyalty_discount=0.02,
            total_orders=3,
            total_spent=8500.0
        )
    }
    
    profile = profiles.get(customer_id, CustomerProfile(
        customer_id=customer_id,
        name="New Customer",
        customer_type="standard",
        negotiation_style="cooperative"
    ))
    
    logger.success(f"✅ Customer profile analyzed: {profile.name} ({profile.customer_type})")
    return profile.model_dump()


@customer_agent.tool
async def evaluate_quote(
    ctx: RunContext[CustomerDependencies], 
    quote: dict, 
    customer_profile: dict
) -> dict:
    """
    Evaluate a quote from the customer's perspective and determine negotiation strategy.
    
    Args:
        quote: Quote details from quoting agent
        customer_profile: Customer profile and preferences
        
    Returns:
        Evaluation with negotiation recommendations
    """
    logger.info(f"💰 Evaluating quote for {customer_profile['name']}")
    
    # Analyze quote against customer preferences
    total_price = quote.get('total_price', 0)
    budget_min, budget_max = customer_profile.get('budget_range', (0, float('inf')))
    
    # Calculate satisfaction score
    satisfaction = 0.5
    
    # Price evaluation
    if budget_max and total_price <= budget_max:
        price_score = 1.0 - (total_price - budget_min) / (budget_max - budget_min)
        satisfaction += price_score * 0.4
    
    # Delivery time evaluation
    delivery_days = quote.get('delivery_days', 7)
    preferred_delivery = customer_profile.get('preferred_delivery_time', 7)
    if delivery_days <= preferred_delivery:
        satisfaction += 0.3
    
    # Discount evaluation
    discount = quote.get('discount_percentage', 0)
    loyalty_discount = customer_profile.get('loyalty_discount', 0)
    if discount >= loyalty_discount:
        satisfaction += 0.2
    
    # Determine negotiation strategy
    negotiation_style = customer_profile.get('negotiation_style', 'cooperative')
    
    if satisfaction >= 0.8:
        strategy = "accept"
        message = "This quote meets our expectations. We're ready to proceed."
    elif satisfaction >= 0.6:
        strategy = "minor_negotiation"
        message = "The quote is good, but we'd like to discuss some terms."
    else:
        strategy = "major_negotiation"
        message = "We need to negotiate better terms to make this work."
    
    evaluation = {
        "satisfaction_score": satisfaction,
        "strategy": strategy,
        "message": message,
        "price_acceptable": total_price <= budget_max if budget_max else True,
        "delivery_acceptable": delivery_days <= preferred_delivery,
        "discount_acceptable": discount >= loyalty_discount,
        "negotiation_points": []
    }
    
    # Add specific negotiation points
    if total_price > budget_min and budget_min:
        evaluation["negotiation_points"].append(f"Price is above our minimum budget of ${budget_min:,.2f}")
    
    if delivery_days > preferred_delivery:
        evaluation["negotiation_points"].append(f"Delivery time of {delivery_days} days exceeds our preferred {preferred_delivery} days")
    
    if discount < loyalty_discount:
        evaluation["negotiation_points"].append(f"Discount of {discount:.1%} is below our loyalty discount of {loyalty_discount:.1%}")
    
    logger.success(f"✅ Quote evaluated: {strategy} (satisfaction: {satisfaction:.2f})")
    return evaluation


@customer_agent.tool
async def make_counter_offer(
    ctx: RunContext[CustomerDependencies],
    original_quote: dict,
    customer_profile: dict,
    evaluation: dict
) -> dict:
    """
    Make a counter-offer based on customer preferences and negotiation style.
    
    Args:
        original_quote: Original quote from quoting agent
        customer_profile: Customer profile
        evaluation: Quote evaluation results
        
    Returns:
        Counter-offer details
    """
    logger.info(f"🤝 Making counter-offer for {customer_profile['name']}")
    
    negotiation_style = customer_profile.get('negotiation_style', 'cooperative')
    customer_type = customer_profile.get('customer_type', 'standard')
    
    # Base counter-offer on original quote
    counter_offer = original_quote.copy()
    
    # Adjust based on negotiation style
    if negotiation_style == "aggressive":
        # Ask for 15-20% discount
        discount_increase = 0.15
        delivery_reduction = 2
    elif negotiation_style == "analytical":
        # Ask for 8-12% discount with data-driven reasoning
        discount_increase = 0.10
        delivery_reduction = 1
    else:  # cooperative
        # Ask for 5-8% discount
        discount_increase = 0.06
        delivery_reduction = 1
    
    # Apply customer type multiplier
    if customer_type == "premium":
        discount_increase *= 1.2
    elif customer_type == "bulk":
        discount_increase *= 1.5
    
    # Calculate new discount
    current_discount = original_quote.get('discount_percentage', 0) / 100
    new_discount = min(current_discount + discount_increase, 0.25)  # Cap at 25%
    
    # Recalculate pricing
    subtotal = original_quote.get('subtotal', 0)
    new_discount_amount = subtotal * new_discount
    new_total = subtotal - new_discount_amount
    
    counter_offer.update({
        'discount_percentage': new_discount * 100,
        'discount_amount': new_discount_amount,
        'total_price': new_total,
        'delivery_days': max(original_quote.get('delivery_days', 7) - delivery_reduction, 3),
        'counter_offer_reason': f"Based on our {customer_type} status and {negotiation_style} negotiation style",
        'customer_justification': evaluation.get('negotiation_points', [])
    })
    
    logger.success(f"✅ Counter-offer made: ${new_total:,.2f} (discount: {new_discount:.1%})")
    return counter_offer


@customer_agent.tool
async def finalize_deal(
    ctx: RunContext[CustomerDependencies],
    final_quote: dict,
    customer_profile: dict
) -> dict:
    """
    Finalize the deal and prepare for order processing.
    
    Args:
        final_quote: Final agreed quote
        customer_profile: Customer profile
        
    Returns:
        Deal finalization details
    """
    logger.info(f"✅ Finalizing deal for {customer_profile['name']}")
    
    deal = {
        'customer_id': customer_profile['customer_id'],
        'customer_name': customer_profile['name'],
        'company': customer_profile.get('company', ''),
        'quote_id': final_quote.get('request_id', ''),
        'total_amount': final_quote.get('total_price', 0),
        'discount_applied': final_quote.get('discount_percentage', 0),
        'delivery_days': final_quote.get('delivery_days', 7),
        'deal_status': 'finalized',
        'finalized_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'customer_satisfaction': 0.9,  # High satisfaction for finalized deals
        'next_steps': [
            "Order will be processed by Sales Agent",
            f"Delivery scheduled for {final_quote.get('delivery_days', 7)} days",
            "Invoice will be generated",
            "Customer will receive confirmation email"
        ]
    }
    
    logger.success(f"✅ Deal finalized: ${deal['total_amount']:,.2f} for {deal['customer_name']}")
    return deal


async def negotiate_with_customer(
    customer_id: str,
    original_request: str,
    initial_quote: dict,
    db_path: str = "munder_difflin.db"
) -> dict:
    """
    Main negotiation function that handles the entire customer interaction process.
    
    Args:
        customer_id: Customer identifier
        original_request: Original customer request
        initial_quote: Initial quote from quoting agent
        db_path: Database path
        
    Returns:
        Final negotiation result
    """
    logger.info(f"🤝 Starting negotiation with customer {customer_id}")
    
    try:
        # Step 1: Analyze customer profile
        profile_result = await customer_agent.run(
            f"Analyze customer profile for {customer_id}",
            deps=CustomerDependencies(db_path=db_path)
        )
        customer_profile = profile_result.output
        
        # Step 2: Evaluate the initial quote
        evaluation_result = await customer_agent.run(
            f"Evaluate this quote for customer {customer_id}: {initial_quote}",
            deps=CustomerDependencies(db_path=db_path)
        )
        evaluation = evaluation_result.output
        
        # Step 3: Make counter-offer if needed
        if evaluation.get('strategy') != 'accept':
            counter_offer_result = await customer_agent.run(
                f"Make a counter-offer for customer {customer_id} based on their preferences",
                deps=CustomerDependencies(db_path=db_path)
            )
            counter_offer = counter_offer_result.output
            
            # Step 4: Finalize the deal
            finalize_result = await customer_agent.run(
                f"Finalize the deal for customer {customer_id}",
                deps=CustomerDependencies(db_path=db_path)
            )
            final_deal = finalize_result.output
            
            return {
                'negotiation_successful': True,
                'customer_profile': customer_profile,
                'initial_evaluation': evaluation,
                'counter_offer': counter_offer,
                'final_deal': final_deal,
                'negotiation_rounds': 2
            }
        else:
            # Customer accepts initial quote
            finalize_result = await customer_agent.run(
                f"Finalize the deal for customer {customer_id} - they accepted the initial quote",
                deps=CustomerDependencies(db_path=db_path)
            )
            final_deal = finalize_result.output
            
            return {
                'negotiation_successful': True,
                'customer_profile': customer_profile,
                'initial_evaluation': evaluation,
                'counter_offer': None,
                'final_deal': final_deal,
                'negotiation_rounds': 1
            }
            
    except Exception as e:
        logger.error(f"❌ Error in negotiation: {e}")
        return {
            'negotiation_successful': False,
            'error': str(e),
            'customer_profile': None,
            'initial_evaluation': None,
            'counter_offer': None,
            'final_deal': None,
            'negotiation_rounds': 0
        }
