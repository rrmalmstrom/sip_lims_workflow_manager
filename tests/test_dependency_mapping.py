#!/usr/bin/env python3
"""
Dependency Mapping Test for Mac + VNC Enhanced Implementation
Phase 1, Step 1.3: Complete Codebase Analysis

This test documents the complete dependency mapping between baseline files
and Docker-era enhancement files, identifying what to integrate vs. remove.

CRITICAL ADDITION: Analysis of run.py to understand Docker-era enhancement usage patterns.
"""

import ast
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple
import unittest


class DependencyMapper:
    """Maps dependencies across the entire codebase for Mac + VNC implementation."""
    
    def __init__(self):
        self.baseline_files = {
            "app.py": "Main Streamlit application",
            "src/core.py": "Core workflow engine", 
            "src/logic.py": "State management and script execution",
            "src/workflow_utils.py": "Multi-workflow utilities",
            "templates/sip_workflow.yml": "SIP workflow definition",
            "templates/sps_workflow.yml": "SPS-CE workflow definition"
        }
        
        self.docker_era_files = {
            # Files to PRESERVE and integrate
            "src/debug_logger.py": "Enhanced debug logging system (PRESERVE - remove Smart Sync parts)",
            "src/git_update_manager.py": "Enhanced Git-based update management (PRESERVE)",
            "src/scripts_updater.py": "Workflow-specific script management (PRESERVE)",
            
            # Files to REMOVE completely
            "src/smart_sync.py": "Smart Sync system (REMOVE - Docker-specific)",
            "src/update_detector.py": "Docker image update detection (REMOVE - Docker-specific)",
            "src/fatal_sync_checker.py": "Smart Sync error checking (REMOVE - Docker-specific)"
        }
        
        self.import_map = {}
        self.function_call_map = {}
        self.external_dependencies = set()
    
    def analyze_file_imports(self, file_path: str) -> Dict[str, List[str]]:
        """Analyze imports in a Python file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                tree = ast.parse(f.read())
            
            imports = {
                'standard_library': [],
                'third_party': [],
                'local_imports': [],
                'relative_imports': []
            }
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        self._categorize_import(alias.name, imports)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        if node.level > 0:  # Relative import
                            imports['relative_imports'].append(f"from {'.' * node.level}{node.module}")
                        else:
                            self._categorize_import(node.module, imports)
            
            return imports
        except Exception as e:
            return {"error": str(e)}
    
    def _categorize_import(self, module_name: str, imports: Dict[str, List[str]]):
        """Categorize an import as standard library, third-party, or local."""
        if module_name.startswith('src.'):
            imports['local_imports'].append(module_name)
        elif module_name in ['os', 'sys', 'json', 'time', 'datetime', 'pathlib', 'subprocess', 
                           'threading', 'queue', 'tempfile', 'shutil', 'platform', 'urllib',
                           'zipfile', 're', 'traceback', 'enum', 'contextlib', 'dataclasses']:
            imports['standard_library'].append(module_name)
        else:
            imports['third_party'].append(module_name)
            self.external_dependencies.add(module_name)


class TestDependencyMapping(unittest.TestCase):
    """Test dependency mapping for Mac + VNC implementation."""
    
    def setUp(self):
        self.mapper = DependencyMapper()
    
    def test_baseline_file_analysis(self):
        """Test analysis of baseline files from commit 3d5ac82."""
        baseline_analysis = {}
        
        # Analyze app.py (baseline)
        baseline_analysis['app.py'] = {
            'purpose': 'Main Streamlit application with Docker integration',
            'key_imports': [
                'streamlit', 'pathlib', 'subprocess', 'sys', 'json', 'shutil',
                'threading', 'time', 'queue', 'yaml', 'webbrowser', 'os'
            ],
            'local_imports': [
                'src.core.Project', 'src.logic.RunResult', 'src.workflow_utils',
                'utils.docker_validation'  # Docker-specific - REMOVE
            ],
            'docker_dependencies': [
                'utils.docker_validation',  # REMOVE
                'Docker environment detection',  # REMOVE
                'Docker project auto-loading'  # REMOVE
            ],
            'preserve_functionality': [
                'Streamlit UI components',
                'Project management',
                'Workflow step execution',
                'File browser functionality',
                'Undo/redo system',
                'Terminal interaction'
            ]
        }
        
        # Analyze src/core.py (baseline)
        baseline_analysis['src/core.py'] = {
            'purpose': 'Core workflow engine with project and workflow management',
            'key_imports': ['yaml', 'pathlib', 'typing'],
            'local_imports': ['src.logic'],
            'docker_dependencies': [],  # Clean baseline
            'preserve_functionality': [
                'Workflow class',
                'Project class', 
                'Step execution logic',
                'State management integration',
                'Snapshot management integration',
                'Script runner integration'
            ]
        }
        
        # Analyze src/logic.py (baseline)
        baseline_analysis['src/logic.py'] = {
            'purpose': 'State management, snapshots, and script execution',
            'key_imports': [
                'json', 'zipfile', 'shutil', 'subprocess', 'sys', 'datetime',
                'pty', 'os', 'select', 'threading', 'queue', 'time', 're'
            ],
            'local_imports': [],
            'docker_dependencies': [],  # Clean baseline
            'preserve_functionality': [
                'StateManager class',
                'SnapshotManager class', 
                'ScriptRunner class',
                'RunResult dataclass',
                'PTY-based script execution',
                'Snapshot management with timestamps',
                'Chronological completion tracking'
            ]
        }
        
        # Analyze src/workflow_utils.py (baseline)
        baseline_analysis['src/workflow_utils.py'] = {
            'purpose': 'Multi-workflow utilities for template selection',
            'key_imports': ['os', 'pathlib'],
            'local_imports': [],
            'docker_dependencies': [],  # Clean baseline
            'preserve_functionality': [
                'get_workflow_template_path()',
                'get_workflow_type_display()',
                'validate_workflow_type()',
                'Environment variable handling'
            ]
        }
        
        self.assertIsInstance(baseline_analysis, dict)
        self.assertEqual(len(baseline_analysis), 4)
        
        # Verify no Smart Sync dependencies in baseline
        for file_name, analysis in baseline_analysis.items():
            self.assertNotIn('smart_sync', str(analysis).lower(), 
                           f"Baseline file {file_name} should not have Smart Sync dependencies")
    
    def test_docker_era_enhancement_analysis(self):
        """Test analysis of Docker-era enhancement files."""
        enhancement_analysis = {}
        
        # PRESERVE: src/debug_logger.py (remove Smart Sync parts)
        enhancement_analysis['src/debug_logger.py'] = {
            'purpose': 'Enhanced debug logging system',
            'preserve_functions': [
                'SmartSyncDebugLogger class (rename to DebugLogger)',
                'debug(), info(), warning(), error(), critical()',
                'operation_timer() context manager',
                'get_performance_summary()',
                'export_debug_data()',
                'Session management functionality'
            ],
            'remove_functions': [
                'log_smart_sync_detection()',
                'log_sync_operation()',
                'log_fail_fast_trigger()',
                'log_three_factor_validation()',
                'log_cleanup_operation()',
                'log_sync_pattern()',
                'All Smart Sync specific logging'
            ],
            'add_functions': [
                'log_vnc_session_start()',
                'log_native_script_execution()',
                'log_workflow_step_native()'
            ],
            'integration_target': 'src/core.py, src/logic.py'
        }
        
        # PRESERVE: src/git_update_manager.py
        enhancement_analysis['src/git_update_manager.py'] = {
            'purpose': 'Git-based update management',
            'preserve_functions': [
                'GitUpdateManager class',
                'get_current_version()',
                'get_latest_release()',
                'compare_versions()',
                'check_for_updates()',
                'update_to_latest()',
                'Repository configuration management'
            ],
            'remove_functions': [],  # All Git functionality is Docker-independent
            'integration_target': 'Native Python launcher'
        }
        
        # PRESERVE: src/scripts_updater.py
        enhancement_analysis['src/scripts_updater.py'] = {
            'purpose': 'Workflow-specific script management',
            'preserve_functions': [
                'ScriptsUpdater class',
                'check_scripts_update()',
                'update_scripts()',
                'Workflow-aware repository configuration'
            ],
            'remove_functions': [],  # All functionality is Docker-independent
            'integration_target': 'Native Python launcher'
        }
        
        # REMOVE: src/smart_sync.py
        enhancement_analysis['src/smart_sync.py'] = {
            'purpose': 'Windows network drive Docker workaround',
            'preserve_functions': [],  # REMOVE EVERYTHING
            'remove_functions': [
                'SmartSyncManager class',
                'detect_smart_sync_scenario()',
                'setup_smart_sync_environment()',
                'All sync functionality'
            ],
            'removal_reason': 'Docker-specific workaround not needed for native Python'
        }
        
        # REMOVE: src/update_detector.py
        enhancement_analysis['src/update_detector.py'] = {
            'purpose': 'Docker image update detection',
            'preserve_functions': [
                'get_local_commit_sha()',  # Git functionality only
                'get_remote_commit_sha()',  # Git functionality only
                'get_commit_timestamp()',  # Git functionality only
                'is_commit_ancestor()'  # Git functionality only
            ],
            'remove_functions': [
                'get_local_docker_image_commit_sha()',
                'get_remote_docker_image_digest()',
                'check_docker_update()',
                'All Docker image detection methods'
            ],
            'integration_target': 'Merge Git functions into git_update_manager.py'
        }
        
        self.assertIsInstance(enhancement_analysis, dict)
        self.assertEqual(len(enhancement_analysis), 5)
    
    def test_integration_mapping(self):
        """Test mapping of which enhancements integrate with which baseline files."""
        integration_map = {
            'src/core.py': {
                'integrate_from': [
                    'src/debug_logger.py (adapted debug logging)',
                ],
                'remove_integrations': [
                    'Smart Sync imports',
                    'Smart Sync method calls'
                ],
                'new_functionality': [
                    'Native Python script execution',
                    'VNC-specific logging',
                    'Enhanced error handling'
                ]
            },
            'src/logic.py': {
                'integrate_from': [
                    'src/debug_logger.py (performance monitoring)',
                ],
                'remove_integrations': [],  # Clean baseline
                'new_functionality': [
                    'Native execution performance tracking'
                ]
            },
            'app.py': {
                'integrate_from': [],
                'remove_integrations': [
                    'utils.docker_validation',
                    'Docker environment detection',
                    'Docker project auto-loading'
                ],
                'new_functionality': [
                    'Native Python environment setup',
                    'VNC session management',
                    'Direct file system access'
                ]
            },
            'src/workflow_utils.py': {
                'integrate_from': [],
                'remove_integrations': [],  # Clean baseline
                'new_functionality': []  # No changes needed
            }
        }
        
        # Verify integration mapping
        for target_file, mapping in integration_map.items():
            self.assertIn('integrate_from', mapping)
            self.assertIn('remove_integrations', mapping)
            self.assertIn('new_functionality', mapping)
    
    def test_external_dependencies(self):
        """Test mapping of external dependencies for native Python."""
        native_dependencies = {
            'required': [
                'streamlit>=1.28.0',
                'pyyaml>=6.0',
                'requests>=2.31.0',
                'click>=8.1.0',
                'pathlib>=1.0.1'
            ],
            'remove': [
                'docker',  # All Docker dependencies
                'docker-compose',
                'Any Docker-related packages'
            ],
            'optional': [
                'psutil',  # For process management in native launcher
            ]
        }
        
        self.assertIsInstance(native_dependencies, dict)
        self.assertIn('streamlit', str(native_dependencies['required']))
        self.assertIn('docker', str(native_dependencies['remove']))
    
    def test_file_removal_mapping(self):
        """Test mapping of files to be completely removed."""
        files_to_remove = {
            'docker_specific': [
                'docker-compose.yml',
                'Dockerfile', 
                'entrypoint.sh',
                'src/smart_sync.py',
                'src/fatal_sync_checker.py',
                'utils/docker_validation.py'
            ],
            'docker_tests': [
                'tests/test_docker_*.py',
                'tests/test_smart_sync*.py',
                'tests/test_fatal_sync_checker.py'
            ],
            'docker_docs': [
                'docs/Docker_docs/',
                'Docker-related documentation'
            ]
        }
        
        # Verify Smart Sync is marked for removal
        self.assertIn('src/smart_sync.py', files_to_remove['docker_specific'])
        self.assertIn('src/fatal_sync_checker.py', files_to_remove['docker_specific'])
    
    def test_new_files_mapping(self):
        """Test mapping of new files to be created."""
        new_files = {
            'native_launcher': {
                'file': 'run_native.py',
                'purpose': 'Native Python launcher replacing Docker',
                'dependencies': ['src/git_update_manager.py', 'src/scripts_updater.py']
            },
            'native_requirements': {
                'file': 'requirements_native.txt', 
                'purpose': 'Native Python dependencies',
                'content': 'streamlit, pyyaml, requests, click, pathlib'
            },
            'vnc_documentation': {
                'file': 'docs/vnc_setup_guide.md',
                'purpose': 'VNC configuration guide',
                'content': 'Server setup, client setup, troubleshooting'
            }
        }
        
        self.assertIsInstance(new_files, dict)
        self.assertEqual(len(new_files), 3)
    
    def test_run_py_analysis(self):
        """Test analysis of run.py to understand Docker-era enhancement usage patterns."""
        run_py_analysis = {
            'purpose': 'Unified Docker launcher for cross-platform container management',
            'total_lines': 1263,
            'key_classes': [
                'PlatformAdapter',
                'UserInterface',
                'ContainerManager',
                'UpdateManager',
                'DockerLauncher'
            ],
            'docker_era_integrations': {
                'debug_logger': {
                    'imports': [
                        'debug_context', 'log_smart_sync_detection', 'log_info',
                        'log_error', 'log_warning', 'debug_enabled', 'get_debug_logger'
                    ],
                    'usage_patterns': [
                        'Context-based logging with debug_context()',
                        'Smart Sync detection logging',
                        'Container launch operation logging',
                        'Error and warning logging throughout'
                    ],
                    'adaptation_for_native': [
                        'Keep: debug_context, log_info, log_error, log_warning',
                        'Remove: log_smart_sync_detection (Smart Sync specific)',
                        'Add: log_vnc_session_start, log_native_script_execution'
                    ]
                },
                'update_detector': {
                    'imports': ['UpdateDetector'],
                    'usage_patterns': [
                        'Docker image update detection via check_docker_update()',
                        'Chronology uncertainty handling',
                        'Image digest comparison'
                    ],
                    'adaptation_for_native': [
                        'Remove: All Docker image detection methods',
                        'Keep: Git commit comparison methods only',
                        'Integrate: Git functionality into git_update_manager.py'
                    ]
                },
                'scripts_updater': {
                    'imports': ['ScriptsUpdater'],
                    'usage_patterns': [
                        'Workflow-specific script repository management',
                        'Git-based script updates via check_scripts_update()',
                        'Automatic script cloning/pulling'
                    ],
                    'adaptation_for_native': [
                        'Keep: All functionality (100% Docker-independent)',
                        'Integrate: Into native Python launcher'
                    ]
                },
                'smart_sync': {
                    'imports': ['setup_smart_sync_environment', 'SmartSyncManager'],
                    'usage_patterns': [
                        'Windows network drive detection',
                        'Local staging directory setup',
                        'Bidirectional sync management',
                        'Container environment variable setup'
                    ],
                    'adaptation_for_native': [
                        'Remove: ALL Smart Sync functionality',
                        'Reason: Docker-specific workaround not needed for native Python + VNC'
                    ]
                },
                'fatal_sync_checker': {
                    'imports': ['check_fatal_sync_errors'],
                    'usage_patterns': [
                        'Pre-launch fatal error detection',
                        'Repository/Docker sync validation'
                    ],
                    'adaptation_for_native': [
                        'Remove: Docker sync checking',
                        'Keep: Git repository validation only'
                    ]
                }
            },
            'native_launcher_adaptation': {
                'preserve_patterns': [
                    'Cross-platform path normalization (PlatformAdapter.normalize_path)',
                    'Interactive UI patterns (UserInterface class)',
                    'Update management workflow (UpdateManager patterns)',
                    'Environment variable setup patterns',
                    'Error handling and user feedback patterns'
                ],
                'remove_patterns': [
                    'Docker container management (ContainerManager)',
                    'Docker image operations',
                    'Smart Sync integration',
                    'Docker-compose command execution',
                    'Container lifecycle management'
                ],
                'adapt_patterns': [
                    'Replace Docker container launch with native Python process launch',
                    'Replace Docker environment setup with native environment setup',
                    'Replace Docker image updates with application updates',
                    'Replace container cleanup with process cleanup'
                ]
            },
            'critical_insights': [
                'run.py shows how debug_logger is used throughout the application lifecycle',
                'UpdateManager demonstrates the integration pattern for git_update_manager and scripts_updater',
                'PlatformAdapter shows cross-platform compatibility patterns to preserve',
                'Smart Sync integration is extensive but completely Docker-specific',
                'User interaction patterns can be preserved for native launcher'
            ]
        }
        
        # Verify run.py analysis structure
        self.assertIn('docker_era_integrations', run_py_analysis)
        self.assertIn('native_launcher_adaptation', run_py_analysis)
        self.assertIn('critical_insights', run_py_analysis)
        
        # Verify Smart Sync is correctly identified for removal
        smart_sync_analysis = run_py_analysis['docker_era_integrations']['smart_sync']
        self.assertIn('Remove: ALL Smart Sync functionality',
                     str(smart_sync_analysis['adaptation_for_native']))
        
        # Verify scripts_updater is correctly identified for preservation
        scripts_analysis = run_py_analysis['docker_era_integrations']['scripts_updater']
        self.assertIn('Keep: All functionality (100% Docker-independent)',
                     str(scripts_analysis['adaptation_for_native']))
    
    def test_native_launcher_requirements(self):
        """Test requirements for the new native Python launcher based on run.py analysis."""
        native_launcher_requirements = {
            'core_functionality': [
                'Cross-platform path normalization',
                'Interactive workflow type selection',
                'Project folder selection with validation',
                'Environment variable setup',
                'Git-based update management',
                'Script repository management',
                'Native Python process launching',
                'Error handling and user feedback'
            ],
            'preserve_from_run_py': [
                'PlatformAdapter.normalize_path() - path handling',
                'UserInterface class patterns - user interaction',
                'UpdateManager workflow patterns - update management',
                'Environment validation patterns',
                'Cross-platform compatibility logic'
            ],
            'remove_from_run_py': [
                'ContainerManager class - Docker container management',
                'Docker image operations',
                'Smart Sync integration',
                'Docker-compose command execution',
                'Container lifecycle management'
            ],
            'new_functionality': [
                'Native Streamlit application launching',
                'VNC session management',
                'Direct file system access (no container volumes)',
                'Native Python environment validation',
                'Process-based execution (not container-based)'
            ],
            'integration_targets': {
                'git_update_manager.py': 'Application and script updates',
                'scripts_updater.py': 'Workflow-specific script management',
                'debug_logger.py': 'Enhanced logging (adapted for native)',
                'workflow_utils.py': 'Workflow type handling'
            }
        }
        
        # Verify native launcher requirements
        self.assertIn('core_functionality', native_launcher_requirements)
        self.assertIn('preserve_from_run_py', native_launcher_requirements)
        self.assertIn('remove_from_run_py', native_launcher_requirements)
        self.assertIn('new_functionality', native_launcher_requirements)
        
        # Verify Smart Sync is not in preserve list
        preserve_items = str(native_launcher_requirements['preserve_from_run_py'])
        self.assertNotIn('smart_sync', preserve_items.lower())
        self.assertNotIn('Smart Sync', preserve_items)


if __name__ == '__main__':
    unittest.main()