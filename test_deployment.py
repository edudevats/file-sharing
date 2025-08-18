#!/usr/bin/env python3
"""
Test script to verify deployment path configuration
This simulates what happens during deployment
"""
import os
import sys
import tempfile
import shutil

def test_deployment_initialization():
    """Test deployment initialization without running the full app"""
    print("="*60)
    print("TESTING DEPLOYMENT INITIALIZATION")
    print("="*60)
    
    # Save current working directory
    original_wd = os.getcwd()
    
    try:
        # Test 1: Import and initialize deployment
        print("\n1. Testing deployment initialization...")
        from deploy_init import initialize_deployment
        
        paths = initialize_deployment()
        
        # Test 2: Verify all paths are within project
        print("\n2. Verifying all paths are within project directory...")
        project_root = paths['base_dir']
        
        all_paths_correct = True
        for name, path in paths.items():
            if not path.startswith(project_root):
                print(f"[ERROR] {name} path is outside project: {path}")
                all_paths_correct = False
            else:
                print(f"[OK] {name}: {path}")
        
        # Test 3: Verify working directory
        print("\n3. Verifying working directory...")
        current_wd = os.getcwd()
        if current_wd == project_root:
            print(f"[OK] Working directory correct: {current_wd}")
        else:
            print(f"[ERROR] Working directory incorrect: {current_wd} (expected: {project_root})")
            all_paths_correct = False
        
        # Test 4: Verify directories exist
        print("\n4. Verifying directories exist...")
        for name, path in paths.items():
            if name == 'database':
                # Check parent directory for database
                parent_dir = os.path.dirname(path)
                if os.path.exists(parent_dir):
                    print(f"[OK] Database parent directory exists: {parent_dir}")
                else:
                    print(f"[ERROR] Database parent directory missing: {parent_dir}")
                    all_paths_correct = False
            elif name in ['uploads', 'logos', 'static_css', 'static_js']:
                if os.path.exists(path):
                    print(f"[OK] Directory exists: {path}")
                else:
                    print(f"[ERROR] Directory missing: {path}")
                    all_paths_correct = False
        
        # Test 5: Test database service initialization
        print("\n5. Testing database service initialization...")
        try:
            from database_service import DatabaseService
            db_service = DatabaseService()
            
            expected_db_path = paths['database']
            actual_db_path = db_service.db_path
            
            if actual_db_path == expected_db_path:
                print(f"[OK] Database service path correct: {actual_db_path}")
            else:
                print(f"[ERROR] Database service path incorrect:")
                print(f"  Expected: {expected_db_path}")
                print(f"  Actual: {actual_db_path}")
                all_paths_correct = False
            
            # Verify database path is within project
            if actual_db_path.startswith(project_root):
                print(f"[OK] Database path within project directory")
            else:
                print(f"[ERROR] Database path outside project directory!")
                all_paths_correct = False
                
        except Exception as e:
            print(f"[ERROR] Error testing database service: {e}")
            all_paths_correct = False
        
        # Final result
        print("\n" + "="*60)
        if all_paths_correct:
            print("[SUCCESS] DEPLOYMENT TEST PASSED!")
            print("All paths are correctly configured within the project directory.")
        else:
            print("[FAILED] DEPLOYMENT TEST FAILED!")
            print("Some paths are not correctly configured.")
        print("="*60)
        
        return all_paths_correct
        
    except Exception as e:
        print(f"CRITICAL ERROR during deployment test: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # Restore original working directory
        os.chdir(original_wd)

def test_simulated_deployment():
    """Simulate deployment in a different directory"""
    print("\n" + "="*60)
    print("TESTING SIMULATED DEPLOYMENT (Different Working Directory)")
    print("="*60)
    
    # Create a temporary directory to simulate deployment
    with tempfile.TemporaryDirectory() as temp_dir:
        print(f"Simulating deployment in: {temp_dir}")
        
        # Copy the project files to temp directory
        project_files = [
            'deploy_init.py',
            'database_service.py',
            'app.py',
            'db_wrapper.py'
        ]
        
        for file in project_files:
            if os.path.exists(file):
                shutil.copy2(file, temp_dir)
                print(f"Copied: {file}")
        
        # Change to temp directory (simulating deployment environment)
        original_wd = os.getcwd()
        os.chdir(temp_dir)
        
        try:
            print(f"Changed working directory to: {os.getcwd()}")
            
            # Test deployment initialization in this new environment
            sys.path.insert(0, temp_dir)
            
            # Import and test deployment
            import deploy_init
            paths = deploy_init.initialize_deployment()
            
            # Verify paths are in the temp directory (simulated deployment location)
            temp_dir_abs = os.path.abspath(temp_dir)
            
            all_correct = True
            for name, path in paths.items():
                if not path.startswith(temp_dir_abs):
                    print(f"[ERROR] {name} not in deployment directory: {path}")
                    all_correct = False
                else:
                    print(f"[OK] {name} correctly in deployment directory")
            
            if all_correct:
                print("[SUCCESS] SIMULATED DEPLOYMENT TEST PASSED!")
            else:
                print("[FAILED] SIMULATED DEPLOYMENT TEST FAILED!")
            
            return all_correct
            
        except Exception as e:
            print(f"Error in simulated deployment: {e}")
            import traceback
            traceback.print_exc()
            return False
        finally:
            os.chdir(original_wd)
            if temp_dir in sys.path:
                sys.path.remove(temp_dir)

if __name__ == "__main__":
    print("EY File Sharing - Deployment Test Suite")
    
    success1 = test_deployment_initialization()
    success2 = test_simulated_deployment()
    
    print("\n" + "="*60)
    print("FINAL TEST RESULTS")
    print("="*60)
    print(f"Deployment Initialization: {'[PASS]' if success1 else '[FAIL]'}")
    print(f"Simulated Deployment: {'[PASS]' if success2 else '[FAIL]'}")
    
    if success1 and success2:
        print("\n[SUCCESS] ALL TESTS PASSED! Deployment should work correctly.")
        sys.exit(0)
    else:
        print("\n[FAILED] SOME TESTS FAILED! Please check the configuration.")
        sys.exit(1)