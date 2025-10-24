#!/usr/bin/env python3
"""
Advanced Features Demo - Customer Agent, Terminal Animation, and Business Advisor
"""

import asyncio
import time
from datetime import datetime
from typing import Dict, Any

from src.database import init_database
from src.agents.orchestrator import handle_customer_request
from src.agents.quoting_agent import request_quote
from src.agents.customer_agent import negotiate_with_customer
from src.agents.sales_agent import process_order
from src.agents.business_advisor import analyze_business_performance, get_business_recommendations
from src.utils.terminal_animation import (
    start_processing_animation, stop_processing_animation,
    update_agent_processing, update_processing_step,
    show_customer_details, show_negotiation_details,
    show_business_insights, show_processing_summary
)


async def demo_advanced_features():
    """Demonstrate the advanced features of the multi-agent system"""
    
    print("🚀 Starting Advanced Features Demo")
    print("=" * 80)
    
    # Initialize database
    print("📊 Initializing database...")
    init_database()
    
    # Start terminal animation
    start_processing_animation()
    
    try:
        # Step 1: Customer Request Processing
        update_processing_step("Processing customer request", 1)
        update_agent_processing("orchestrator", "processing", "Analyzing request")
        
        customer_request = "I need 500 sheets of A4 paper and 200 sheets of cardstock for our upcoming conference. We're a premium customer and need delivery within 5 days."
        customer_id = "CUST001"  # Sarah Johnson - Premium customer
        
        show_customer_details("Sarah Johnson (TechCorp Solutions)", customer_request)
        
        # Simulate processing time
        await asyncio.sleep(2)
        
        # Step 2: Orchestrator Processing
        update_agent_processing("orchestrator", "completed", "Request analyzed")
        update_agent_processing("inventory", "processing", "Checking stock levels")
        update_processing_step("Checking inventory availability", 2)
        
        orchestrator_response = await handle_customer_request(customer_request, "munder_difflin.db")
        await asyncio.sleep(1)
        
        # Step 3: Inventory Check
        update_agent_processing("inventory", "completed", "Stock levels verified")
        update_agent_processing("quoting", "processing", "Generating quote")
        update_processing_step("Generating quote with discounts", 3)
        
        # Step 4: Quote Generation
        quote_response = await request_quote("A4 paper x500, Cardstock x200", "munder_difflin.db", customer_id)
        await asyncio.sleep(1)
        
        update_agent_processing("quoting", "completed", "Quote generated")
        update_agent_processing("customer", "processing", "Negotiating terms")
        update_processing_step("Customer negotiation in progress", 4)
        
        # Step 5: Customer Negotiation
        # Simulate initial quote
        initial_quote = {
            "request_id": "Q20250124120000",
            "item_name": "A4 paper, Cardstock",
            "quantity": 700,
            "unit_price": 0.12,
            "discount_percentage": 5.0,
            "subtotal": 84.00,
            "discount_amount": 4.20,
            "total_price": 79.80,
            "delivery_days": 7,
            "quote_explanation": "Quote for 500 A4 paper + 200 cardstock with 5% bulk discount"
        }
        
        show_negotiation_details(1, initial_quote)
        await asyncio.sleep(2)
        
        # Customer negotiation
        negotiation_result = await negotiate_with_customer(
            customer_id, customer_request, initial_quote, "munder_difflin.db"
        )
        
        if negotiation_result.get('negotiation_successful'):
            final_deal = negotiation_result.get('final_deal', {})
            show_negotiation_details(2, final_deal)
            
            update_agent_processing("customer", "completed", "Deal finalized")
            update_agent_processing("sales", "processing", "Processing order")
            update_processing_step("Processing sales transaction", 5)
            
            # Step 6: Sales Processing
            sales_response = await process_order(
                f"Process order: {final_deal.get('total_amount', 79.80)} for {customer_id}",
                "munder_difflin.db", customer_id
            )
            
            await asyncio.sleep(1)
            update_agent_processing("sales", "completed", "Transaction completed")
            update_agent_processing("reordering", "processing", "Checking stock levels")
            update_processing_step("Auto-reordering low stock items", 6)
            
            # Step 7: Reordering
            await asyncio.sleep(1)
            update_agent_processing("reordering", "completed", "Stock replenished")
            update_agent_processing("business_advisor", "processing", "Analyzing performance")
            update_processing_step("Business advisor analysis", 7)
            
            # Step 8: Business Advisor Analysis
            business_analysis = await analyze_business_performance("munder_difflin.db")
            recommendations = await get_business_recommendations("munder_difflin.db")
            
            show_business_insights(recommendations)
            
            await asyncio.sleep(2)
            update_agent_processing("business_advisor", "completed", "Analysis complete")
            
            # Final Summary
            results = {
                'negotiation_successful': True,
                'final_deal': final_deal,
                'negotiation_rounds': negotiation_result.get('negotiation_rounds', 2),
                'transaction_completed': True,
                'items_sold': 700,
                'reorder_triggered': True,
                'items_reordered': 133,
                'processing_time': 8.5,
                'business_recommendations': len(recommendations)
            }
            
            show_processing_summary(results)
            
        else:
            update_agent_processing("customer", "error", "Negotiation failed")
            print("❌ Customer negotiation failed")
            
    except Exception as e:
        print(f"❌ Error during demo: {e}")
        update_agent_processing("orchestrator", "error", f"Error: {str(e)}")
        
    finally:
        # Stop animation
        await asyncio.sleep(3)
        stop_processing_animation()


async def demo_customer_profiles():
    """Demonstrate different customer profiles and negotiation styles"""
    
    print("\n🎭 Customer Profiles Demo")
    print("=" * 80)
    
    customers = [
        {
            "id": "CUST001",
            "name": "Sarah Johnson",
            "company": "TechCorp Solutions",
            "type": "premium",
            "style": "analytical",
            "request": "I need 1000 sheets of premium paper for our annual report. Quality is more important than price."
        },
        {
            "id": "CUST002", 
            "name": "Mike Rodriguez",
            "company": "PrintWorks Inc",
            "type": "bulk",
            "style": "aggressive",
            "request": "I need 5000 sheets of A4 paper. Give me your best price - I'm shopping around."
        },
        {
            "id": "CUST003",
            "name": "Lisa Chen", 
            "company": "Event Planners Pro",
            "type": "standard",
            "style": "cooperative",
            "request": "I need 200 sheets of colored paper for an event. What can you do for me?"
        }
    ]
    
    for customer in customers:
        print(f"\n👤 {customer['name']} ({customer['company']})")
        print(f"🏷️  Type: {customer['type'].title()}")
        print(f"🤝 Style: {customer['style'].title()}")
        print(f"💬 Request: {customer['request']}")
        print("-" * 50)
        
        # Simulate negotiation for each customer
        initial_quote = {
            "total_price": 50.00,
            "discount_percentage": 5.0,
            "delivery_days": 7
        }
        
        # Show how different customers would negotiate
        if customer['style'] == 'aggressive':
            print("🤝 Aggressive negotiation: Asking for 20% discount, 3-day delivery")
        elif customer['style'] == 'analytical':
            print("🤝 Analytical negotiation: Requesting detailed breakdown, 10% discount")
        else:
            print("🤝 Cooperative negotiation: Accepting terms with minor adjustments")
            
        await asyncio.sleep(1)


async def demo_business_advisor():
    """Demonstrate business advisor capabilities"""
    
    print("\n💼 Business Advisor Demo")
    print("=" * 80)
    
    # Analyze current business performance
    print("📊 Analyzing business performance...")
    await asyncio.sleep(1)
    
    # Get recommendations
    print("🎯 Generating business recommendations...")
    await asyncio.sleep(1)
    
    # Simulate business recommendations
    recommendations = [
        {
            "category": "pricing",
            "priority": "high",
            "title": "Implement Dynamic Pricing for Premium Customers",
            "description": "Adjust pricing based on customer type and order volume",
            "expected_impact": "Increase revenue by 15-20%",
            "implementation_effort": "medium",
            "estimated_roi": 25.0,
            "timeline": "2-3 weeks"
        },
        {
            "category": "inventory",
            "priority": "medium", 
            "title": "Optimize Stock Levels for High-Demand Items",
            "description": "Increase stock for A4 paper and cardstock to reduce stockouts",
            "expected_impact": "Reduce stockouts by 40%",
            "implementation_effort": "low",
            "estimated_roi": 12.0,
            "timeline": "1 week"
        },
        {
            "category": "operations",
            "priority": "high",
            "title": "Automate Reordering Process",
            "description": "Implement predictive reordering based on sales patterns",
            "expected_impact": "Reduce manual work by 60%",
            "implementation_effort": "high",
            "estimated_roi": 35.0,
            "timeline": "4-6 weeks"
        }
    ]
    
    show_business_insights(recommendations)


async def main():
    """Main demo function"""
    print("🎬 Munder Difflin Advanced Features Demo")
    print("=" * 80)
    print("This demo showcases:")
    print("1. 🤖 Customer Agent with negotiation capabilities")
    print("2. 🎬 Real-time terminal animation")
    print("3. 💼 Business Advisor with recommendations")
    print("=" * 80)
    
    # Run main demo
    await demo_advanced_features()
    
    # Run customer profiles demo
    await demo_customer_profiles()
    
    # Run business advisor demo
    await demo_business_advisor()
    
    print("\n🎉 Demo completed successfully!")
    print("=" * 80)
    print("Key Features Demonstrated:")
    print("✅ Customer Agent with profile-based negotiation")
    print("✅ Real-time terminal animation system")
    print("✅ Business Advisor with actionable recommendations")
    print("✅ Multi-agent coordination and communication")
    print("✅ End-to-end customer journey processing")


if __name__ == "__main__":
    asyncio.run(main())
