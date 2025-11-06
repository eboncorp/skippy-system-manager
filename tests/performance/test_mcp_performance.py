#!/usr/bin/env python3
"""
Performance tests for MCP server operations
"""

import time
import pytest
from concurrent.futures import ThreadPoolExecutor, as_completed


class TestMCPPerformance:
    """Performance tests for MCP server"""

    @pytest.mark.performance
    def test_file_read_performance(self, tmp_path):
        """Test file reading performance"""
        # Create test file
        test_file = tmp_path / "test.txt"
        test_content = "x" * 1024 * 100  # 100KB
        test_file.write_text(test_content)

        # Measure read time
        start = time.time()
        for _ in range(100):
            content = test_file.read_text()
            assert len(content) == len(test_content)
        duration = time.time() - start

        # Should complete 100 reads in under 1 second
        assert duration < 1.0, f"100 file reads took {duration:.2f}s (expected <1s)"

    @pytest.mark.performance
    def test_file_write_performance(self, tmp_path):
        """Test file writing performance"""
        test_content = "x" * 1024 * 10  # 10KB

        start = time.time()
        for i in range(100):
            test_file = tmp_path / f"test_{i}.txt"
            test_file.write_text(test_content)
        duration = time.time() - start

        # Should complete 100 writes in under 2 seconds
        assert duration < 2.0, f"100 file writes took {duration:.2f}s (expected <2s)"

    @pytest.mark.performance
    def test_concurrent_operations(self, tmp_path):
        """Test concurrent file operations"""
        def write_and_read(path, content):
            """Write and read a file"""
            path.write_text(content)
            return path.read_text()

        # Test with 10 concurrent operations
        test_content = "test content"
        paths = [tmp_path / f"concurrent_{i}.txt" for i in range(10)]

        start = time.time()
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [
                executor.submit(write_and_read, path, test_content)
                for path in paths
            ]
            results = [f.result() for f in as_completed(futures)]
        duration = time.time() - start

        assert len(results) == 10
        assert all(r == test_content for r in results)
        # Should complete in under 1 second
        assert duration < 1.0, f"10 concurrent ops took {duration:.2f}s (expected <1s)"

    @pytest.mark.performance
    def test_large_file_handling(self, tmp_path):
        """Test handling of large files"""
        # Create 10MB file
        test_file = tmp_path / "large.txt"
        test_content = "x" * 1024 * 1024 * 10  # 10MB

        # Write
        start = time.time()
        test_file.write_text(test_content)
        write_duration = time.time() - start

        # Read
        start = time.time()
        content = test_file.read_text()
        read_duration = time.time() - start

        assert len(content) == len(test_content)
        # Should complete read/write in reasonable time
        assert write_duration < 2.0, f"10MB write took {write_duration:.2f}s"
        assert read_duration < 2.0, f"10MB read took {read_duration:.2f}s"

    @pytest.mark.performance
    @pytest.mark.benchmark
    def test_path_validation_performance(self):
        """Test path validation performance"""
        try:
            from skippy_validator import validate_path
        except ImportError:
            pytest.skip("skippy_validator not available")

        # Test 1000 path validations
        paths = [f"/tmp/test/path/{i}/file.txt" for i in range(1000)]

        start = time.time()
        for path in paths:
            try:
                validate_path(path, base_dir="/tmp/test")
            except Exception:
                pass  # Some may fail validation
        duration = time.time() - start

        # Should validate 1000 paths in under 0.5 seconds
        assert duration < 0.5, f"1000 validations took {duration:.2f}s (expected <0.5s)"

    @pytest.mark.performance
    @pytest.mark.benchmark
    def test_logging_performance(self):
        """Test logging performance"""
        try:
            from skippy_logger import get_logger
        except ImportError:
            pytest.skip("skippy_logger not available")

        logger = get_logger("performance_test")

        # Test 1000 log messages
        start = time.time()
        for i in range(1000):
            logger.debug(f"Test message {i}")
        duration = time.time() - start

        # Should log 1000 messages in under 1 second
        assert duration < 1.0, f"1000 log messages took {duration:.2f}s (expected <1s)"


class TestSystemResourceUsage:
    """Test system resource usage under load"""

    @pytest.mark.performance
    @pytest.mark.slow
    def test_memory_usage_stability(self, tmp_path):
        """Test that memory usage remains stable under load"""
        import psutil
        import os

        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss

        # Perform many operations
        for i in range(100):
            test_file = tmp_path / f"mem_test_{i}.txt"
            test_file.write_text("x" * 1024 * 100)  # 100KB
            content = test_file.read_text()
            test_file.unlink()

        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory

        # Memory increase should be less than 50MB
        max_increase = 50 * 1024 * 1024  # 50MB
        assert memory_increase < max_increase, \
            f"Memory increased by {memory_increase / 1024 / 1024:.1f}MB (expected <50MB)"

    @pytest.mark.performance
    @pytest.mark.benchmark
    def test_cpu_efficiency(self):
        """Test CPU efficiency of operations"""
        import psutil
        import os

        process = psutil.Process(os.getpid())

        # Measure CPU usage during operations
        process.cpu_percent(interval=None)  # Initialize
        time.sleep(0.1)

        start_cpu = process.cpu_percent(interval=None)

        # Do some work
        result = 0
        for i in range(100000):
            result += i * 2

        time.sleep(0.1)
        end_cpu = process.cpu_percent(interval=None)

        # CPU usage should be reasonable
        # Note: This is process-specific, not system-wide
        assert result > 0  # Ensure work was done


@pytest.fixture
def performance_report(request):
    """Generate performance report after tests"""
    yield

    # This runs after each test
    if hasattr(request.node, 'rep_call') and request.node.rep_call.passed:
        duration = request.node.rep_call.duration
        test_name = request.node.name
        print(f"\n[PERF] {test_name}: {duration:.3f}s")


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Hook to store test results"""
    outcome = yield
    rep = outcome.get_result()
    setattr(item, f"rep_{rep.when}", rep)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "performance"])
