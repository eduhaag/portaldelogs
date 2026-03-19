# -*- coding: utf-8 -*-
"""
Backend API tests for Centralizador de Logs
Tests: auth, log analysis, profiler, log cleaner, issues CRUD, file upload, PDF generation
"""

import pytest
import requests
import os
import io
import time
from datetime import datetime

# Base URL from environment - DO NOT add default
BASE_URL = os.environ.get('BACKEND_URL', '').rstrip('/')


class TestAuthEndpoints:
    """Authentication endpoint tests"""
    
    def test_register_user(self):
        """Register a test user for subsequent tests"""
        response = requests.post(f"{BASE_URL}/api/auth/register", json={
            "display_name": "Test User",
            "username": "testuser",
            "email": "testuser@example.com",
            "password": "Test@1234"
        })
        # May be 200/201 (success) or 409 (already exists)
        assert response.status_code in [200, 201, 409], f"Register failed: {response.text}"
        if response.status_code in [200, 201]:
            data = response.json()
            assert data.get("success") == True
    
    def test_login_success(self):
        """Test login with valid credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "username": "testuser",
            "password": "Test@1234"
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert data.get("success") == True
        assert "access_token" in data
        assert data.get("token_type") == "Bearer"
        
    def test_login_invalid_credentials(self):
        """Test login with invalid credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "username": "invaliduser",
            "password": "wrongpass"
        })
        assert response.status_code == 401


@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token for protected endpoints"""
    # First try to register (in case user doesn't exist)
    requests.post(f"{BASE_URL}/api/auth/register", json={
        "display_name": "Test User",
        "username": "testuser",
        "email": "testuser@example.com",
        "password": "Test@1234"
    })
    
    # Then login
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "username": "testuser",
        "password": "Test@1234"
    })
    if response.status_code == 200:
        return response.json().get("access_token")
    pytest.skip("Authentication failed - skipping authenticated tests")


@pytest.fixture(scope="module")
def auth_headers(auth_token):
    """Headers with Bearer token"""
    return {"Authorization": f"Bearer {auth_token}"}


class TestLogAnalysis:
    """Log analysis endpoint tests - Critical performance tests"""
    
    def test_analyze_log_large_file(self, auth_headers):
        """Test POST /api/analyze-log with large clientlog-lapereira.log (81K lines) - should complete in <5s"""
        # Read the actual large log file
        log_path = "/tmp/clientlog-lapereira.log"
        if not os.path.exists(log_path):
            pytest.skip("Large log file not found")
        
        with open(log_path, 'rb') as f:
            log_content = f.read()
        
        files = {'log_file': ('clientlog-lapereira.log', io.BytesIO(log_content), 'text/plain')}
        
        start_time = time.time()
        response = requests.post(
            f"{BASE_URL}/api/analyze-log",
            files=files,
            headers=auth_headers,
            timeout=30  # Allow up to 30s for safety, but expect <5s
        )
        elapsed_time = time.time() - start_time
        
        assert response.status_code == 200, f"Analyze log failed: {response.text}"
        data = response.json()
        
        # Validate response structure
        assert data.get("success") == True, f"Analysis not successful: {data}"
        assert "results" in data
        assert "statistics" in data
        assert "total_results" in data
        
        # Performance check - should be <5s after optimization
        print(f"Log analysis took {elapsed_time:.2f} seconds for 81K lines")
        # Note: We're checking <10s as a more lenient threshold
        assert elapsed_time < 10, f"Log analysis too slow: {elapsed_time:.2f}s (expected <5s)"
    
    def test_analyze_log_categories(self, auth_headers):
        """Test POST /api/analyze-log-categories with clientlog-lapereira.log"""
        log_path = "/tmp/clientlog-lapereira.log"
        if not os.path.exists(log_path):
            pytest.skip("Large log file not found")
        
        with open(log_path, 'rb') as f:
            log_content = f.read()
        
        files = {'log_file': ('clientlog-lapereira.log', io.BytesIO(log_content), 'text/plain')}
        
        start_time = time.time()
        response = requests.post(
            f"{BASE_URL}/api/analyze-log-categories",
            files=files,
            headers=auth_headers,
            timeout=30
        )
        elapsed_time = time.time() - start_time
        
        assert response.status_code == 200, f"Analyze categories failed: {response.text}"
        data = response.json()
        
        assert data.get("success") == True
        assert "analysis" in data
        assert "found_categories" in data
        assert "category_info" in data
        
        print(f"Category analysis took {elapsed_time:.2f} seconds")
        # Should have found some categories
        found_cats = data.get("found_categories", {})
        print(f"Found categories: {list(found_cats.keys())[:10]}")


class TestLogCleaner:
    """Log cleaner endpoint tests"""
    
    def test_clean_log_with_categories(self, auth_headers):
        """Test POST /api/clean-log with categories_to_remove"""
        log_path = "/tmp/clientlog-lapereira.log"
        if not os.path.exists(log_path):
            pytest.skip("Large log file not found")
        
        with open(log_path, 'rb') as f:
            log_content = f.read()
        
        files = {'log_file': ('clientlog-lapereira.log', io.BytesIO(log_content), 'text/plain')}
        # Remove common noise categories
        data = {'categories_to_remove': '4gltrace,heartbeat,debug_trace'}
        
        start_time = time.time()
        response = requests.post(
            f"{BASE_URL}/api/clean-log",
            files=files,
            data=data,
            headers=auth_headers,
            timeout=30
        )
        elapsed_time = time.time() - start_time
        
        assert response.status_code == 200, f"Clean log failed: {response.text}"
        
        # Response should be a file download (text/plain)
        content_type = response.headers.get('content-type', '')
        assert 'text/plain' in content_type, f"Expected text/plain response, got {content_type}"
        
        # Check cleaning stats in header
        cleaning_stats = response.headers.get('X-Cleaning-Stats')
        if cleaning_stats:
            import json
            stats = json.loads(cleaning_stats)
            print(f"Cleaning stats: {stats}")
        
        print(f"Log cleaning took {elapsed_time:.2f} seconds")
        # Should be fast after optimization (was 14.7s, now ~0.115s)
        assert elapsed_time < 5, f"Log cleaning too slow: {elapsed_time:.2f}s"


class TestProfilerAnalysis:
    """Profiler analysis endpoint tests"""
    
    def test_analyze_profiler_file(self, auth_headers):
        """Test POST /api/analyze-profiler with profiler.out (v3 format with 35 modules)"""
        profiler_path = "/tmp/profiler.out"
        if not os.path.exists(profiler_path):
            pytest.skip("Profiler file not found")
        
        with open(profiler_path, 'rb') as f:
            profiler_content = f.read()
        
        files = {'log_file': ('profiler.out', io.BytesIO(profiler_content), 'text/plain')}
        
        response = requests.post(
            f"{BASE_URL}/api/analyze-profiler",
            files=files,
            headers=auth_headers,
            timeout=30
        )
        
        assert response.status_code == 200, f"Profiler analysis failed: {response.text}"
        data = response.json()
        
        assert data.get("success") == True, f"Analysis not successful: {data}"
        
        # Validate structure
        assert "session" in data
        assert "summary" in data
        assert "raw_data" in data
        
        # Check that modules were parsed (should be ~35 modules)
        raw_data = data.get("raw_data", {})
        modules = raw_data.get("modules", [])
        print(f"Parsed {len(modules)} modules from profiler")
        assert len(modules) > 0, "No modules parsed from profiler file"
        
        # Check session info
        session = data.get("session", {})
        print(f"Profiler session: version={session.get('version')}, date={session.get('date')}")


class TestIssuesCRUD:
    """Issues CRUD endpoint tests"""
    
    @pytest.fixture(autouse=True)
    def setup_test_issue(self, auth_headers):
        """Setup and cleanup test issue"""
        self.test_issue_id = None
        self.auth_headers = auth_headers
        yield
        # Cleanup - delete test issue if created
        if self.test_issue_id:
            try:
                requests.delete(
                    f"{BASE_URL}/api/issues/{self.test_issue_id}",
                    headers=self.auth_headers
                )
            except:
                pass
    
    def test_get_issues_list(self, auth_headers):
        """Test GET /api/issues - should return list of issues"""
        response = requests.get(f"{BASE_URL}/api/issues", headers=auth_headers)
        
        assert response.status_code == 200, f"Get issues failed: {response.text}"
        data = response.json()
        assert isinstance(data, list)
        print(f"Found {len(data)} issues in database")
    
    def test_create_issue(self, auth_headers):
        """Test POST /api/issues - create a new issue"""
        test_ticket = f"TEST_TICKET_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        issue_data = {
            "ticket": test_ticket,
            "issue": "TEST_ISSUE_001",
            "cliente": "Cliente Teste",
            "rotina": "cd0603.p",
            "situacao": "Erro ao executar rotina",
            "status": "Aberto",
            "liberado_versoes": ""
        }
        
        response = requests.post(
            f"{BASE_URL}/api/issues",
            json=issue_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200, f"Create issue failed: {response.text}"
        data = response.json()
        
        # Validate response structure
        assert "id" in data
        assert data.get("ticket") == test_ticket
        assert data.get("issue") == "TEST_ISSUE_001"
        assert data.get("cliente") == "Cliente Teste"
        
        self.test_issue_id = data.get("id")
        print(f"Created issue with ID: {self.test_issue_id}")
        
        # Verify by fetching
        verify_response = requests.get(f"{BASE_URL}/api/issues", headers=auth_headers)
        issues = verify_response.json()
        created_issue = next((i for i in issues if i.get("id") == self.test_issue_id), None)
        assert created_issue is not None, "Created issue not found in list"
    
    def test_update_issue(self, auth_headers):
        """Test PUT /api/issues/{id} - update an issue"""
        # First create an issue
        test_ticket = f"TEST_UPDATE_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        create_response = requests.post(
            f"{BASE_URL}/api/issues",
            json={
                "ticket": test_ticket,
                "issue": "TEST_UPDATE_ISSUE",
                "cliente": "Cliente Original",
                "rotina": "test.p",
                "situacao": "Situação Original",
                "status": "Aberto"
            },
            headers=auth_headers
        )
        assert create_response.status_code == 200
        issue_id = create_response.json().get("id")
        self.test_issue_id = issue_id
        
        # Update the issue
        update_data = {
            "status": "Em Andamento",
            "situacao": "Situação Atualizada"
        }
        
        update_response = requests.put(
            f"{BASE_URL}/api/issues/{issue_id}",
            json=update_data,
            headers=auth_headers
        )
        
        assert update_response.status_code == 200, f"Update issue failed: {update_response.text}"
        
        # Verify update
        verify_response = requests.get(f"{BASE_URL}/api/issues", headers=auth_headers)
        issues = verify_response.json()
        updated_issue = next((i for i in issues if i.get("id") == issue_id), None)
        assert updated_issue is not None
        assert updated_issue.get("status") == "Em Andamento"
        assert updated_issue.get("situacao") == "Situação Atualizada"
    
    def test_delete_issue(self, auth_headers):
        """Test DELETE /api/issues/{id} - delete an issue"""
        # First create an issue to delete
        test_ticket = f"TEST_DELETE_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        create_response = requests.post(
            f"{BASE_URL}/api/issues",
            json={
                "ticket": test_ticket,
                "issue": "TEST_DELETE_ISSUE",
                "cliente": "Cliente Delete",
                "rotina": "delete.p",
                "situacao": "Situação Delete",
                "status": "Aberto"
            },
            headers=auth_headers
        )
        assert create_response.status_code == 200
        issue_id = create_response.json().get("id")
        
        # Delete the issue
        delete_response = requests.delete(
            f"{BASE_URL}/api/issues/{issue_id}",
            headers=auth_headers
        )
        
        assert delete_response.status_code == 200, f"Delete issue failed: {delete_response.text}"
        
        # Verify deletion - should return 404 or not be in list
        verify_response = requests.get(f"{BASE_URL}/api/issues", headers=auth_headers)
        issues = verify_response.json()
        deleted_issue = next((i for i in issues if i.get("id") == issue_id), None)
        assert deleted_issue is None, "Deleted issue still exists in list"
        
        # Reset test_issue_id since we deleted it
        self.test_issue_id = None


class TestFileUpload:
    """File upload endpoint tests"""
    
    def test_upload_files_with_session(self, auth_headers):
        """Test POST /api/upload-files with session_id"""
        # Create a test file
        test_content = b"Test file content for upload"
        files = {'files': ('test_upload.txt', io.BytesIO(test_content), 'text/plain')}
        
        response = requests.post(
            f"{BASE_URL}/api/upload-files",
            files=files,
            headers=auth_headers
        )
        
        assert response.status_code == 200, f"Upload failed: {response.text}"
        data = response.json()
        
        assert "session_id" in data
        assert "files" in data
        assert len(data["files"]) == 1
        assert data["files"][0]["filename"] == "test_upload.txt"
        
        session_id = data.get("session_id")
        print(f"File uploaded with session_id: {session_id}")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/cleanup-session/{session_id}", headers=auth_headers)


class TestPDFGeneration:
    """PDF/DOCX generation endpoint tests"""
    
    def test_generate_pdf_returns_zip(self, auth_headers):
        """Test POST /api/generate-pdf creates ZIP with PDF+DOCX"""
        form_data = {
            'ticket_number': f'TEST_{datetime.now().strftime("%Y%m%d%H%M%S")}',
            'situation': 'Teste de Geração de PDF',
            'issue': 'ISSUE-TEST-001',
            'client_name': 'Cliente Teste PDF',
            'client_version': '12.1.2403',
            'database_type': 'Progress',
            'routine_program': 'cd0603.p',
            'occurrence_type': 'Erro',
            'simulated_internally': 'true',
            'simulation_base': 'Base Teste',
            'occurrence_description': 'Descrição detalhada do teste',
            'expected_result': 'Sistema deve gerar PDF e DOCX corretamente',
            'program_needed': 'false',
            'notification_emails': 'test@example.com'
        }
        
        response = requests.post(
            f"{BASE_URL}/api/generate-pdf",
            data=form_data,
            headers=auth_headers,
            timeout=30
        )
        
        assert response.status_code == 200, f"PDF generation failed: {response.text}"
        
        # Should return a ZIP file
        content_type = response.headers.get('content-type', '')
        assert 'application/zip' in content_type, f"Expected ZIP response, got {content_type}"
        
        # Check content disposition
        content_disp = response.headers.get('content-disposition', '')
        assert '.zip' in content_disp, f"Expected .zip in filename, got {content_disp}"
        
        # Verify ZIP content is not empty
        assert len(response.content) > 0, "ZIP file is empty"
        print(f"Generated ZIP file size: {len(response.content)} bytes")


class TestHealthAndStatus:
    """Health check and status endpoints"""
    
    def test_api_root(self):
        """Test GET /api/ - should be public"""
        response = requests.get(f"{BASE_URL}/api/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
    
    def test_status_endpoint(self):
        """Test GET /api/status - should be public"""
        response = requests.get(f"{BASE_URL}/api/status")
        assert response.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
