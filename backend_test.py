
import requests
import os
import sys
import unittest
from pathlib import Path
import base64

class ResumeRoasterAPITester(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Get the backend URL from the frontend .env file
        env_path = Path("/app/frontend/.env")
        self.backend_url = None
        
        if env_path.exists():
            with open(env_path, "r") as f:
                for line in f:
                    if line.startswith("REACT_APP_BACKEND_URL="):
                        self.backend_url = line.strip().split("=")[1].strip('"')
                        break
        
        if not self.backend_url:
            self.backend_url = "https://e9da16de-b29e-4cdd-b1bc-ad2650167a64.preview.emergentagent.com"
        
        self.api_url = f"{self.backend_url}/api"
        print(f"Using API URL: {self.api_url}")
        
        # Create a sample PDF file for testing
        self.sample_pdf_path = "/tmp/sample_resume.pdf"
        self.create_sample_pdf()
        
        # Sample Google Drive link for testing
        self.sample_gdrive_link = "https://drive.google.com/file/d/1234567890abcdef/view?usp=sharing"

    def create_sample_pdf(self):
        """Create a simple PDF file for testing"""
        try:
            # Create a very basic PDF content
            pdf_content = b"%PDF-1.4\n1 0 obj\n<</Type/Catalog/Pages 2 0 R>>\nendobj\n2 0 obj\n<</Type/Pages/Kids[3 0 R]/Count 1>>\nendobj\n3 0 obj\n<</Type/Page/MediaBox[0 0 612 792]/Contents 4 0 R/Resources<<>>>>\nendobj\n4 0 obj\n<</Length 22>>\nstream\nBT /F1 12 Tf (Sample Resume) Tj ET\nendstream\nendobj\nxref\n0 5\n0000000000 65535 f\n0000000010 00000 n\n0000000053 00000 n\n0000000102 00000 n\n0000000182 00000 n\ntrailer\n<</Size 5/Root 1 0 R>>\nstartxref\n254\n%%EOF"
            
            with open(self.sample_pdf_path, "wb") as f:
                f.write(pdf_content)
            
            print(f"Created sample PDF at {self.sample_pdf_path}")
        except Exception as e:
            print(f"Error creating sample PDF: {e}")

    def test_01_api_root(self):
        """Test the API root endpoint"""
        print("\n🔍 Testing API root endpoint...")
        try:
            response = requests.get(f"{self.api_url}/")
            self.assertEqual(response.status_code, 200)
            self.assertIn("message", response.json())
            print("✅ API root endpoint test passed")
        except Exception as e:
            print(f"❌ API root endpoint test failed: {e}")
            raise

    def test_02_upload_resume_with_file(self):
        """Test uploading a resume file"""
        print("\n🔍 Testing resume upload with file...")
        try:
            with open(self.sample_pdf_path, "rb") as f:
                files = {"file": ("sample_resume.pdf", f, "application/pdf")}
                response = requests.post(f"{self.api_url}/upload-resume", files=files)
            
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertIn("id", data)
            self.assertIn("roast", data)
            self.assertIn("review", data)
            print("✅ Resume upload with file test passed")
            return data
        except Exception as e:
            print(f"❌ Resume upload with file test failed: {e}")
            raise

    def test_03_upload_resume_with_gdrive_link(self):
        """Test uploading a resume with Google Drive link"""
        print("\n🔍 Testing resume upload with Google Drive link...")
        try:
            data = {"gdrive_link": self.sample_gdrive_link}
            response = requests.post(f"{self.api_url}/upload-resume", data=data)
            
            # This might fail if the Google Drive link is not valid or accessible
            # We'll check for either success or a specific error
            if response.status_code == 200:
                data = response.json()
                self.assertIn("id", data)
                self.assertIn("roast", data)
                self.assertIn("review", data)
                print("✅ Resume upload with Google Drive link test passed")
            else:
                # Check if it's a specific error about Google Drive access
                error_msg = response.json().get("detail", "")
                if "Failed to extract text from Google Drive link" in error_msg:
                    print("⚠️ Google Drive link test skipped: Link not accessible (expected)")
                else:
                    self.fail(f"Unexpected error: {error_msg}")
        except Exception as e:
            print(f"❌ Resume upload with Google Drive link test failed: {e}")
            raise

    def test_04_upload_invalid_file_type(self):
        """Test uploading an invalid file type"""
        print("\n🔍 Testing upload with invalid file type...")
        try:
            # Create a text file
            invalid_file_path = "/tmp/invalid_file.txt"
            with open(invalid_file_path, "w") as f:
                f.write("This is not a valid resume file")
            
            with open(invalid_file_path, "rb") as f:
                files = {"file": ("invalid_file.txt", f, "text/plain")}
                response = requests.post(f"{self.api_url}/upload-resume", files=files)
            
            self.assertEqual(response.status_code, 400)
            error_msg = response.json().get("detail", "")
            self.assertIn("Unsupported file format", error_msg)
            print("✅ Invalid file type test passed")
        except Exception as e:
            print(f"❌ Invalid file type test failed: {e}")
            raise

    def test_05_missing_input(self):
        """Test uploading with no file or link"""
        print("\n🔍 Testing upload with no file or link...")
        try:
            response = requests.post(f"{self.api_url}/upload-resume")
            
            self.assertEqual(response.status_code, 400)
            error_msg = response.json().get("detail", "")
            self.assertIn("No file or Google Drive link provided", error_msg)
            print("✅ Missing input test passed")
        except Exception as e:
            print(f"❌ Missing input test failed: {e}")
            raise

    def run_all_tests(self):
        """Run all tests and return results"""
        tests = [
            self.test_01_api_root,
            self.test_02_upload_resume_with_file,
            self.test_03_upload_resume_with_gdrive_link,
            self.test_04_upload_invalid_file_type,
            self.test_05_missing_input
        ]
        
        results = {
            "total": len(tests),
            "passed": 0,
            "failed": 0,
            "errors": []
        }
        
        for test in tests:
            try:
                test()
                results["passed"] += 1
            except Exception as e:
                results["failed"] += 1
                results["errors"].append(f"{test.__name__}: {str(e)}")
        
        return results

def main():
    tester = ResumeRoasterAPITester()
    results = tester.run_all_tests()
    
    print("\n📊 Test Results:")
    print(f"Total tests: {results['total']}")
    print(f"Passed: {results['passed']}")
    print(f"Failed: {results['failed']}")
    
    if results["errors"]:
        print("\nErrors:")
        for error in results["errors"]:
            print(f"- {error}")
    
    return 0 if results["failed"] == 0 else 1

if __name__ == "__main__":
    sys.exit(main())
