#!/usr/bin/env python3
"""
System Performance Detection Script for Synapse AI

This script detects your system's hardware capabilities and suggests
optimal timeout configurations for the best Synapse AI experience.
"""

import os
import sys
import psutil
import platform
from pathlib import Path


def detect_system_specs():
    """Detect system hardware specifications"""
    specs = {
        'cpu_cores': psutil.cpu_count(logical=False),  # Physical cores
        'cpu_threads': psutil.cpu_count(logical=True),  # Logical cores
        'memory_gb': round(psutil.virtual_memory().total / (1024**3), 1),
        'platform': platform.system(),
        'architecture': platform.machine(),
        'python_version': platform.python_version()
    }
    
    # Get CPU frequency if available
    try:
        cpu_freq = psutil.cpu_freq()
        if cpu_freq:
            specs['cpu_freq_ghz'] = round(cpu_freq.max / 1000, 2) if cpu_freq.max else None
    except:
        specs['cpu_freq_ghz'] = None
    
    return specs


def classify_performance_level(specs):
    """Classify system performance level based on specs"""
    cpu_cores = specs['cpu_cores']
    memory_gb = specs['memory_gb']
    
    # Performance classification logic
    if cpu_cores <= 2 or memory_gb <= 2:
        return 'low'
    elif cpu_cores >= 8 and memory_gb >= 8:
        return 'high'
    else:
        return 'medium'


def get_recommended_timeouts(performance_level):
    """Get recommended timeout settings based on performance level"""
    recommendations = {
        'low': {
            'RESPONSE_TIMEOUT': 120,
            'STREAMING_TIMEOUT': 300,
            'OLLAMA_TIMEOUT': 60,
            'description': 'Conservative timeouts for slower systems'
        },
        'medium': {
            'RESPONSE_TIMEOUT': 60,
            'STREAMING_TIMEOUT': 180,
            'OLLAMA_TIMEOUT': 30,
            'description': 'Balanced timeouts for standard systems'
        },
        'high': {
            'RESPONSE_TIMEOUT': 30,
            'STREAMING_TIMEOUT': 90,
            'OLLAMA_TIMEOUT': 15,
            'description': 'Optimized timeouts for high-performance systems'
        }
    }
    
    return recommendations.get(performance_level, recommendations['medium'])


def create_env_file(recommendations, specs):
    """Create or update .env file with recommended settings"""
    env_path = Path('.env')
    env_example_path = Path('.env.example')
    
    # Read existing .env or use .env.example as template
    if env_path.exists():
        print(f"📝 Updating existing {env_path}")
        with open(env_path, 'r') as f:
            content = f.read()
    elif env_example_path.exists():
        print(f"📝 Creating {env_path} from {env_example_path}")
        with open(env_example_path, 'r') as f:
            content = f.read()
    else:
        print(f"📝 Creating new {env_path}")
        content = "# Synapse AI Configuration\n"
    
    # Update timeout values
    lines = content.split('\n')
    updated_lines = []
    updated_keys = set()
    
    for line in lines:
        if '=' in line and not line.strip().startswith('#'):
            key = line.split('=')[0].strip()
            if key in recommendations:
                updated_lines.append(f"{key}={recommendations[key]}")
                updated_keys.add(key)
            else:
                updated_lines.append(line)
        else:
            updated_lines.append(line)
    
    # Add any missing timeout configurations
    for key, value in recommendations.items():
        if key not in updated_keys and key != 'description':
            updated_lines.append(f"{key}={value}")
    
    # Add system detection comment
    updated_lines.append(f"\n# System detected: {specs['cpu_cores']} cores, {specs['memory_gb']}GB RAM")
    updated_lines.append(f"# Performance level: {classify_performance_level(specs)}")
    updated_lines.append(f"# Timeouts optimized for your system on {platform.node()}")
    
    # Write updated content
    with open(env_path, 'w') as f:
        f.write('\n'.join(updated_lines))
    
    print(f"✅ Configuration saved to {env_path}")


def main():
    """Main function to detect system and configure timeouts"""
    print("🔍 Synapse AI System Performance Detection")
    print("=" * 50)
    
    # Detect system specifications
    print("Detecting system specifications...")
    specs = detect_system_specs()
    
    # Display system information
    print(f"\n💻 System Information:")
    print(f"   Platform: {specs['platform']} ({specs['architecture']})")
    print(f"   CPU Cores: {specs['cpu_cores']} physical, {specs['cpu_threads']} logical")
    if specs['cpu_freq_ghz']:
        print(f"   CPU Frequency: {specs['cpu_freq_ghz']} GHz")
    print(f"   Memory: {specs['memory_gb']} GB")
    print(f"   Python: {specs['python_version']}")
    
    # Classify performance level
    performance_level = classify_performance_level(specs)
    print(f"\n📊 Performance Level: {performance_level.upper()}")
    
    # Get recommendations
    recommendations = get_recommended_timeouts(performance_level)
    print(f"\n⚙️  Recommended Settings:")
    print(f"   {recommendations['description']}")
    print(f"   Response Timeout: {recommendations['RESPONSE_TIMEOUT']} seconds")
    print(f"   Streaming Timeout: {recommendations['STREAMING_TIMEOUT']} seconds")
    print(f"   Ollama Timeout: {recommendations['OLLAMA_TIMEOUT']} seconds")
    
    # Ask user if they want to apply settings
    print(f"\n❓ Apply these settings to your .env file?")
    response = input("   Enter 'y' to apply, 'n' to skip: ").lower().strip()
    
    if response in ['y', 'yes']:
        try:
            create_env_file(recommendations, specs)
            print(f"\n🎉 Configuration complete!")
            print(f"   Restart Synapse AI to apply the new timeout settings.")
            
            # Performance tips
            print(f"\n💡 Performance Tips:")
            if performance_level == 'low':
                print(f"   • Your system may need extra time for AI processing")
                print(f"   • Consider using shorter, simpler questions for faster responses")
                print(f"   • Close other applications when using Synapse AI")
            elif performance_level == 'high':
                print(f"   • Your system should handle complex AI requests quickly")
                print(f"   • You can use streaming mode for real-time responses")
                print(f"   • Consider running multiple AI models simultaneously")
            else:
                print(f"   • Your system should handle most AI requests well")
                print(f"   • Use streaming mode for better user experience")
                print(f"   • Monitor performance and adjust timeouts if needed")
                
        except Exception as e:
            print(f"❌ Error creating configuration: {e}")
            sys.exit(1)
    else:
        print(f"\n📋 Manual Configuration:")
        print(f"   Add these lines to your .env file:")
        for key, value in recommendations.items():
            if key != 'description':
                print(f"   {key}={value}")
    
    print(f"\n🔧 You can also manually adjust timeouts in .env based on your experience.")
    print(f"   Higher values = more patience for slower responses")
    print(f"   Lower values = faster timeout for quicker feedback")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n👋 Detection cancelled by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)