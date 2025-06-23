"""
Quick fix for LangGraph cache interface and recursion issues
"""

def fix_cache_interface():
    """Fix the cache interface in the workflow"""
    
    file_path = "src/sports_bot/workflows/intelligent_data_flow.py"
    
    # Read the file
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Fix cache interface
    content = content.replace(
        "cached_data = self.cache.get(cache_key)",
        "cached_player = self.cache.get_player(sport, player_name)"
    )
    
    content = content.replace(
        "self.cache.set(cache_key, player_data, expire=3600)",
        "self.cache.set_stats(sport, player_id, '2024', query_context.get('metrics_needed', []), player_data)"
    )
    
    # Add recursion limit
    content = content.replace(
        'return workflow.compile(checkpointer=MemorySaver())',
        '''return workflow.compile(
            checkpointer=MemorySaver()
        )'''
    )
    
    content = content.replace(
        '"recursion_limit": 10  # EXPLICIT LIMIT',
        '"recursion_limit": 15  # EXPLICIT LIMIT'
    )
    
    # Write back
    with open(file_path, 'w') as f:
        f.write(content)
    
    print("✅ Fixed cache interface and recursion limit!")

if __name__ == "__main__":
    fix_cache_interface()
