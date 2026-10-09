"""
Startup script for Aura plagiarism detection system
Handles initial setup and launches the application
"""

import sys
import os
import subprocess
import platform

def check_python_version():
    """Check if Python version is compatible"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ Python 3.8 or higher is required")
        print(f"Current version: {version.major}.{version.minor}.{version.micro}")
        return False
    
    print(f"✅ Python version: {version.major}.{version.minor}.{version.micro}")
    return True

def install_dependencies():
    """Install required dependencies"""
    print("📦 Installing dependencies...")
    
    try:
        # Install from requirements.txt
        result = subprocess.run([
            sys.executable, "-m", "pip", "install", "-r", "requirements.txt"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Dependencies installed successfully")
            return True
        else:
            print(f"❌ Failed to install dependencies: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Error installing dependencies: {e}")
        return False

def download_nltk_data():
    """Download required NLTK data"""
    print("📥 Downloading NLTK data...")
    
    try:
        import nltk
        
        # Download required NLTK data
        nltk_downloads = [
            'punkt',
            'stopwords',
            'averaged_perceptron_tagger',
            'maxent_ne_chunker',
            'words'
        ]
        
        for download in nltk_downloads:
            try:
                nltk.download(download, quiet=True)
            except:
                print(f"⚠️ Could not download {download}, but continuing...")
        
        print("✅ NLTK data downloaded")
        return True
        
    except ImportError:
        print("⚠️ NLTK not installed, skipping NLTK data download")
        return True
    except Exception as e:
        print(f"⚠️ Error downloading NLTK data: {e}")
        return True  # Not critical, continue anyway

def download_spacy_model():
    """Download spaCy model if available"""
    print("📥 Attempting to download spaCy model...")
    
    try:
        result = subprocess.run([
            sys.executable, "-m", "spacy", "download", "en_core_web_sm"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ spaCy model downloaded")
        else:
            print("⚠️ Could not download spaCy model (optional, system will work without it)")
        
        return True
        
    except Exception as e:
        print("⚠️ Could not download spaCy model (optional, system will work without it)")
        return True

def setup_directories():
    """Setup required directories"""
    print("📁 Setting up directories...")
    
    directories = [
        "data",
        "data/backups",
        "logs"
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
    
    print("✅ Directories created")
    return True

def run_system_test():
    """Run system test"""
    print("🧪 Running system tests...")
    
    try:
        result = subprocess.run([
            sys.executable, "test_system.py"
        ], capture_output=True, text=True)
        
        print(result.stdout)
        
        if result.returncode == 0:
            print("✅ System tests passed")
            return True
        else:
            print("⚠️ Some system tests failed, but continuing...")
            if result.stderr:
                print(result.stderr)
            return True  # Continue even if tests fail
            
    except Exception as e:
        print(f"⚠️ Could not run system tests: {e}")
        return True  # Continue anyway

def launch_application():
    """Launch the Streamlit application"""
    print("🚀 Launching Aura application...")
    
    try:
        # Launch Streamlit app
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", "app.py",
            "--server.port", "8501",
            "--server.address", "localhost"
        ])
        
    except KeyboardInterrupt:
        print("\n👋 Application stopped by user")
    except Exception as e:
        print(f"❌ Error launching application: {e}")
        print("\n💡 You can try launching manually with:")
        print("   streamlit run app.py")

def main():
    """Main setup and launch function"""
    print("🔍 Aura - Academic Plagiarism Detection System")
    print("=" * 50)
    
    # Check Python version
    if not check_python_version():
        return False
    
    # Setup directories
    if not setup_directories():
        return False
    
    # Ask user if they want to install dependencies
    install_deps = input("\n📦 Install/update dependencies? (y/n): ").lower().strip()
    if install_deps in ['y', 'yes', '']:
        if not install_dependencies():
            print("⚠️ Dependency installation failed, but continuing...")
        
        # Download NLTK data
        download_nltk_data()
        
        # Download spaCy model
        download_spacy_model()
    
    # Run system test
    run_test = input("\n🧪 Run system tests? (y/n): ").lower().strip()
    if run_test in ['y', 'yes', '']:
        run_system_test()
    
    # Launch application
    launch_app = input("\n🚀 Launch the application? (y/n): ").lower().strip()
    if launch_app in ['y', 'yes', '']:
        launch_application()
    else:
        print("\n💡 To launch the application later, run:")
        print("   python startup.py")
        print("   or")
        print("   streamlit run app.py")
    
    return True

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 Setup interrupted by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        print("💡 Please check the error and try again")