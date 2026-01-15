"""
Smart Sync Performance Testing and Benchmarking Suite

This module provides comprehensive performance testing for Smart Sync functionality,
including benchmarking, stress testing, and performance regression detection.

Key Performance Areas:
1. Initial sync performance with various project sizes
2. Incremental sync efficiency and speed
3. Memory usage and resource consumption
4. Network simulation and latency handling
5. Concurrent operation performance
6. Large file handling and optimization
"""

import pytest
import tempfile
import shutil
import time
import os
import threading
import psutil
from pathlib import Path
from unittest.mock import patch, MagicMock
import statistics
from typing import List, Dict, Tuple

from src.smart_sync import SmartSyncManager, detect_smart_sync_scenario


class PerformanceTimer:
    """Context manager for measuring execution time."""
    
    def __init__(self, description: str = "Operation"):
        self.description = description
        self.start_time = None
        self.end_time = None
        self.duration = None
    
    def __enter__(self):
        self.start_time = time.perf_counter()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = time.perf_counter()
        self.duration = self.end_time - self.start_time
        print(f"{self.description}: {self.duration:.3f}s")


class MemoryProfiler:
    """Memory usage profiler for sync operations."""
    
    def __init__(self):
        self.process = psutil.Process()
        self.initial_memory = None
        self.peak_memory = None
        self.final_memory = None
    
    def start(self):
        """Start memory profiling."""
        self.initial_memory = self.process.memory_info().rss / 1024 / 1024  # MB
        self.peak_memory = self.initial_memory
    
    def update_peak(self):
        """Update peak memory usage."""
        current_memory = self.process.memory_info().rss / 1024 / 1024  # MB
        if current_memory > self.peak_memory:
            self.peak_memory = current_memory
    
    def finish(self):
        """Finish memory profiling."""
        self.final_memory = self.process.memory_info().rss / 1024 / 1024  # MB
    
    def get_stats(self) -> Dict[str, float]:
        """Get memory usage statistics."""
        return {
            "initial_mb": self.initial_memory,
            "peak_mb": self.peak_memory,
            "final_mb": self.final_memory,
            "increase_mb": self.final_memory - self.initial_memory,
            "peak_increase_mb": self.peak_memory - self.initial_memory
        }


class TestSmartSyncPerformanceBenchmarks:
    """Comprehensive performance benchmarks for Smart Sync operations."""
    
    def setup_method(self):
        """Set up performance test environment."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.network_dir = self.temp_dir / "network"
        self.local_dir = self.temp_dir / "local"
        self.network_dir.mkdir()
        self.local_dir.mkdir()
        
        # Performance thresholds (in seconds)
        self.thresholds = {
            "small_project_initial": 5.0,      # <100 files
            "medium_project_initial": 15.0,    # 100-1000 files
            "large_project_initial": 60.0,     # >1000 files
            "incremental_sync": 10.0,          # Any incremental sync
            "single_file_sync": 1.0,           # Single file operations
        }
    
    def teardown_method(self):
        """Clean up test environment."""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    def _create_test_files(self, count: int, size_kb: int = 1) -> List[Path]:
        """Create test files of specified count and size."""
        files = []
        content = "x" * (size_kb * 1024)
        
        for i in range(count):
            file_path = self.network_dir / f"test_file_{i:04d}.txt"
            file_path.write_text(content)
            files.append(file_path)
        
        return files
    
    def _create_nested_structure(self, dirs: int, files_per_dir: int) -> int:
        """Create nested directory structure with files."""
        total_files = 0
        
        for i in range(dirs):
            dir_path = self.network_dir / f"dir_{i:03d}"
            dir_path.mkdir()
            
            for j in range(files_per_dir):
                file_path = dir_path / f"file_{j:03d}.txt"
                file_path.write_text(f"Content for dir {i}, file {j}")
                total_files += 1
        
        return total_files
    
    def test_small_project_performance(self):
        """Benchmark performance with small projects (<100 files)."""
        # Create small project (50 files)
        files = self._create_test_files(50, size_kb=2)
        
        sync_manager = SmartSyncManager(self.network_dir, self.local_dir)
        memory_profiler = MemoryProfiler()
        
        # Benchmark initial sync
        memory_profiler.start()
        with PerformanceTimer("Small project initial sync") as timer:
            result = sync_manager.initial_sync()
        memory_profiler.finish()
        
        # Assertions
        assert result is True
        assert timer.duration < self.thresholds["small_project_initial"], \
            f"Small project sync too slow: {timer.duration:.3f}s > {self.thresholds['small_project_initial']}s"
        
        # Memory usage should be reasonable
        memory_stats = memory_profiler.get_stats()
        assert memory_stats["increase_mb"] < 50, f"Memory usage too high: {memory_stats['increase_mb']:.1f}MB"
        
        # Verify all files synced
        assert len(list(self.local_dir.rglob("*.txt"))) == 50
        
        print(f"Memory usage: {memory_stats}")
    
    def test_medium_project_performance(self):
        """Benchmark performance with medium projects (100-1000 files)."""
        # Create medium project (500 files in nested structure)
        total_files = self._create_nested_structure(dirs=20, files_per_dir=25)
        assert total_files == 500
        
        sync_manager = SmartSyncManager(self.network_dir, self.local_dir)
        memory_profiler = MemoryProfiler()
        
        # Benchmark initial sync
        memory_profiler.start()
        with PerformanceTimer("Medium project initial sync") as timer:
            result = sync_manager.initial_sync()
        memory_profiler.finish()
        
        # Assertions
        assert result is True
        assert timer.duration < self.thresholds["medium_project_initial"], \
            f"Medium project sync too slow: {timer.duration:.3f}s > {self.thresholds['medium_project_initial']}s"
        
        # Memory usage should scale reasonably
        memory_stats = memory_profiler.get_stats()
        assert memory_stats["increase_mb"] < 100, f"Memory usage too high: {memory_stats['increase_mb']:.1f}MB"
        
        # Verify all files synced
        assert len(list(self.local_dir.rglob("*.txt"))) == 500
        
        print(f"Memory usage: {memory_stats}")
    
    def test_large_project_performance(self):
        """Benchmark performance with large projects (>1000 files)."""
        # Create large project (1500 files)
        total_files = self._create_nested_structure(dirs=50, files_per_dir=30)
        assert total_files == 1500
        
        sync_manager = SmartSyncManager(self.network_dir, self.local_dir)
        memory_profiler = MemoryProfiler()
        
        # Benchmark initial sync
        memory_profiler.start()
        with PerformanceTimer("Large project initial sync") as timer:
            result = sync_manager.initial_sync()
        memory_profiler.finish()
        
        # Assertions
        assert result is True
        assert timer.duration < self.thresholds["large_project_initial"], \
            f"Large project sync too slow: {timer.duration:.3f}s > {self.thresholds['large_project_initial']}s"
        
        # Memory usage should not be excessive
        memory_stats = memory_profiler.get_stats()
        assert memory_stats["increase_mb"] < 200, f"Memory usage too high: {memory_stats['increase_mb']:.1f}MB"
        
        # Verify all files synced
        assert len(list(self.local_dir.rglob("*.txt"))) == 1500
        
        print(f"Memory usage: {memory_stats}")
    
    def test_incremental_sync_performance(self):
        """Benchmark incremental sync performance."""
        # Set up initial project
        self._create_test_files(100, size_kb=1)
        
        sync_manager = SmartSyncManager(self.network_dir, self.local_dir)
        sync_manager.initial_sync()
        
        # Modify a few files
        modified_files = []
        for i in [5, 25, 50, 75, 95]:
            file_path = self.network_dir / f"test_file_{i:04d}.txt"
            file_path.write_text(f"Modified content {i}")
            modified_files.append(file_path)
        
        # Add a few new files
        new_files = self._create_test_files(5, size_kb=1)
        
        # Benchmark incremental sync
        with PerformanceTimer("Incremental sync down") as timer:
            result = sync_manager.incremental_sync_down()
        
        # Assertions
        assert result is True
        assert timer.duration < self.thresholds["incremental_sync"], \
            f"Incremental sync too slow: {timer.duration:.3f}s > {self.thresholds['incremental_sync']}s"
        
        # Verify changes were synced
        for i in [5, 25, 50, 75, 95]:
            local_file = self.local_dir / f"test_file_{i:04d}.txt"
            assert f"Modified content {i}" in local_file.read_text()
    
    def test_large_file_performance(self):
        """Benchmark performance with large files."""
        # Create files of various sizes
        file_sizes = [
            (1, 1024),      # 1MB
            (1, 5120),      # 5MB
            (1, 10240),     # 10MB
        ]
        
        sync_manager = SmartSyncManager(self.network_dir, self.local_dir)
        
        for count, size_kb in file_sizes:
            # Clean up previous files
            for file in self.network_dir.glob("*.txt"):
                file.unlink()
            for file in self.local_dir.glob("*.txt"):
                file.unlink()
            
            # Create large file
            self._create_test_files(count, size_kb)
            
            # Benchmark sync
            with PerformanceTimer(f"Large file sync ({size_kb}KB)") as timer:
                result = sync_manager.initial_sync()
            
            assert result is True
            
            # Performance should scale reasonably with file size
            # Allow more time for larger files, but not linearly
            max_time = min(30.0, 5.0 + (size_kb / 1024) * 2)  # Base 5s + 2s per MB
            assert timer.duration < max_time, \
                f"Large file sync too slow: {timer.duration:.3f}s > {max_time:.3f}s for {size_kb}KB"
    
    def test_sync_efficiency_ratio(self):
        """Test that incremental sync is significantly faster than full sync."""
        # Create initial project
        self._create_test_files(200, size_kb=1)
        
        sync_manager = SmartSyncManager(self.network_dir, self.local_dir)
        
        # Measure initial sync time
        with PerformanceTimer("Full initial sync") as initial_timer:
            sync_manager.initial_sync()
        
        # Modify only 5% of files
        for i in range(0, 200, 20):  # Every 20th file
            file_path = self.network_dir / f"test_file_{i:04d}.txt"
            file_path.write_text(f"Modified {i}")
        
        # Measure incremental sync time
        with PerformanceTimer("Incremental sync") as incremental_timer:
            sync_manager.incremental_sync_down()
        
        # Incremental sync should be at least 5x faster than full sync
        efficiency_ratio = initial_timer.duration / incremental_timer.duration
        assert efficiency_ratio >= 5.0, \
            f"Incremental sync not efficient enough: {efficiency_ratio:.1f}x speedup (expected ≥5x)"
        
        print(f"Sync efficiency: {efficiency_ratio:.1f}x faster")


class TestSmartSyncStressTesting:
    """Stress testing for Smart Sync under extreme conditions."""
    
    def setup_method(self):
        """Set up stress test environment."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.network_dir = self.temp_dir / "network"
        self.local_dir = self.temp_dir / "local"
        self.network_dir.mkdir()
        self.local_dir.mkdir()
    
    def teardown_method(self):
        """Clean up test environment."""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    def test_concurrent_sync_operations(self):
        """Test concurrent sync operations for thread safety."""
        # Create test files
        for i in range(50):
            (self.network_dir / f"file_{i}.txt").write_text(f"Content {i}")
        
        sync_manager = SmartSyncManager(self.network_dir, self.local_dir)
        sync_manager.initial_sync()
        
        # Prepare concurrent operations
        results = []
        errors = []
        
        def sync_operation(operation_id: int):
            """Perform sync operation in thread."""
            try:
                # Modify a file
                file_path = self.network_dir / f"file_{operation_id % 50}.txt"
                file_path.write_text(f"Modified by thread {operation_id}")
                
                # Perform sync
                result = sync_manager.incremental_sync_down()
                results.append((operation_id, result))
            except Exception as e:
                errors.append((operation_id, str(e)))
        
        # Run concurrent operations
        threads = []
        for i in range(10):
            thread = threading.Thread(target=sync_operation, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Verify results
        assert len(errors) == 0, f"Concurrent operations failed: {errors}"
        assert len(results) == 10, f"Not all operations completed: {len(results)}/10"
        
        # All operations should succeed
        for operation_id, result in results:
            assert result is True, f"Operation {operation_id} failed"
    
    def test_rapid_file_changes(self):
        """Test handling of rapid file changes."""
        # Create initial files
        for i in range(20):
            (self.network_dir / f"rapid_{i}.txt").write_text(f"Initial {i}")
        
        sync_manager = SmartSyncManager(self.network_dir, self.local_dir)
        sync_manager.initial_sync()
        
        # Rapidly modify files and sync
        sync_times = []
        
        for iteration in range(10):
            # Modify multiple files
            for i in range(0, 20, 2):  # Every other file
                file_path = self.network_dir / f"rapid_{i}.txt"
                file_path.write_text(f"Rapid change {iteration}-{i}")
            
            # Measure sync time
            start_time = time.perf_counter()
            result = sync_manager.incremental_sync_down()
            sync_time = time.perf_counter() - start_time
            
            assert result is True
            sync_times.append(sync_time)
            
            # Brief pause to avoid overwhelming the system
            time.sleep(0.1)
        
        # Verify sync times remain reasonable
        avg_sync_time = statistics.mean(sync_times)
        max_sync_time = max(sync_times)
        
        assert avg_sync_time < 2.0, f"Average sync time too high: {avg_sync_time:.3f}s"
        assert max_sync_time < 5.0, f"Max sync time too high: {max_sync_time:.3f}s"
        
        print(f"Rapid sync stats - Avg: {avg_sync_time:.3f}s, Max: {max_sync_time:.3f}s")
    
    def test_memory_leak_detection(self):
        """Test for memory leaks during repeated sync operations."""
        # Create test files
        for i in range(100):
            (self.network_dir / f"leak_test_{i}.txt").write_text(f"Content {i}")
        
        sync_manager = SmartSyncManager(self.network_dir, self.local_dir)
        
        # Measure initial memory
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Perform many sync operations
        for iteration in range(20):
            # Modify some files
            for i in range(0, 100, 10):
                file_path = self.network_dir / f"leak_test_{i}.txt"
                file_path.write_text(f"Modified {iteration}-{i}")
            
            # Sync
            if iteration == 0:
                sync_manager.initial_sync()
            else:
                sync_manager.incremental_sync_down()
            
            # Check memory every 5 iterations
            if iteration % 5 == 0:
                current_memory = process.memory_info().rss / 1024 / 1024  # MB
                memory_increase = current_memory - initial_memory
                
                # Memory increase should be reasonable (allow some growth but not excessive)
                assert memory_increase < 100, \
                    f"Potential memory leak detected: {memory_increase:.1f}MB increase after {iteration} iterations"
        
        # Final memory check
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        total_increase = final_memory - initial_memory
        
        print(f"Memory usage: Initial {initial_memory:.1f}MB, Final {final_memory:.1f}MB, Increase {total_increase:.1f}MB")
        
        # Total memory increase should be reasonable
        assert total_increase < 150, f"Excessive memory usage: {total_increase:.1f}MB increase"


class TestSmartSyncPerformanceRegression:
    """Performance regression testing to detect performance degradation."""
    
    def setup_method(self):
        """Set up regression test environment."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.network_dir = self.temp_dir / "network"
        self.local_dir = self.temp_dir / "local"
        self.network_dir.mkdir()
        self.local_dir.mkdir()
        
        # Baseline performance expectations (in seconds)
        self.baselines = {
            "detection_100_paths": 0.1,        # Detect 100 paths
            "sync_100_small_files": 3.0,       # Sync 100 small files
            "sync_10_large_files": 10.0,       # Sync 10 large files (1MB each)
            "incremental_10_changes": 1.0,     # Incremental sync of 10 changes
        }
    
    def teardown_method(self):
        """Clean up test environment."""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    @patch('platform.system', return_value='Windows')
    def test_detection_performance_regression(self, mock_platform):
        """Test that path detection performance hasn't regressed."""
        # Create many paths to test
        test_paths = []
        for drive in "DEFGHIJKLMNOPQRSTUVWXYZ":
            for i in range(5):
                test_paths.append(Path(f"{drive}:\\project_{i}"))
        
        # Benchmark detection
        with PerformanceTimer("Detection of 100 paths") as timer:
            for path in test_paths:
                detect_smart_sync_scenario(path)
        
        # Check against baseline
        assert timer.duration < self.baselines["detection_100_paths"], \
            f"Detection performance regression: {timer.duration:.3f}s > {self.baselines['detection_100_paths']}s"
    
    def test_small_files_sync_regression(self):
        """Test that small files sync performance hasn't regressed."""
        # Create 100 small files
        for i in range(100):
            (self.network_dir / f"small_{i}.txt").write_text(f"Small content {i}")
        
        sync_manager = SmartSyncManager(self.network_dir, self.local_dir)
        
        # Benchmark sync
        with PerformanceTimer("Sync 100 small files") as timer:
            result = sync_manager.initial_sync()
        
        assert result is True
        assert timer.duration < self.baselines["sync_100_small_files"], \
            f"Small files sync regression: {timer.duration:.3f}s > {self.baselines['sync_100_small_files']}s"
    
    def test_large_files_sync_regression(self):
        """Test that large files sync performance hasn't regressed."""
        # Create 10 large files (1MB each)
        large_content = "x" * (1024 * 1024)  # 1MB
        for i in range(10):
            (self.network_dir / f"large_{i}.dat").write_text(large_content)
        
        sync_manager = SmartSyncManager(self.network_dir, self.local_dir)
        
        # Benchmark sync
        with PerformanceTimer("Sync 10 large files") as timer:
            result = sync_manager.initial_sync()
        
        assert result is True
        assert timer.duration < self.baselines["sync_10_large_files"], \
            f"Large files sync regression: {timer.duration:.3f}s > {self.baselines['sync_10_large_files']}s"
    
    def test_incremental_sync_regression(self):
        """Test that incremental sync performance hasn't regressed."""
        # Set up initial files
        for i in range(50):
            (self.network_dir / f"inc_{i}.txt").write_text(f"Initial {i}")
        
        sync_manager = SmartSyncManager(self.network_dir, self.local_dir)
        sync_manager.initial_sync()
        
        # Modify 10 files
        for i in range(0, 50, 5):  # Every 5th file
            (self.network_dir / f"inc_{i}.txt").write_text(f"Modified {i}")
        
        # Benchmark incremental sync
        with PerformanceTimer("Incremental sync 10 changes") as timer:
            result = sync_manager.incremental_sync_down()
        
        assert result is True
        assert timer.duration < self.baselines["incremental_10_changes"], \
            f"Incremental sync regression: {timer.duration:.3f}s > {self.baselines['incremental_10_changes']}s"


class TestSmartSyncResourceUsage:
    """Test resource usage patterns and optimization."""
    
    def setup_method(self):
        """Set up resource usage test environment."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.network_dir = self.temp_dir / "network"
        self.local_dir = self.temp_dir / "local"
        self.network_dir.mkdir()
        self.local_dir.mkdir()
    
    def teardown_method(self):
        """Clean up test environment."""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    def test_cpu_usage_efficiency(self):
        """Test CPU usage during sync operations."""
        # Create test files
        for i in range(200):
            (self.network_dir / f"cpu_test_{i}.txt").write_text(f"Content {i}")
        
        sync_manager = SmartSyncManager(self.network_dir, self.local_dir)
        
        # Monitor CPU usage during sync
        process = psutil.Process()
        cpu_samples = []
        
        def monitor_cpu():
            """Monitor CPU usage in background."""
            for _ in range(20):  # Sample for 2 seconds
                cpu_samples.append(process.cpu_percent())
                time.sleep(0.1)
        
        # Start CPU monitoring
        monitor_thread = threading.Thread(target=monitor_cpu)
        monitor_thread.start()
        
        # Perform sync
        result = sync_manager.initial_sync()
        
        # Wait for monitoring to complete
        monitor_thread.join()
        
        assert result is True
        
        # Analyze CPU usage
        if cpu_samples:
            avg_cpu = statistics.mean(cpu_samples)
            max_cpu = max(cpu_samples)
            
            # CPU usage should be reasonable (not pegging the CPU)
            assert avg_cpu < 80.0, f"Average CPU usage too high: {avg_cpu:.1f}%"
            assert max_cpu < 95.0, f"Peak CPU usage too high: {max_cpu:.1f}%"
            
            print(f"CPU usage - Avg: {avg_cpu:.1f}%, Max: {max_cpu:.1f}%")
    
    def test_disk_io_efficiency(self):
        """Test disk I/O patterns during sync operations."""
        # Create files with known total size
        file_count = 100
        file_size_kb = 10
        total_size_mb = (file_count * file_size_kb) / 1024
        
        content = "x" * (file_size_kb * 1024)
        for i in range(file_count):
            (self.network_dir / f"io_test_{i}.txt").write_text(content)
        
        sync_manager = SmartSyncManager(self.network_dir, self.local_dir)
        
        # Monitor disk I/O (with platform compatibility)
        process = psutil.Process()
        
        # Check if io_counters is available (not available on macOS)
        try:
            io_before = process.io_counters()
            io_available = True
        except (AttributeError, OSError):
            # io_counters not available on this platform (e.g., macOS)
            io_available = False
            io_before = None
        
        # Perform sync
        start_time = time.perf_counter()
        result = sync_manager.initial_sync()
        sync_duration = time.perf_counter() - start_time
        
        assert result is True
        
        if io_available:
            io_after = process.io_counters()
            
            # Calculate I/O statistics
            bytes_read = io_after.read_bytes - io_before.read_bytes
            bytes_written = io_after.write_bytes - io_before.write_bytes
            
            read_mb = bytes_read / 1024 / 1024
            written_mb = bytes_written / 1024 / 1024
            
            # I/O should be efficient (not excessive compared to file sizes)
            # Allow some overhead for metadata and filesystem operations
            max_expected_io = total_size_mb * 3  # 3x overhead allowance
            
            assert read_mb < max_expected_io, f"Excessive read I/O: {read_mb:.1f}MB (expected <{max_expected_io:.1f}MB)"
            assert written_mb < max_expected_io, f"Excessive write I/O: {written_mb:.1f}MB (expected <{max_expected_io:.1f}MB)"
            
            # Calculate throughput
            total_io_mb = read_mb + written_mb
            throughput_mbps = total_io_mb / sync_duration
            
            print(f"I/O efficiency - Read: {read_mb:.1f}MB, Write: {written_mb:.1f}MB, Throughput: {throughput_mbps:.1f}MB/s")
        else:
            # On platforms without io_counters, just verify sync worked and report timing
            throughput_mbps = total_size_mb / sync_duration
            print(f"I/O monitoring not available on this platform - Sync completed in {sync_duration:.2f}s, Estimated throughput: {throughput_mbps:.1f}MB/s")


if __name__ == "__main__":
    # Run performance tests with detailed output
    pytest.main([__file__, "-v", "-s", "--tb=short"])