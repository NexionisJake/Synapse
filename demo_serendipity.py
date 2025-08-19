#!/usr/bin/env python3
"""
Demo script for Serendipity Engine

This script demonstrates the serendipity engine functionality
by analyzing the existing memory.json file.
"""

import sys
import os
import json
from datetime import datetime

# Add the project directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from serendipity_service import get_serendipity_service, SerendipityServiceError

def main():
    """Main demo function"""
    print("Synapse Serendipity Engine Demo")
    print("=" * 40)
    
    try:
        # Get serendipity service
        service = get_serendipity_service(memory_file='memory.json')
        
        # Check if memory file exists
        if not os.path.exists('memory.json'):
            print("❌ Memory file not found!")
            print("Please run some conversations first to build memory.")
            return
        
        # Load and display memory stats
        memory_data = service.load_memory_data()
        insights_count = len(memory_data.get('insights', []))
        summaries_count = len(memory_data.get('conversation_summaries', []))
        
        print(f"📊 Memory Statistics:")
        print(f"   • Insights: {insights_count}")
        print(f"   • Conversation Summaries: {summaries_count}")
        print()
        
        if insights_count < 3:
            print("⚠️  Insufficient data for meaningful connections")
            print(f"   Need at least 3 insights, currently have {insights_count}")
            print("   Have more conversations to build up your memory!")
            return
        
        print("🔮 Discovering connections...")
        print("   This may take a moment while the AI analyzes your memory...")
        print()
        
        # Analyze memory for connections
        start_time = datetime.now()
        connections_data = service.analyze_memory()
        end_time = datetime.now()
        
        processing_time = (end_time - start_time).total_seconds()
        print(f"✅ Analysis complete! (took {processing_time:.1f} seconds)")
        print()
        
        # Display results
        display_results(connections_data)
        
    except SerendipityServiceError as e:
        print(f"❌ Serendipity service error: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

def display_results(data):
    """Display serendipity analysis results"""
    
    # Summary
    summary = data.get('serendipity_summary', 'No summary available')
    print("📋 Discovery Summary:")
    print(f"   {summary}")
    print()
    
    # Connections
    connections = data.get('connections', [])
    if connections:
        print(f"🔗 Unexpected Connections ({len(connections)} found):")
        for i, connection in enumerate(connections, 1):
            title = connection.get('title', 'Untitled Connection')
            description = connection.get('description', 'No description')
            surprise = connection.get('surprise_factor', 0) * 100
            relevance = connection.get('relevance', 0) * 100
            conn_type = connection.get('connection_type', 'unknown')
            insight = connection.get('actionable_insight', '')
            
            print(f"   {i}. {title}")
            print(f"      Type: {conn_type.title()}")
            print(f"      Surprise: {surprise:.0f}% | Relevance: {relevance:.0f}%")
            print(f"      {description}")
            if insight:
                print(f"      💡 Actionable: {insight}")
            print()
    else:
        print("🔗 No unexpected connections found")
        print("   Keep having diverse conversations to discover more patterns!")
        print()
    
    # Meta Patterns
    patterns = data.get('meta_patterns', [])
    if patterns:
        print(f"🧩 Overarching Patterns ({len(patterns)} found):")
        for i, pattern in enumerate(patterns, 1):
            name = pattern.get('pattern_name', 'Unnamed Pattern')
            description = pattern.get('description', 'No description')
            evidence = pattern.get('evidence_count', 0)
            confidence = pattern.get('confidence', 0) * 100
            
            print(f"   {i}. {name}")
            print(f"      Confidence: {confidence:.0f}% | Evidence: {evidence} insights")
            print(f"      {description}")
            print()
    else:
        print("🧩 No overarching patterns detected")
        print("   More conversations will help reveal deeper patterns!")
        print()
    
    # Recommendations
    recommendations = data.get('recommendations', [])
    if recommendations:
        print(f"💡 Recommendations ({len(recommendations)} suggestions):")
        for i, rec in enumerate(recommendations, 1):
            print(f"   {i}. {rec}")
        print()
    
    # Metadata
    metadata = data.get('analysis_metadata', {})
    if metadata:
        insights_analyzed = metadata.get('insights_analyzed', 0)
        conversations_analyzed = metadata.get('conversations_analyzed', 0)
        model_used = metadata.get('model_used', 'unknown')
        
        print("📈 Analysis Details:")
        print(f"   • Model: {model_used}")
        print(f"   • Insights Analyzed: {insights_analyzed}")
        print(f"   • Conversations Analyzed: {conversations_analyzed}")
        print(f"   • Timestamp: {metadata.get('timestamp', 'unknown')}")

if __name__ == '__main__':
    main()