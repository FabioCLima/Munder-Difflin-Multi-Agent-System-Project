"""
Terminal Animation System - Shows real-time processing of customer requests
"""

import time
import threading
from typing import Dict, List, Any
from datetime import datetime
import sys
import os


class TerminalAnimation:
    """Animated terminal display for multi-agent system processing"""
    
    def __init__(self):
        self.animation_chars = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
        self.current_char = 0
        self.running = False
        self.agent_status = {}
        self.current_step = ""
        self.progress = 0
        self.total_steps = 0
        
    def start_animation(self, total_steps: int = 5):
        """Start the terminal animation"""
        self.running = True
        self.total_steps = total_steps
        self.progress = 0
        self.agent_status = {
            "orchestrator": "waiting",
            "inventory": "waiting", 
            "quoting": "waiting",
            "customer": "waiting",
            "sales": "waiting",
            "reordering": "waiting",
            "business_advisor": "waiting"
        }
        
        # Clear screen and start animation thread
        os.system('clear' if os.name == 'posix' else 'cls')
        self.animation_thread = threading.Thread(target=self._animate)
        self.animation_thread.daemon = True
        self.animation_thread.start()
        
    def stop_animation(self):
        """Stop the terminal animation"""
        self.running = False
        if hasattr(self, 'animation_thread'):
            self.animation_thread.join()
        print("\n" + "="*80)
        
    def update_agent_status(self, agent: str, status: str, message: str = ""):
        """Update the status of a specific agent"""
        self.agent_status[agent] = {
            "status": status,
            "message": message,
            "timestamp": datetime.now().strftime("%H:%M:%S")
        }
        
    def update_agent_processing(self, agent: str, status: str, message: str = ""):
        """Alias for update_agent_status for compatibility"""
        self.update_agent_status(agent, status, message)
        
    def update_step(self, step: str, progress: int = None):
        """Update the current processing step"""
        self.current_step = step
        if progress is not None:
            self.progress = progress
            
    def update_processing_step(self, step: str, progress: int = None):
        """Alias for update_step for compatibility"""
        self.update_step(step, progress)
            
    def _animate(self):
        """Main animation loop"""
        while self.running:
            self._draw_frame()
            time.sleep(0.1)
            
    def _draw_frame(self):
        """Draw the current animation frame"""
        # Move cursor to top
        sys.stdout.write('\033[H')
        sys.stdout.write('\033[2J')
        
        # Header
        print("🚀 Munder Difflin Multi-Agent System - Live Processing")
        print("=" * 80)
        print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # Progress bar
        progress_bar = self._create_progress_bar()
        print(f"📊 Progress: {progress_bar} {self.progress}/{self.total_steps}")
        print()
        
        # Current step
        if self.current_step:
            char = self.animation_chars[self.current_char]
            print(f"{char} Current Step: {self.current_step}")
            self.current_char = (self.current_char + 1) % len(self.animation_chars)
        print()
        
        # Agent status
        print("🤖 Agent Status:")
        print("-" * 50)
        
        for agent, status_info in self.agent_status.items():
            if isinstance(status_info, dict):
                status = status_info["status"]
                message = status_info.get("message", "")
                timestamp = status_info.get("timestamp", "")
            else:
                status = status_info
                message = ""
                timestamp = ""
                
            # Choose emoji and color based on status
            if status == "processing":
                emoji = "🔄"
                color = "\033[93m"  # Yellow
            elif status == "completed":
                emoji = "✅"
                color = "\033[92m"  # Green
            elif status == "error":
                emoji = "❌"
                color = "\033[91m"  # Red
            elif status == "waiting":
                emoji = "⏳"
                color = "\033[94m"  # Blue
            else:
                emoji = "❓"
                color = "\033[0m"   # Default
                
            # Format agent name
            agent_name = agent.replace("_", " ").title()
            
            # Print status
            print(f"{color}{emoji} {agent_name:<15} {status.upper():<12} {message} {timestamp}\033[0m")
            
        print()
        
        # Recent activity
        print("📋 Recent Activity:")
        print("-" * 50)
        self._show_recent_activity()
        
        sys.stdout.flush()
        
    def _create_progress_bar(self, width: int = 30) -> str:
        """Create a visual progress bar"""
        filled = int((self.progress / self.total_steps) * width)
        bar = "█" * filled + "░" * (width - filled)
        return f"[{bar}]"
        
    def _show_recent_activity(self):
        """Show recent system activity"""
        activities = [
            "🔍 Analyzing customer request...",
            "📦 Checking inventory levels...",
            "💰 Generating quote with discounts...",
            "🤝 Customer negotiation in progress...",
            "🛒 Processing sales transaction...",
            "📊 Business advisor analyzing performance...",
            "🔄 Auto-reordering low stock items..."
        ]
        
        # Show last few activities based on progress
        start_idx = max(0, self.progress - 3)
        for i in range(start_idx, min(self.progress + 1, len(activities))):
            if i < len(activities):
                print(f"  {activities[i]}")
                
    def show_customer_interaction(self, customer_name: str, request: str):
        """Show customer interaction details"""
        print(f"\n👤 Customer: {customer_name}")
        print(f"💬 Request: {request}")
        print("-" * 50)
        
    def show_negotiation_round(self, round_num: int, offer: Dict[str, Any]):
        """Show negotiation round details"""
        print(f"\n🤝 Negotiation Round {round_num}")
        print(f"💰 Offer: ${offer.get('total_price', 0):,.2f}")
        print(f"📊 Discount: {offer.get('discount_percentage', 0):.1f}%")
        print(f"🚚 Delivery: {offer.get('delivery_days', 7)} days")
        print("-" * 50)
        
    def show_business_recommendations(self, recommendations: List[Dict[str, Any]]):
        """Show business advisor recommendations"""
        print(f"\n💼 Business Advisor Recommendations:")
        print("-" * 50)
        
        for i, rec in enumerate(recommendations[:3], 1):  # Show top 3
            priority_emoji = {
                "high": "🔴",
                "medium": "🟡", 
                "low": "🟢"
            }.get(rec.get('priority', 'medium'), "🟡")
            
            print(f"{priority_emoji} {i}. {rec.get('title', 'Recommendation')}")
            print(f"   📈 Expected Impact: {rec.get('expected_impact', 'N/A')}")
            print(f"   💰 Estimated ROI: {rec.get('estimated_roi', 0):.1f}%")
            print()
            
    def show_final_summary(self, results: Dict[str, Any]):
        """Show final processing summary"""
        print("\n🎉 Processing Complete!")
        print("=" * 80)
        
        if results.get('negotiation_successful'):
            print("✅ Customer negotiation successful")
            print(f"💰 Final deal value: ${results.get('final_deal', {}).get('total_amount', 0):,.2f}")
            print(f"🤝 Negotiation rounds: {results.get('negotiation_rounds', 0)}")
            
        if results.get('transaction_completed'):
            print("✅ Sales transaction completed")
            print(f"📦 Items sold: {results.get('items_sold', 0)}")
            
        if results.get('reorder_triggered'):
            print("✅ Auto-reorder triggered")
            print(f"📦 Items reordered: {results.get('items_reordered', 0)}")
            
        print(f"⏱️  Total processing time: {results.get('processing_time', 0):.2f} seconds")
        print("=" * 80)


# Global animation instance
animation = TerminalAnimation()


def start_processing_animation():
    """Start the processing animation"""
    animation.start_animation(7)  # 7 steps: orchestrator -> inventory -> quoting -> customer -> sales -> reordering -> business_advisor


def stop_processing_animation():
    """Stop the processing animation"""
    animation.stop_animation()


def update_agent_processing(agent: str, status: str, message: str = ""):
    """Update agent processing status"""
    animation.update_agent_status(agent, status, message)


def update_processing_step(step: str, progress: int = None):
    """Update current processing step"""
    animation.update_step(step, progress)


def show_customer_details(customer_name: str, request: str):
    """Show customer interaction details"""
    animation.show_customer_interaction(customer_name, request)


def show_negotiation_details(round_num: int, offer: Dict[str, Any]):
    """Show negotiation details"""
    animation.show_negotiation_round(round_num, offer)


def show_business_insights(recommendations: List[Dict[str, Any]]):
    """Show business advisor insights"""
    animation.show_business_recommendations(recommendations)


def show_processing_summary(results: Dict[str, Any]):
    """Show final processing summary"""
    animation.show_final_summary(results)
