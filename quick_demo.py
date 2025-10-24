#!/usr/bin/env python3
"""
Quick Demo - Munder Difflin Advanced Features
Demonstrates Customer Agent, Terminal Animation, and Business Advisor
"""

import asyncio
import time
from src.utils.terminal_animation import TerminalAnimation
from src.agents.customer_agent import analyze_customer_profile, evaluate_quote


async def quick_customer_demo():
    """Quick demonstration of Customer Agent features"""
    print("🤖 Customer Agent Demo")
    print("=" * 50)
    
    # Test different customer profiles
    customers = ["CUST001", "CUST002", "CUST003"]
    names = ["Sarah Johnson (Premium)", "Mike Rodriguez (Bulk)", "Lisa Chen (Standard)"]
    
    for customer_id, name in zip(customers, names):
        print(f"\n👤 {name}")
        
        # Analyze customer profile
        profile = await analyze_customer_profile(None, customer_id)
        print(f"   📊 Type: {profile['customer_type']}")
        print(f"   🤝 Style: {profile['negotiation_style']}")
        
        # Test quote evaluation
        quote = {'total_price': 150.0, 'discount_percentage': 5.0, 'delivery_days': 7}
        evaluation = await evaluate_quote(None, quote, profile)
        print(f"   💰 Quote: ${quote['total_price']:,.2f} - {evaluation['strategy']}")
        print(f"   😊 Satisfaction: {evaluation['satisfaction_score']:.2f}")
        
        await asyncio.sleep(0.5)


def quick_animation_demo():
    """Quick demonstration of Terminal Animation"""
    print("\n🎬 Terminal Animation Demo")
    print("=" * 50)
    
    anim = TerminalAnimation()
    anim.start_animation(4)
    
    try:
        # Simulate quick processing
        steps = [
            ("Customer analysis", "customer", "processing", "Analyzing profile"),
            ("Quote generation", "quoting", "processing", "Calculating price"),
            ("Negotiation", "customer", "processing", "Making counter-offer"),
            ("Deal finalization", "sales", "processing", "Completing transaction")
        ]
        
        for i, (step, agent, status, message) in enumerate(steps, 1):
            time.sleep(1)
            anim.update_processing_step(step, i)
            anim.update_agent_processing(agent, status, message)
            
            # Mark previous as completed
            if i > 1:
                prev_agent = steps[i-2][1]
                anim.update_agent_processing(prev_agent, "completed", "Done")
        
        # Mark final as completed
        anim.update_agent_processing("sales", "completed", "Transaction completed")
        time.sleep(1)
        
    finally:
        anim.stop_animation()


def quick_business_demo():
    """Quick demonstration of Business Advisor"""
    print("\n💼 Business Advisor Demo")
    print("=" * 50)
    
    # Simulate business metrics
    metrics = {
        'revenue': 45000.0,
        'transactions': 25,
        'satisfaction': 0.85,
        'efficiency': 0.78
    }
    
    print("📊 Current Performance:")
    print(f"   💰 Revenue: ${metrics['revenue']:,.2f}")
    print(f"   📈 Transactions: {metrics['transactions']}")
    print(f"   😊 Satisfaction: {metrics['satisfaction']:.1%}")
    print(f"   ⚡ Efficiency: {metrics['efficiency']:.1%}")
    
    # Simulate recommendations
    recommendations = [
        ("Dynamic Pricing", "high", "25% ROI", "2-3 weeks"),
        ("Stock Optimization", "medium", "12% ROI", "1 week"),
        ("Process Automation", "high", "35% ROI", "4-6 weeks")
    ]
    
    print("\n🎯 Top Recommendations:")
    for title, priority, roi, timeline in recommendations:
        emoji = "🔴" if priority == "high" else "🟡"
        print(f"   {emoji} {title}: {roi} ({timeline})")


async def main():
    """Main quick demo function"""
    print("⚡ Quick Demo - Advanced Features")
    print("=" * 60)
    print("This demo shows:")
    print("1. 🤖 Customer Agent negotiation")
    print("2. 🎬 Terminal animation")
    print("3. 💼 Business recommendations")
    print("=" * 60)
    
    # Customer Agent Demo
    await quick_customer_demo()
    
    # Animation Demo
    quick_animation_demo()
    
    # Business Advisor Demo
    quick_business_demo()
    
    print("\n🎉 Quick Demo Completed!")
    print("=" * 60)
    print("✅ All advanced features demonstrated successfully!")
    print("🚀 Run 'python main_advanced.py' for full interactive demo")


if __name__ == "__main__":
    asyncio.run(main())
