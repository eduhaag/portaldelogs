#!/usr/bin/env python3
"""
Backend Test Suite for Performance Analysis Feature
Tests the new slow programs detection functionality in log analysis.
"""

import requests
import json
import os
import sys
from pathlib import Path

# Configuration
BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:8001/api")
TEST_LOG_FILE = "/app/backend/test_slow_programs.log"

class PerformanceAnalysisTest:
    def __init__(self):
        self.backend_url = BACKEND_URL
        self.test_results = []
        self.errors = []
        
    def log_result(self, test_name, success, message, details=None):
        """Log test result"""
        result = {
            "test": test_name,
            "success": success,
            "message": message,
            "details": details or {}
        }
        self.test_results.append(result)
        
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}: {message}")
        
        if not success:
            self.errors.append(f"{test_name}: {message}")
            if details:
                print(f"   Details: {details}")
    
    def test_log_file_exists(self):
        """Test 1: Verify test log file exists"""
        try:
            if os.path.exists(TEST_LOG_FILE):
                with open(TEST_LOG_FILE, 'r') as f:
                    content = f.read()
                    line_count = len(content.splitlines())
                    
                self.log_result(
                    "Log File Exists", 
                    True, 
                    f"Test log file found with {line_count} lines",
                    {"file_path": TEST_LOG_FILE, "line_count": line_count}
                )
                return True
            else:
                self.log_result(
                    "Log File Exists", 
                    False, 
                    f"Test log file not found at {TEST_LOG_FILE}"
                )
                return False
        except Exception as e:
            self.log_result(
                "Log File Exists", 
                False, 
                f"Error reading test log file: {str(e)}"
            )
            return False
    
    def test_backend_connectivity(self):
        """Test 2: Verify backend is accessible"""
        try:
            response = requests.get(f"{self.backend_url}/", timeout=10)
            if response.status_code == 200:
                self.log_result(
                    "Backend Connectivity", 
                    True, 
                    "Backend is accessible",
                    {"status_code": response.status_code, "response": response.json()}
                )
                return True
            else:
                self.log_result(
                    "Backend Connectivity", 
                    False, 
                    f"Backend returned status {response.status_code}"
                )
                return False
        except Exception as e:
            self.log_result(
                "Backend Connectivity", 
                False, 
                f"Cannot connect to backend: {str(e)}"
            )
            return False
    
    def test_analyze_log_endpoint(self):
        """Test 3: Test log analysis endpoint with performance analysis"""
        try:
            # Read test log file
            with open(TEST_LOG_FILE, 'rb') as f:
                files = {'log_file': ('test_slow_programs.log', f, 'text/plain')}
                
                response = requests.post(
                    f"{self.backend_url}/analyze-log",
                    files=files,
                    timeout=30
                )
            
            if response.status_code == 200:
                data = response.json()
                
                # Check if response has required structure
                required_fields = ['success', 'statistics', 'results', 'performance_analysis']
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    self.log_result(
                        "Analyze Log Endpoint", 
                        False, 
                        f"Missing required fields: {missing_fields}",
                        {"response_keys": list(data.keys())}
                    )
                    return False, None
                
                self.log_result(
                    "Analyze Log Endpoint", 
                    True, 
                    "Log analysis endpoint working correctly",
                    {
                        "status_code": response.status_code,
                        "has_performance_analysis": "performance_analysis" in data,
                        "response_size": len(str(data))
                    }
                )
                return True, data
            else:
                self.log_result(
                    "Analyze Log Endpoint", 
                    False, 
                    f"API returned status {response.status_code}: {response.text}"
                )
                return False, None
                
        except Exception as e:
            self.log_result(
                "Analyze Log Endpoint", 
                False, 
                f"Error calling analyze-log endpoint: {str(e)}"
            )
            return False, None
    
    def test_performance_analysis_structure(self, analysis_data):
        """Test 4: Verify performance_analysis structure"""
        try:
            performance_analysis = analysis_data.get('performance_analysis', {})
            
            if not performance_analysis:
                self.log_result(
                    "Performance Analysis Structure", 
                    False, 
                    "performance_analysis field is empty or missing"
                )
                return False
            
            # Check for slow_programs field
            if 'slow_programs' not in performance_analysis:
                self.log_result(
                    "Performance Analysis Structure", 
                    False, 
                    "slow_programs field missing from performance_analysis"
                )
                return False
            
            slow_programs = performance_analysis['slow_programs']
            
            if not isinstance(slow_programs, list):
                self.log_result(
                    "Performance Analysis Structure", 
                    False, 
                    f"slow_programs should be a list, got {type(slow_programs)}"
                )
                return False
            
            self.log_result(
                "Performance Analysis Structure", 
                True, 
                f"Performance analysis structure is correct with {len(slow_programs)} slow programs",
                {
                    "slow_programs_count": len(slow_programs),
                    "performance_analysis_keys": list(performance_analysis.keys())
                }
            )
            return True
            
        except Exception as e:
            self.log_result(
                "Performance Analysis Structure", 
                False, 
                f"Error validating performance analysis structure: {str(e)}"
            )
            return False
    
    def test_slow_programs_data(self, analysis_data):
        """Test 5: Verify slow_programs data format and content"""
        try:
            slow_programs = analysis_data.get('performance_analysis', {}).get('slow_programs', [])
            
            if not slow_programs:
                self.log_result(
                    "Slow Programs Data", 
                    False, 
                    "No slow programs detected in test log"
                )
                return False
            
            # Required fields for each slow program
            required_fields = ['program', 'duration_ms', 'duration_seconds', 'line', 'timestamp', 'severity', 'context']
            
            valid_programs = 0
            invalid_programs = []
            
            for i, program in enumerate(slow_programs):
                missing_fields = [field for field in required_fields if field not in program]
                
                if missing_fields:
                    invalid_programs.append(f"Program {i}: missing {missing_fields}")
                    continue
                
                # Validate data types and values
                try:
                    duration_ms = program['duration_ms']
                    duration_seconds = program['duration_seconds']
                    severity = program['severity']
                    
                    # Check if duration is >= 2000ms (2 seconds)
                    if duration_ms < 2000:
                        invalid_programs.append(f"Program {i}: duration {duration_ms}ms < 2000ms threshold")
                        continue
                    
                    # Check severity mapping
                    expected_severity = "critical" if duration_ms >= 5000 else ("high" if duration_ms >= 3000 else "medium")
                    if severity != expected_severity:
                        invalid_programs.append(f"Program {i}: incorrect severity '{severity}', expected '{expected_severity}' for {duration_ms}ms")
                        continue
                    
                    # Check duration consistency
                    expected_seconds = round(duration_ms / 1000, 2)
                    if abs(duration_seconds - expected_seconds) > 0.01:
                        invalid_programs.append(f"Program {i}: duration_seconds {duration_seconds} doesn't match duration_ms {duration_ms}")
                        continue
                    
                    valid_programs += 1
                    
                except (ValueError, TypeError) as e:
                    invalid_programs.append(f"Program {i}: data type error - {str(e)}")
            
            if invalid_programs:
                self.log_result(
                    "Slow Programs Data", 
                    False, 
                    f"Found {len(invalid_programs)} invalid programs out of {len(slow_programs)}",
                    {"invalid_programs": invalid_programs[:5]}  # Show first 5 errors
                )
                return False
            
            self.log_result(
                "Slow Programs Data", 
                True, 
                f"All {valid_programs} slow programs have valid data format",
                {
                    "total_programs": len(slow_programs),
                    "valid_programs": valid_programs,
                    "sample_program": slow_programs[0] if slow_programs else None
                }
            )
            return True
            
        except Exception as e:
            self.log_result(
                "Slow Programs Data", 
                False, 
                f"Error validating slow programs data: {str(e)}"
            )
            return False
    
    def test_slow_programs_statistics(self, analysis_data):
        """Test 6: Verify slow_programs_stats if present"""
        try:
            performance_analysis = analysis_data.get('performance_analysis', {})
            slow_programs = performance_analysis.get('slow_programs', [])
            
            if not slow_programs:
                self.log_result(
                    "Slow Programs Statistics", 
                    True, 
                    "No slow programs found, statistics not expected"
                )
                return True
            
            # Check if slow_programs_stats exists
            if 'slow_programs_stats' not in performance_analysis:
                self.log_result(
                    "Slow Programs Statistics", 
                    False, 
                    "slow_programs_stats missing when slow programs exist"
                )
                return False
            
            stats = performance_analysis['slow_programs_stats']
            required_stats = ['total_slow_programs', 'slowest_duration_ms', 'average_duration_ms', 
                            'critical_count', 'high_count', 'medium_count']
            
            missing_stats = [stat for stat in required_stats if stat not in stats]
            if missing_stats:
                self.log_result(
                    "Slow Programs Statistics", 
                    False, 
                    f"Missing statistics fields: {missing_stats}"
                )
                return False
            
            # Validate statistics values
            total_programs = len(slow_programs)
            if stats['total_slow_programs'] != total_programs:
                self.log_result(
                    "Slow Programs Statistics", 
                    False, 
                    f"total_slow_programs {stats['total_slow_programs']} != actual count {total_programs}"
                )
                return False
            
            # Count severity levels
            actual_critical = len([p for p in slow_programs if p['severity'] == 'critical'])
            actual_high = len([p for p in slow_programs if p['severity'] == 'high'])
            actual_medium = len([p for p in slow_programs if p['severity'] == 'medium'])
            
            if (stats['critical_count'] != actual_critical or 
                stats['high_count'] != actual_high or 
                stats['medium_count'] != actual_medium):
                self.log_result(
                    "Slow Programs Statistics", 
                    False, 
                    f"Severity counts mismatch: stats({stats['critical_count']},{stats['high_count']},{stats['medium_count']}) vs actual({actual_critical},{actual_high},{actual_medium})"
                )
                return False
            
            self.log_result(
                "Slow Programs Statistics", 
                True, 
                "Slow programs statistics are accurate",
                {
                    "total_programs": stats['total_slow_programs'],
                    "slowest_ms": stats['slowest_duration_ms'],
                    "average_ms": stats['average_duration_ms'],
                    "severity_counts": {
                        "critical": stats['critical_count'],
                        "high": stats['high_count'],
                        "medium": stats['medium_count']
                    }
                }
            )
            return True
            
        except Exception as e:
            self.log_result(
                "Slow Programs Statistics", 
                False, 
                f"Error validating statistics: {str(e)}"
            )
            return False
    
    def test_expected_programs_detection(self, analysis_data):
        """Test 7: Verify detection of expected slow programs from test log"""
        try:
            slow_programs = analysis_data.get('performance_analysis', {}).get('slow_programs', [])
            
            # Expected programs from test log (programs >= 2 seconds)
            expected_programs = [
                {"name": "financeiro.p", "duration_ms": 2500, "severity": "medium"},
                {"name": "estoque_consulta.p", "duration_ms": 4500, "severity": "high"},
                {"name": "nfe_transmissao.p", "duration_ms": 8200, "severity": "critical"},
                {"name": "report_vendas.p", "duration_ms": 3200, "severity": "high"},
                {"name": "calculo_impostos.p", "duration_ms": 5900, "severity": "critical"},
                {"name": "backup_dados.p", "duration_ms": 2100, "severity": "medium"},
                {"name": "importacao_xml.p", "duration_ms": 6500, "severity": "critical"},
                {"name": "validacao_nfe.p", "duration_ms": 3800, "severity": "high"},
                {"name": "controle_estoque.p", "duration_ms": 7200, "severity": "critical"},
                {"name": "relatorio_fiscal.p", "duration_ms": 4100, "severity": "high"},
                {"name": "sincronizacao_datasul.p", "duration_ms": 9500, "severity": "critical"}
            ]
            
            detected_programs = [p['program'] for p in slow_programs]
            detected_count = len(detected_programs)
            expected_count = len(expected_programs)
            
            # Check if we detected approximately the right number
            if detected_count < expected_count * 0.8:  # Allow 20% tolerance
                self.log_result(
                    "Expected Programs Detection", 
                    False, 
                    f"Detected only {detected_count} programs, expected around {expected_count}",
                    {
                        "detected_programs": detected_programs,
                        "expected_count": expected_count
                    }
                )
                return False
            
            # Check for some specific programs
            key_programs = ["financeiro.p", "nfe_transmissao.p", "calculo_impostos.p"]
            found_key_programs = []
            
            for program in slow_programs:
                program_name = program['program']
                for key_prog in key_programs:
                    if key_prog in program_name:
                        found_key_programs.append(key_prog)
            
            if len(found_key_programs) < 2:  # At least 2 key programs should be found
                self.log_result(
                    "Expected Programs Detection", 
                    False, 
                    f"Found only {len(found_key_programs)} key programs: {found_key_programs}",
                    {"detected_programs": detected_programs}
                )
                return False
            
            self.log_result(
                "Expected Programs Detection", 
                True, 
                f"Successfully detected {detected_count} slow programs including key programs",
                {
                    "detected_count": detected_count,
                    "expected_count": expected_count,
                    "key_programs_found": found_key_programs,
                    "sample_detected": detected_programs[:5]
                }
            )
            return True
            
        except Exception as e:
            self.log_result(
                "Expected Programs Detection", 
                False, 
                f"Error checking expected programs: {str(e)}"
            )
            return False
    
    def run_all_tests(self):
        """Run all performance analysis tests"""
        print("🚀 Starting Performance Analysis Tests")
        print("=" * 60)
        
        # Test 1: Log file exists
        if not self.test_log_file_exists():
            print("\n❌ Cannot proceed without test log file")
            return False
        
        # Test 2: Backend connectivity
        if not self.test_backend_connectivity():
            print("\n❌ Cannot proceed without backend connectivity")
            return False
        
        # Test 3: Analyze log endpoint
        success, analysis_data = self.test_analyze_log_endpoint()
        if not success:
            print("\n❌ Cannot proceed without working analyze-log endpoint")
            return False
        
        # Test 4: Performance analysis structure
        if not self.test_performance_analysis_structure(analysis_data):
            return False
        
        # Test 5: Slow programs data validation
        if not self.test_slow_programs_data(analysis_data):
            return False
        
        # Test 6: Statistics validation
        if not self.test_slow_programs_statistics(analysis_data):
            return False
        
        # Test 7: Expected programs detection
        if not self.test_expected_programs_detection(analysis_data):
            return False
        
        return True
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r['success']])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        
        if failed_tests > 0:
            print(f"\n🔥 FAILED TESTS:")
            for error in self.errors:
                print(f"   • {error}")
        
        success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
        print(f"\n📈 Success Rate: {success_rate:.1f}%")
        
        if success_rate == 100:
            print("🎉 ALL TESTS PASSED! Performance analysis feature is working correctly.")
        elif success_rate >= 80:
            print("⚠️  Most tests passed, but some issues need attention.")
        else:
            print("🚨 CRITICAL ISSUES DETECTED! Performance analysis feature needs fixes.")
        
        return success_rate == 100

def main():
    """Main test execution"""
    tester = PerformanceAnalysisTest()
    
    try:
        success = tester.run_all_tests()
        overall_success = tester.print_summary()
        
        # Exit with appropriate code
        sys.exit(0 if overall_success else 1)
        
    except KeyboardInterrupt:
        print("\n\n⏹️  Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n💥 Unexpected error during testing: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()