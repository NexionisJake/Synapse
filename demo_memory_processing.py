#!/usr/bin/env python3
"""
Memory Processing Demonstration Script

This script demonstrates the memory processing and insight generation
functionality of the Synapse AI webapp.
"""

import json
import os
from memory_service import get_memory_service, MemoryServiceError

def demo_memory_processing():
    """Demonstrate memory processing functionality"""
    print("=== Synapse Memory Processing Demo ===\n")
    
    # Sample conversation for demonstration
    sample_conversation = [
        {"role": "user", "content": "I've been thinking about starting a new career in data science"},
        {"role": "assistant", "content": "That's exciting! What draws you to data science specifically?"},
        {"role": "user", "content": "I love working with numbers and finding patterns in data. I have a background in mathematics and I've been learning Python"},
        {"role": "assistant", "content": "Your math background will be very valuable! Python is an excellent choice for data science. What areas of data science interest you most?"},
        {"role": "user", "content": "I'm particularly interested in machine learning and predictive analytics. I want to help businesses make better decisions"},
        {"role": "assistant", "content": "Machine learning and predictive analytics are fascinating fields with huge business impact. Have you worked on any projects yet?"}
    ]
    
    print("Sample Conversation:")
    print("-" * 50)
    for i, message in enumerate(sample_conversation):
        role = message['role'].title()
        content = message['content']
        print(f"{role}: {content}")
        if i < len(sample_conversation) - 1:
            print()
    
    print("\n" + "=" * 60)
    print("Processing conversation for memory insights...")
    print("=" * 60)
    
    try:
        # Get memory service instance
        memory_service = get_memory_service(
            model="llama3:8b",
            memory_file="demo_memory.json"
        )
        
        # Note: This will fail if Ollama is not running or model is not available
        # In a real scenario, you would have Ollama running with the model
        print("\nAttempting to extract insights...")
        print("(Note: This requires Ollama to be running with llama3:8b model)")
        
        # Process the conversation
        result = memory_service.process_conversation(sample_conversation)
        
        print(f"\n✅ Successfully processed conversation!")
        print(f"📊 Insights extracted: {result['insights_extracted']}")
        print(f"📝 Conversation summary: {result['conversation_summary']}")
        print(f"🏷️  Key themes: {', '.join(result['key_themes'])}")
        
        # Show memory statistics
        stats = result['memory_stats']
        print(f"\n📈 Memory Statistics:")
        print(f"   Total insights: {stats['total_insights']}")
        print(f"   Total conversations: {stats['total_conversations']}")
        print(f"   Memory file exists: {stats['memory_file_exists']}")
        
        # Show the memory file content if it exists
        if os.path.exists("demo_memory.json"):
            print(f"\n📄 Memory file content:")
            with open("demo_memory.json", 'r') as f:
                memory_data = json.load(f)
                print(json.dumps(memory_data, indent=2))
        
    except MemoryServiceError as e:
        print(f"\n❌ Memory service error: {e}")
        print("\nThis is expected if Ollama is not running or the model is not available.")
        print("To run this demo successfully:")
        print("1. Install Ollama: https://ollama.ai/")
        print("2. Pull the model: ollama pull llama3:8b")
        print("3. Start Ollama service")
        
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
    
    print("\n" + "=" * 60)
    print("Demo completed!")
    print("=" * 60)

def demo_memory_file_structure():
    """Demonstrate the memory file structure"""
    print("\n=== Memory File Structure Demo ===\n")
    
    # Create a sample memory structure
    sample_memory = {
        "insights": [
            {
                "category": "career_goals",
                "content": "User is interested in transitioning to data science career",
                "confidence": 0.9,
                "tags": ["career", "data_science", "transition"],
                "evidence": "I've been thinking about starting a new career in data science",
                "timestamp": "2024-01-01T12:00:00",
                "source_conversation_length": 6
            },
            {
                "category": "technical_skills",
                "content": "User has mathematics background and is learning Python",
                "confidence": 0.8,
                "tags": ["mathematics", "python", "programming"],
                "evidence": "I have a background in mathematics and I've been learning Python",
                "timestamp": "2024-01-01T12:00:00",
                "source_conversation_length": 6
            },
            {
                "category": "interests",
                "content": "User enjoys working with data patterns and numbers",
                "confidence": 0.85,
                "tags": ["data_analysis", "patterns", "numbers"],
                "evidence": "I love working with numbers and finding patterns in data",
                "timestamp": "2024-01-01T12:00:00",
                "source_conversation_length": 6
            }
        ],
        "conversation_summaries": [
            {
                "timestamp": "2024-01-01T12:00:00",
                "summary": "Discussion about career transition to data science",
                "key_themes": ["career_change", "data_science", "machine_learning"],
                "insights_count": 3
            }
        ],
        "metadata": {
            "total_insights": 3,
            "last_updated": "2024-01-01T12:00:00",
            "version": "1.0"
        }
    }
    
    print("Sample Memory File Structure:")
    print("-" * 40)
    print(json.dumps(sample_memory, indent=2))
    
    print("\n📋 Key Components:")
    print("• insights: Array of extracted insights with metadata")
    print("• conversation_summaries: Summaries of processed conversations")
    print("• metadata: Overall statistics and file information")
    
    print("\n🔍 Insight Structure:")
    print("• category: Type of insight (interests, skills, goals, etc.)")
    print("• content: Human-readable description of the insight")
    print("• confidence: AI confidence level (0.0 to 1.0)")
    print("• tags: Keywords for categorization and search")
    print("• evidence: Supporting quote from conversation")
    print("• timestamp: When the insight was extracted")

if __name__ == "__main__":
    demo_memory_processing()
    demo_memory_file_structure()