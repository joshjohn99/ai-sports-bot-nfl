#!/usr/bin/env python3

"""
🏢 Commercial AI Sports Debate Arena - Production Demo
Demonstrates the complete commercial system with billing, rate limiting, premium features, and analytics
"""

import asyncio
import sys
import os

# Add the source directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt

console = Console()

async def demo_commercial_system():
    """Demo the complete commercial system"""
    
    console.print(Panel.fit(
        "[bold red]🏢 AI SPORTS DEBATE ARENA - COMMERCIAL SYSTEM DEMO[/bold red]\\n"
        "[green]Production-grade billing, rate limiting, and premium features[/green]\\n"
        "[cyan]Ready for revenue generation and enterprise customers[/cyan]",
        border_style="red"
    ))
    
    try:
        # Import commercial system
        from sports_bot.commercial.gateway import commercial_gateway
        from sports_bot.commercial.billing import UserTier, billing_manager
        
        console.print("[green]✅ Commercial system imported successfully![/green]")
        
        # Phase 1: Create Test Users for Different Tiers
        console.print("\\n[bold yellow]📋 Phase 1: Creating Test Users for All Tiers[/bold yellow]")
        
        test_users = {}
        for tier in UserTier:
            email = f"test_{tier.value}@sportsbot.ai"
            user_account = await billing_manager.create_user_account(email, tier)
            test_users[tier.value] = user_account.user_id
            
            console.print(f"[cyan]Created {tier.value.title()} user: {user_account.user_id[:8]}...[/cyan]")
        
        # Phase 2: Demo Tier Pricing and Limits
        console.print("\\n[bold yellow]💰 Phase 2: Commercial Tier Structure[/bold yellow]")
        
        pricing_table = Table(title="Commercial Pricing Tiers")
        pricing_table.add_column("Tier", style="cyan")
        pricing_table.add_column("Price/Month", style="green")
        pricing_table.add_column("Monthly Debates", style="yellow")
        pricing_table.add_column("Concurrent", style="magenta")
        pricing_table.add_column("Advanced Analytics", style="blue")
        pricing_table.add_column("Real-time Streaming", style="red")
        pricing_table.add_column("Custom Agents", style="purple")
        
        for tier in UserTier:
            limits = billing_manager.tier_config.get_limits(tier)
            pricing_table.add_row(
                tier.value.title(),
                f"${limits.monthly_price_usd}",
                str(limits.monthly_debates) if limits.monthly_debates != -1 else "Unlimited",
                str(limits.concurrent_debates),
                "✅" if limits.advanced_analytics else "❌",
                "✅" if limits.real_time_streaming else "❌",
                "✅" if limits.custom_agents else "❌"
            )
        
        console.print(pricing_table)
        
        # Phase 3: Demo Commercial Debates for Each Tier
        console.print("\\n[bold yellow]🏟️ Phase 3: Commercial Debate Demonstrations[/bold yellow]")
        
        test_topics = [
            "Who is the better quarterback: Josh Allen vs Lamar Jackson?",
            "Compare LeBron James vs Michael Jordan career achievements",
            "NFL vs NBA: Which has better playoffs?",
            "Tom Brady vs Aaron Rodgers statistical analysis"
        ]
        
        for i, (tier_name, user_id) in enumerate(test_users.items()):
            topic = test_topics[i % len(test_topics)]
            
            console.print(f"\\n[bold blue]Testing {tier_name.title()} Tier - User: {user_id[:8]}...[/bold blue]")
            console.print(f"[yellow]Topic: {topic}[/yellow]")
            
            # Configure options based on tier
            options = {}
            if tier_name in ["premium", "enterprise"]:
                options["advanced_analytics"] = True
            if tier_name in ["basic", "premium", "enterprise"]:
                options["real_time_streaming"] = True
            if tier_name == "enterprise":
                options["custom_agent_config"] = {"style": "enterprise_formal"}
            
            console.print(f"[cyan]Options: {options}[/cyan]")
            
            # Start commercial debate
            async for response in commercial_gateway.start_commercial_debate(user_id, topic, options):
                if response["type"] == "error":
                    console.print(f"[red]❌ {response['message']}[/red]")
                    break
                elif response["type"] == "quota_exceeded":
                    console.print(f"[yellow]⚠️ {response['message']}[/yellow]")
                    console.print(f"[cyan]Upgrade to: {response.get('upgrade_tier', 'Next tier')}[/cyan]")
                    break
                elif response["type"] == "feature_access_denied":
                    console.print(f"[yellow]🔒 Feature Access Denied: {response['feature']}[/yellow]")
                    console.print(f"[cyan]Reason: {response['message']}[/cyan]")
                    break
                elif response["type"] == "debate_starting":
                    console.print(f"[green]🚀 Debate Started![/green]")
                    console.print(f"[cyan]Debate ID: {response['debate_id'][:8]}...[/cyan]")
                    console.print(f"[cyan]Features: {response['features_enabled']}[/cyan]")
                elif response["type"] == "debate_response":
                    console.print(Panel(response["content"], border_style="green"))
                elif response["type"] == "enhanced_analytics":
                    console.print(Panel(response["content"], title="Premium Analytics", border_style="yellow"))
                elif response["type"] == "enterprise_features":
                    console.print(Panel(response["content"], title="Enterprise Features", border_style="purple"))
                elif response["type"] == "debate_completed":
                    console.print(f"[green]✅ Debate completed in {response['total_compute_time']:.2f}s[/green]")
                    billing_summary = response["billing_summary"]
                    if billing_summary.get("debates_remaining", -1) != -1:
                        console.print(f"[cyan]Debates remaining: {billing_summary['debates_remaining']}[/cyan]")
                    break
            
            await asyncio.sleep(1)  # Brief pause between demos
        
        # Phase 4: Demo User Dashboards
        console.print("\\n[bold yellow]📊 Phase 4: User Dashboard Demo[/bold yellow]")
        
        for tier_name, user_id in test_users.items():
            dashboard = await commercial_gateway.get_user_dashboard(user_id)
            
            console.print(f"\\n[bold blue]{tier_name.title()} User Dashboard:[/bold blue]")
            console.print(f"[cyan]Tier: {dashboard['tier']}[/cyan]")
            console.print(f"[cyan]Debates Used: {dashboard['current_usage']['debates_used']}[/cyan]")
            console.print(f"[cyan]Monthly Price: ${dashboard['billing']['monthly_price']}[/cyan]")
            
            if dashboard.get('upgrade_suggestion'):
                upgrade = dashboard['upgrade_suggestion']
                console.print(f"[yellow]💡 Upgrade Suggestion: {upgrade['suggested_tier']} (${upgrade['price']}/month)[/yellow]")
        
        # Phase 5: Demo Tier Upgrades
        console.print("\\n[bold yellow]⬆️ Phase 5: Tier Upgrade Demo[/bold yellow]")
        
        # Upgrade free user to basic
        free_user_id = test_users["free"]
        payment_info = {"payment_method_id": "pm_demo_12345", "billing_address": {"country": "US"}}
        
        console.print(f"[cyan]Upgrading Free user {free_user_id[:8]}... to Basic tier[/cyan]")
        
        upgrade_result = await commercial_gateway.upgrade_user_tier(
            free_user_id, UserTier.BASIC, payment_info
        )
        
        if upgrade_result["success"]:
            console.print(f"[green]✅ {upgrade_result['message']}[/green]")
            console.print(f"[cyan]New billing cycle: {upgrade_result['billing_cycle_start']}[/cyan]")
        else:
            console.print(f"[red]❌ Upgrade failed: {upgrade_result['error']}[/red]")
        
        # Phase 6: Business Analytics Demo
        console.print("\\n[bold yellow]📈 Phase 6: Business Analytics Dashboard[/bold yellow]")
        
        analytics = await commercial_gateway.get_business_analytics()
        
        if "error" not in analytics:
            revenue_data = analytics["revenue"]
            usage_data = analytics["usage"]
            
            analytics_table = Table(title="Business Intelligence Dashboard")
            analytics_table.add_column("Metric", style="cyan")
            analytics_table.add_column("Value", style="green")
            
            analytics_table.add_row("Total Revenue", f"${revenue_data['total_revenue_usd']:.2f}")
            analytics_table.add_row("Active Users", str(revenue_data['total_active_users']))
            analytics_table.add_row("ARPU", f"${revenue_data['avg_revenue_per_user']:.2f}")
            analytics_table.add_row("Total Debates", str(usage_data['total_debates_started']))
            analytics_table.add_row("Completion Rate", f"{usage_data['completion_rate']:.1f}%")
            analytics_table.add_row("Avg Compute Time", f"{usage_data['avg_compute_time_seconds']:.2f}s")
            
            console.print(analytics_table)
            
            # Revenue by tier
            console.print("\\n[bold blue]Revenue by Tier:[/bold blue]")
            for tier, revenue in revenue_data['revenue_by_tier'].items():
                users = revenue_data['users_by_tier'][tier]
                console.print(f"[cyan]{tier.title()}: ${revenue:.2f} ({users} users)[/cyan]")
        
        # Phase 7: System Health Check
        console.print("\\n[bold yellow]🏥 Phase 7: System Health Monitoring[/bold yellow]")
        
        from sports_bot.commercial.monitoring import ProductionMonitor
        monitor = ProductionMonitor()
        
        health_check = await monitor.check_system_health()
        console.print(f"[cyan]Health Score: {health_check['health_score']:.2f}[/cyan]")
        console.print(f"[cyan]Status: {health_check['status'].title()}[/cyan]")
        
        if health_check['issues']:
            console.print("[yellow]Issues detected:[/yellow]")
            for issue in health_check['issues']:
                console.print(f"[yellow]• {issue}[/yellow]")
        
        if health_check['recommendations']:
            console.print("[blue]Recommendations:[/blue]")
            for rec in health_check['recommendations']:
                console.print(f"[blue]• {rec}[/blue]")
        
        # Phase 8: Summary
        console.print("\\n" + "="*80)
        console.print(Panel.fit(
            "[bold green]🎉 COMMERCIAL SYSTEM DEMO COMPLETE![/bold green]\\n\\n"
            "[yellow]✅ Billing & Tier Management[/yellow]\\n"
            "[yellow]✅ Rate Limiting & Quota Enforcement[/yellow]\\n"
            "[yellow]✅ Premium Feature Gates[/yellow]\\n"
            "[yellow]✅ User Dashboards & Analytics[/yellow]\\n"
            "[yellow]✅ Tier Upgrades & Payment Processing[/yellow]\\n"
            "[yellow]✅ Business Intelligence Dashboard[/yellow]\\n"
            "[yellow]✅ Production Monitoring & Health Checks[/yellow]\\n\\n"
            "[cyan]Your existing debate arena is now wrapped with[/cyan]\\n"
            "[cyan]enterprise-grade commercial infrastructure![/cyan]\\n\\n"
            "[green]Ready for customers and revenue generation! 💰[/green]",
            border_style="green"
        ))
        
        console.print("\\n[bold blue]Integration Points for Your Existing System:[/bold blue]")
        console.print("[cyan]1. Replace the demo responses in gateway.py with your dynamic_arena.process_any_debate_query()[/cyan]")
        console.print("[cyan]2. Add payment processor integration (Stripe) in billing.py[/cyan]")
        console.print("[cyan]3. Connect to your user authentication system[/cyan]")
        console.print("[cyan]4. Set up production monitoring and alerting[/cyan]")
        console.print("[cyan]5. Deploy with load balancing and auto-scaling[/cyan]")
        
    except ImportError as e:
        console.print(f"[red]❌ Import Error: {e}[/red]")
        console.print("[yellow]Make sure you're running from the ai-sports-bot-nfl directory[/yellow]")
    except Exception as e:
        console.print(f"[red]❌ Error during demo: {e}[/red]")
        import traceback
        console.print(f"[red]{traceback.format_exc()}[/red]")

if __name__ == "__main__":
    asyncio.run(demo_commercial_system()) 