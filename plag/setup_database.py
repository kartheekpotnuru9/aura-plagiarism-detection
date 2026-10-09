"""
Setup and Run Script for Aura Database Population
Installs dependencies and runs the database building process
"""

import subprocess
import sys
import os

def install_package(package):
    """Install a Python package using pip"""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        return True
    except subprocess.CalledProcessError:
        return False

def check_and_install_dependencies():
    """Check and install required dependencies"""
    required_packages = [
        'requests',
        'pandas',
        'matplotlib',
        'seaborn'
    ]
    
    print("🔍 Checking dependencies...")
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package)
            print(f"✅ {package} is available")
        except ImportError:
            missing_packages.append(package)
            print(f"❌ {package} is missing")
    
    if missing_packages:
        print(f"\n📦 Installing missing packages: {', '.join(missing_packages)}")
        for package in missing_packages:
            print(f"Installing {package}...")
            if install_package(package):
                print(f"✅ {package} installed successfully")
            else:
                print(f"❌ Failed to install {package}")
                return False
    
    return True

def main():
    """Main setup and execution"""
    print("🚀 Aura Database Setup and Population")
    print("=" * 50)
    
    # Check current directory
    if not os.path.exists('app.py'):
        print("❌ Please run this script from the Aura project directory")
        return
    
    # Install dependencies
    if not check_and_install_dependencies():
        print("❌ Failed to install dependencies")
        return
    
    print("\n✅ All dependencies are ready!")
    
    # Ask user what to do
    print("\n🎯 What would you like to do?")
    print("1. Build paper database (fetch ~100 ML papers from arXiv)")
    print("2. Analyze existing database")
    print("3. Both (recommended for first run)")
    
    choice = input("\nChoose option (1-3): ").strip()
    
    if choice in ['1', '3']:
        print("\n🔧 Building paper database...")
        print("This will take several minutes to download and process papers...")
        
        try:
            from build_arxiv_database import main as build_main
            results = build_main()
            print("\n✅ Database building completed!")
        except Exception as e:
            print(f"❌ Error building database: {e}")
            return
    
    if choice in ['2', '3']:
        print("\n📊 Analyzing database...")
        
        try:
            from analyze_database import main as analyze_main
            analyze_main()
        except Exception as e:
            print(f"❌ Error analyzing database: {e}")
            return
    
    print("\n🎉 Setup complete!")
    print("\nYour Aura system is now ready with a populated database.")
    print("You can run the main application with: python app.py")
    print("The system will now be much more effective at detecting plagiarism!")

if __name__ == "__main__":
    main()