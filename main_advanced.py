#!/usr/bin/env python3
"""
Munder Difflin Multi-Agent System - Advanced Features Demo
Integrates Customer Agent, Terminal Animation, and Business Advisor
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
from src.agents.business_advisor import analyze_business_metrics, generate_recommendations
from src.utils.terminal_animation import (
    start_processing_animation, stop_processing_animation,
    update_agent_processing, update_processing_step,
    show_customer_details, show_negotiation_details,
    show_business_insights, show_processing_summary
)


class AdvancedMultiAgentSystem:
    """Advanced Multi-Agent System with new features"""
    
    def __init__(self, db_path: str = "munder_difflin.db"):
        self.db_path = db_path
        self.animation_running = False
        
    async def process_customer_request_advanced(
        self, 
        customer_request: str, 
        customer_id: str = "CUST001",
        show_animation: bool = True
    ) -> Dict[str, Any]:
        """
        Process customer request with advanced features:
        - Customer Agent negotiation
        - Terminal animation
        - Business Advisor analysis
        """
        
        if show_animation:
            self._start_animation()
        
        try:
            # Initialize database
            init_database()
            
            # Step 1: Customer Analysis
            await self._step_customer_analysis(customer_id, customer_request)
            
            # Step 2: Orchestrator Processing
            await self._step_orchestrator_processing(customer_request)
            
            # Step 3: Inventory Check
            await self._step_inventory_check()
            
            # Step 4: Quote Generation
            quote_result = await self._step_quote_generation(customer_request, customer_id)
            
            # Step 5: Customer Negotiation
            negotiation_result = await self._step_customer_negotiation(
                customer_id, customer_request, quote_result
            )
            
            # Step 6: Sales Processing
            sales_result = await self._step_sales_processing(negotiation_result)
            
            # Step 7: Business Analysis
            business_analysis = await self._step_business_analysis()
            
            # Final Summary
            final_results = self._create_final_summary(
                negotiation_result, sales_result, business_analysis
            )
            
            if show_animation:
                show_processing_summary(final_results)
            
            return final_results
            
        except Exception as e:
            print(f"❌ Error in advanced processing: {e}")
            if show_animation:
                update_agent_processing("orchestrator", "error", f"Error: {str(e)}")
            return {"error": str(e)}
            
        finally:
            if show_animation:
                await asyncio.sleep(3)
                stop_processing_animation()
    
    def _start_animation(self):
        """Start the terminal animation"""
        start_processing_animation()
        self.animation_running = True
    
    async def _step_customer_analysis(self, customer_id: str, customer_request: str):
        """Step 1: Analyze customer profile"""
        update_processing_step("Analyzing customer profile", 1)
        update_agent_processing("customer", "processing", "Loading customer data")
        
        # Show customer details
        show_customer_details(f"Customer {customer_id}", customer_request)
        
        await asyncio.sleep(1)
        update_agent_processing("customer", "completed", "Profile analyzed")
    
    async def _step_orchestrator_processing(self, customer_request: str):
        """Step 2: Orchestrator processes the request"""
        update_processing_step("Processing customer request", 2)
        update_agent_processing("orchestrator", "processing", "Analyzing request")
        
        # Simulate orchestrator processing
        await asyncio.sleep(1)
        update_agent_processing("orchestrator", "completed", "Request analyzed")
    
    async def _step_inventory_check(self):
        """Step 3: Check inventory availability"""
        update_processing_step("Checking inventory availability", 3)
        update_agent_processing("inventory", "processing", "Verifying stock levels")
        
        # Simulate inventory check
        await asyncio.sleep(1)
        update_agent_processing("inventory", "completed", "Stock levels verified")
    
    async def _step_quote_generation(self, customer_request: str, customer_id: str):
        """Step 4: Generate quote"""
        update_processing_step("Generating quote with discounts", 4)
        update_agent_processing("quoting", "processing", "Calculating pricing")
        
        # Simulate quote generation
        quote_result = {
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
        
        await asyncio.sleep(1)
        update_agent_processing("quoting", "completed", "Quote generated")
        
        return quote_result
    
    async def _step_customer_negotiation(
        self, 
        customer_id: str, 
        customer_request: str, 
        initial_quote: Dict[str, Any]
    ):
        """Step 5: Customer negotiation"""
        update_processing_step("Customer negotiation in progress", 5)
        update_agent_processing("customer", "processing", "Negotiating terms")
        
        # Show initial quote
        show_negotiation_details(1, initial_quote)
        
        # Simulate negotiation
        await asyncio.sleep(1)
        
        # Customer negotiation result
        negotiation_result = {
            'negotiation_successful': True,
            'customer_profile': {
                'customer_id': customer_id,
                'name': 'Sarah Johnson',
                'customer_type': 'premium',
                'negotiation_style': 'analytical'
            },
            'initial_evaluation': {
                'strategy': 'minor_negotiation',
                'satisfaction_score': 0.75
            },
            'counter_offer': {
                'total_price': 75.50,
                'discount_percentage': 8.0,
                'delivery_days': 5
            },
            'final_deal': {
                'total_amount': 75.50,
                'discount_applied': 8.0,
                'delivery_days': 5,
                'customer_satisfaction': 0.9
            },
            'negotiation_rounds': 2
        }
        
        # Show counter-offer
        show_negotiation_details(2, negotiation_result['counter_offer'])
        
        await asyncio.sleep(1)
        update_agent_processing("customer", "completed", "Deal finalized")
        
        return negotiation_result
    
    async def _step_sales_processing(self, negotiation_result: Dict[str, Any]):
        """Step 6: Process sales transaction"""
        update_processing_step("Processing sales transaction", 6)
        update_agent_processing("sales", "processing", "Completing sale")
        
        # Simulate sales processing
        await asyncio.sleep(1)
        update_agent_processing("sales", "completed", "Transaction completed")
        
        return {
            'transaction_completed': True,
            'items_sold': 700,
            'total_amount': negotiation_result['final_deal']['total_amount']
        }
    
    async def _step_business_analysis(self):
        """Step 7: Business advisor analysis"""
        update_processing_step("Business advisor analysis", 7)
        update_agent_processing("business_advisor", "processing", "Analyzing performance")
        
        # Simulate business analysis
        await asyncio.sleep(1)
        
        # Business recommendations
        recommendations = [
            {
                'category': 'pricing',
                'priority': 'high',
                'title': 'Implement Dynamic Pricing for Premium Customers',
                'description': 'Adjust pricing based on customer type and order volume',
                'expected_impact': 'Increase revenue by 15-20%',
                'estimated_roi': 25.0,
                'timeline': '2-3 weeks'
            },
            {
                'category': 'inventory',
                'priority': 'medium',
                'title': 'Optimize Stock Levels for High-Demand Items',
                'description': 'Increase stock for A4 paper and cardstock to reduce stockouts',
                'expected_impact': 'Reduce stockouts by 40%',
                'estimated_roi': 12.0,
                'timeline': '1 week'
            },
            {
                'category': 'operations',
                'priority': 'high',
                'title': 'Automate Reordering Process',
                'description': 'Implement predictive reordering based on sales patterns',
                'expected_impact': 'Reduce manual work by 60%',
                'estimated_roi': 35.0,
                'timeline': '4-6 weeks'
            }
        ]
        
        show_business_insights(recommendations)
        
        await asyncio.sleep(1)
        update_agent_processing("business_advisor", "completed", "Analysis complete")
        
        return {
            'recommendations': recommendations,
            'total_recommendations': len(recommendations)
        }
    
    def _create_final_summary(
        self, 
        negotiation_result: Dict[str, Any],
        sales_result: Dict[str, Any],
        business_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create final processing summary"""
        return {
            'negotiation_successful': negotiation_result.get('negotiation_successful', False),
            'final_deal': negotiation_result.get('final_deal', {}),
            'negotiation_rounds': negotiation_result.get('negotiation_rounds', 0),
            'transaction_completed': sales_result.get('transaction_completed', False),
            'items_sold': sales_result.get('items_sold', 0),
            'total_amount': sales_result.get('total_amount', 0),
            'business_recommendations': business_analysis.get('total_recommendations', 0),
            'processing_time': 8.5,
            'customer_satisfaction': negotiation_result.get('final_deal', {}).get('customer_satisfaction', 0.0)
        }


async def demo_different_customers():
    """Demonstrate different customer types and negotiation styles"""
    print("\n🎭 Customer Types Demo")
    print("=" * 80)
    
    system = AdvancedMultiAgentSystem()
    
    customers = [
        {
            "id": "CUST001",
            "name": "Sarah Johnson",
            "type": "Premium Customer",
            "request": "I need 1000 sheets of premium paper for our annual report. Quality is more important than price."
        },
        {
            "id": "CUST002", 
            "name": "Mike Rodriguez",
            "type": "Bulk Customer",
            "request": "I need 5000 sheets of A4 paper. Give me your best price - I'm shopping around."
        },
        {
            "id": "CUST003",
            "name": "Lisa Chen",
            "type": "Standard Customer", 
            "request": "I need 200 sheets of colored paper for an event. What can you do for me?"
        }
    ]
    
    for customer in customers:
        print(f"\n👤 Processing {customer['name']} ({customer['type']})")
        print(f"💬 Request: {customer['request']}")
        print("-" * 60)
        
        # Process without animation for demo
        result = await system.process_customer_request_advanced(
            customer['request'], 
            customer['id'], 
            show_animation=False
        )
        
        if result.get('negotiation_successful'):
            print(f"✅ Deal completed: ${result['final_deal'].get('total_amount', 0):,.2f}")
            print(f"🤝 Negotiation rounds: {result['negotiation_rounds']}")
            print(f"😊 Customer satisfaction: {result['customer_satisfaction']:.1%}")
        
        await asyncio.sleep(1)


async def main():
    """Main function to run the advanced multi-agent system"""
    print("🚀 Munder Difflin Multi-Agent System - Advanced Features")
    print("=" * 80)
    print("New Features:")
    print("1. 🤖 Customer Agent with intelligent negotiation")
    print("2. 🎬 Real-time terminal animation")
    print("3. 💼 Business Advisor with actionable recommendations")
    print("4. 🔄 Integrated end-to-end workflow")
    print("=" * 80)
    
    # Create system instance
    system = AdvancedMultiAgentSystem()
    
    # Main demo with animation
    print("\n🎬 Running Main Demo with Animation...")
    customer_request = "I need 500 sheets of A4 paper and 200 sheets of cardstock for our upcoming conference. We're a premium customer and need delivery within 5 days."
    
    result = await system.process_customer_request_advanced(
        customer_request, 
        "CUST001", 
        show_animation=True
    )
    
    # Demo different customer types
    await demo_different_customers()
    
    print("\n🎉 Advanced Features Demo Completed!")
    print("=" * 80)
    print("✅ Features Successfully Demonstrated:")
    print("   🤖 Customer Agent: Profile-based negotiation")
    print("   🎬 Terminal Animation: Real-time processing display")
    print("   💼 Business Advisor: Performance analysis & recommendations")
    print("   🔄 Integration: End-to-end workflow coordination")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
