#!/usr/bin/env python3
"""
Smart Sync Debug Log Analyzer

This tool analyzes Smart Sync debug log files to help troubleshoot issues,
identify performance bottlenecks, and understand system behavior.

Usage:
    python debug_log_analyzer.py [log_file]
    python debug_log_analyzer.py --help

Features:
- Parse and analyze structured JSON log entries
- Generate performance reports and statistics
- Identify error patterns and failure points
- Create timeline analysis of operations
- Export analysis reports in multiple formats
"""

import json
import sys
import argparse
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone
from collections import defaultdict, Counter
import statistics


class SmartSyncLogAnalyzer:
    """
    Comprehensive analyzer for Smart Sync debug logs.
    """
    
    def __init__(self, log_file: Path):
        """Initialize the analyzer with a log file."""
        self.log_file = Path(log_file)
        self.entries = []
        self.sessions = {}
        self.analysis_results = {}
        
        if not self.log_file.exists():
            raise FileNotFoundError(f"Log file not found: {log_file}")
        
        self._load_entries()
        self._parse_sessions()
    
    def _load_entries(self):
        """Load and parse log entries from the file."""
        print(f"📖 Loading log entries from: {self.log_file}")
        
        with open(self.log_file, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                
                try:
                    entry = json.loads(line)
                    entry['_line_number'] = line_num
                    self.entries.append(entry)
                except json.JSONDecodeError as e:
                    print(f"⚠️ Warning: Invalid JSON on line {line_num}: {e}")
                    continue
        
        print(f"✅ Loaded {len(self.entries)} log entries")
    
    def _parse_sessions(self):
        """Parse entries into sessions for analysis."""
        for entry in self.entries:
            session_id = entry.get('session_id', 'unknown')
            if session_id not in self.sessions:
                self.sessions[session_id] = {
                    'entries': [],
                    'start_time': None,
                    'end_time': None,
                    'duration': None,
                    'operations': [],
                    'errors': [],
                    'performance_data': []
                }
            
            self.sessions[session_id]['entries'].append(entry)
            
            # Track session timing
            if entry.get('level') == 'SESSION_START':
                self.sessions[session_id]['start_time'] = entry.get('timestamp')
            elif entry.get('level') == 'SESSION_END':
                self.sessions[session_id]['end_time'] = entry.get('timestamp')
                details = entry.get('details', {})
                self.sessions[session_id]['duration'] = details.get('session_duration')
            
            # Track operations and errors
            if 'operation_id' in entry.get('details', {}):
                self.sessions[session_id]['operations'].append(entry)
            
            if entry.get('level') == 'ERROR':
                self.sessions[session_id]['errors'].append(entry)
            
            # Track performance data
            details = entry.get('details', {})
            if 'duration' in details:
                self.sessions[session_id]['performance_data'].append(entry)
        
        print(f"📊 Parsed {len(self.sessions)} debug sessions")
    
    def analyze_performance(self) -> Dict[str, Any]:
        """Analyze performance metrics from the logs."""
        print("⚡ Analyzing performance metrics...")
        
        performance_analysis = {
            'sync_operations': [],
            'file_operations': [],
            'operation_timings': defaultdict(list),
            'slowest_operations': [],
            'fastest_operations': [],
            'average_durations': {},
            'total_operations': 0
        }
        
        for session_id, session in self.sessions.items():
            for entry in session['performance_data']:
                details = entry.get('details', {})
                duration = details.get('duration', 0)
                operation_name = details.get('operation', 'unknown')
                
                # Categorize operations
                message = entry.get('message', '').lower()
                if 'sync' in message:
                    performance_analysis['sync_operations'].append({
                        'session': session_id,
                        'operation': operation_name,
                        'duration': duration,
                        'message': entry.get('message'),
                        'timestamp': entry.get('timestamp'),
                        'details': details
                    })
                elif 'file' in message:
                    performance_analysis['file_operations'].append({
                        'session': session_id,
                        'operation': operation_name,
                        'duration': duration,
                        'message': entry.get('message'),
                        'timestamp': entry.get('timestamp'),
                        'details': details
                    })
                
                # Track operation timings
                performance_analysis['operation_timings'][operation_name].append(duration)
                performance_analysis['total_operations'] += 1
        
        # Calculate statistics
        for operation, durations in performance_analysis['operation_timings'].items():
            if durations:
                performance_analysis['average_durations'][operation] = {
                    'mean': statistics.mean(durations),
                    'median': statistics.median(durations),
                    'min': min(durations),
                    'max': max(durations),
                    'count': len(durations)
                }
        
        # Find slowest and fastest operations
        all_ops = []
        for session_id, session in self.sessions.items():
            for entry in session['performance_data']:
                details = entry.get('details', {})
                duration = details.get('duration', 0)
                all_ops.append({
                    'session': session_id,
                    'operation': details.get('operation', 'unknown'),
                    'duration': duration,
                    'message': entry.get('message'),
                    'timestamp': entry.get('timestamp')
                })
        
        if all_ops:
            all_ops.sort(key=lambda x: x['duration'], reverse=True)
            performance_analysis['slowest_operations'] = all_ops[:10]
            performance_analysis['fastest_operations'] = all_ops[-10:]
        
        self.analysis_results['performance'] = performance_analysis
        return performance_analysis
    
    def analyze_errors(self) -> Dict[str, Any]:
        """Analyze error patterns and failure points."""
        print("🔍 Analyzing error patterns...")
        
        error_analysis = {
            'total_errors': 0,
            'error_types': Counter(),
            'error_timeline': [],
            'error_sessions': [],
            'common_error_messages': Counter(),
            'error_contexts': defaultdict(list)
        }
        
        for session_id, session in self.sessions.items():
            if session['errors']:
                error_analysis['error_sessions'].append({
                    'session_id': session_id,
                    'error_count': len(session['errors']),
                    'errors': session['errors']
                })
            
            for error_entry in session['errors']:
                error_analysis['total_errors'] += 1
                
                # Categorize error types
                details = error_entry.get('details', {})
                error_type = details.get('error_type', 'unknown')
                error_analysis['error_types'][error_type] += 1
                
                # Track error messages
                message = error_entry.get('message', '')
                error_analysis['common_error_messages'][message] += 1
                
                # Build error timeline
                error_analysis['error_timeline'].append({
                    'timestamp': error_entry.get('timestamp'),
                    'session': session_id,
                    'message': message,
                    'details': details
                })
                
                # Track error contexts
                context = details.get('context', 'unknown')
                error_analysis['error_contexts'][context].append(error_entry)
        
        # Sort timeline by timestamp
        error_analysis['error_timeline'].sort(key=lambda x: x['timestamp'] or '')
        
        self.analysis_results['errors'] = error_analysis
        return error_analysis
    
    def analyze_smart_sync_operations(self) -> Dict[str, Any]:
        """Analyze Smart Sync specific operations and patterns."""
        print("🔄 Analyzing Smart Sync operations...")
        
        sync_analysis = {
            'detection_calls': [],
            'sync_operations': [],
            'environment_setups': [],
            'workflow_integrations': [],
            'container_launches': [],
            'sync_success_rate': 0,
            'average_sync_duration': 0,
            'sync_patterns': defaultdict(int)
        }
        
        successful_syncs = 0
        total_syncs = 0
        sync_durations = []
        
        for session_id, session in self.sessions.items():
            for entry in session['entries']:
                message = entry.get('message', '').lower()
                details = entry.get('details', {})
                
                # Categorize Smart Sync operations
                if 'detection' in message:
                    sync_analysis['detection_calls'].append({
                        'session': session_id,
                        'timestamp': entry.get('timestamp'),
                        'detected': details.get('detected', False),
                        'platform': details.get('platform', 'unknown'),
                        'project_path': details.get('project_path', 'unknown')
                    })
                
                elif 'sync' in message:
                    sync_analysis['sync_operations'].append({
                        'session': session_id,
                        'timestamp': entry.get('timestamp'),
                        'sync_type': details.get('sync_type', 'unknown'),
                        'direction': details.get('direction', 'unknown'),
                        'success': details.get('success', False),
                        'duration': details.get('duration', 0),
                        'files_affected': details.get('files_affected', 0)
                    })
                    
                    total_syncs += 1
                    if details.get('success', False):
                        successful_syncs += 1
                    
                    duration = details.get('duration', 0)
                    if duration > 0:
                        sync_durations.append(duration)
                
                elif 'environment setup' in message:
                    sync_analysis['environment_setups'].append({
                        'session': session_id,
                        'timestamp': entry.get('timestamp'),
                        'success': details.get('success', False),
                        'network_path': details.get('network_path', 'unknown'),
                        'local_path': details.get('local_path', 'unknown')
                    })
                
                elif 'workflow' in message:
                    sync_analysis['workflow_integrations'].append({
                        'session': session_id,
                        'timestamp': entry.get('timestamp'),
                        'step_id': details.get('step_id', 'unknown'),
                        'sync_type': details.get('sync_type', 'unknown'),
                        'success': details.get('success', False)
                    })
                
                elif 'container' in message:
                    sync_analysis['container_launches'].append({
                        'session': session_id,
                        'timestamp': entry.get('timestamp'),
                        'smart_sync_enabled': details.get('smart_sync_enabled', False),
                        'project_path': details.get('project_path', 'unknown')
                    })
                
                # Track sync patterns
                sync_type = details.get('sync_type', '')
                if sync_type:
                    sync_analysis['sync_patterns'][sync_type] += 1
        
        # Calculate success rate and average duration
        if total_syncs > 0:
            sync_analysis['sync_success_rate'] = successful_syncs / total_syncs * 100
        
        if sync_durations:
            sync_analysis['average_sync_duration'] = statistics.mean(sync_durations)
        
        self.analysis_results['smart_sync'] = sync_analysis
        return sync_analysis
    
    def generate_timeline_analysis(self) -> Dict[str, Any]:
        """Generate a timeline analysis of all operations."""
        print("📅 Generating timeline analysis...")
        
        timeline_analysis = {
            'sessions': [],
            'operation_flow': [],
            'critical_path': [],
            'bottlenecks': []
        }
        
        for session_id, session in self.sessions.items():
            session_timeline = {
                'session_id': session_id,
                'start_time': session['start_time'],
                'end_time': session['end_time'],
                'duration': session['duration'],
                'operations': []
            }
            
            # Sort entries by timestamp
            sorted_entries = sorted(session['entries'], 
                                  key=lambda x: x.get('timestamp', ''))
            
            for entry in sorted_entries:
                details = entry.get('details', {})
                if 'operation_id' in details or entry.get('level') in ['ERROR', 'WARNING']:
                    session_timeline['operations'].append({
                        'timestamp': entry.get('timestamp'),
                        'level': entry.get('level'),
                        'message': entry.get('message'),
                        'operation_id': details.get('operation_id'),
                        'duration': details.get('duration'),
                        'context': details.get('context', {})
                    })
            
            timeline_analysis['sessions'].append(session_timeline)
        
        self.analysis_results['timeline'] = timeline_analysis
        return timeline_analysis
    
    def generate_summary_report(self) -> Dict[str, Any]:
        """Generate a comprehensive summary report."""
        print("📋 Generating summary report...")
        
        # Run all analyses if not already done
        if 'performance' not in self.analysis_results:
            self.analyze_performance()
        if 'errors' not in self.analysis_results:
            self.analyze_errors()
        if 'smart_sync' not in self.analysis_results:
            self.analyze_smart_sync_operations()
        if 'timeline' not in self.analysis_results:
            self.generate_timeline_analysis()
        
        summary = {
            'log_file': str(self.log_file),
            'analysis_timestamp': datetime.now(timezone.utc).isoformat(),
            'total_entries': len(self.entries),
            'total_sessions': len(self.sessions),
            'overview': {
                'total_operations': self.analysis_results['performance']['total_operations'],
                'total_errors': self.analysis_results['errors']['total_errors'],
                'sync_success_rate': self.analysis_results['smart_sync']['sync_success_rate'],
                'average_sync_duration': self.analysis_results['smart_sync']['average_sync_duration']
            },
            'key_findings': [],
            'recommendations': []
        }
        
        # Generate key findings
        perf = self.analysis_results['performance']
        errors = self.analysis_results['errors']
        sync = self.analysis_results['smart_sync']
        
        if errors['total_errors'] > 0:
            summary['key_findings'].append(f"Found {errors['total_errors']} errors across {len(errors['error_sessions'])} sessions")
        
        if sync['sync_success_rate'] < 100:
            summary['key_findings'].append(f"Sync success rate: {sync['sync_success_rate']:.1f}%")
        
        if perf['slowest_operations']:
            slowest = perf['slowest_operations'][0]
            summary['key_findings'].append(f"Slowest operation: {slowest['operation']} ({slowest['duration']:.3f}s)")
        
        # Generate recommendations
        if errors['total_errors'] > 5:
            summary['recommendations'].append("High error count detected - investigate error patterns")
        
        if sync['sync_success_rate'] < 95:
            summary['recommendations'].append("Low sync success rate - check network connectivity and permissions")
        
        if sync['average_sync_duration'] > 5.0:
            summary['recommendations'].append("Slow sync operations detected - consider optimizing file transfer")
        
        self.analysis_results['summary'] = summary
        return summary
    
    def export_analysis(self, output_file: Optional[Path] = None, format: str = 'json') -> Path:
        """Export the complete analysis to a file."""
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = self.log_file.parent / f"smart_sync_analysis_{timestamp}.{format}"
        
        output_file = Path(output_file)
        
        if format == 'json':
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(self.analysis_results, f, indent=2, default=str)
        elif format == 'txt':
            self._export_text_report(output_file)
        else:
            raise ValueError(f"Unsupported format: {format}")
        
        print(f"📄 Analysis exported to: {output_file}")
        return output_file
    
    def _export_text_report(self, output_file: Path):
        """Export a human-readable text report."""
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("SMART SYNC DEBUG LOG ANALYSIS REPORT\n")
            f.write("=" * 50 + "\n\n")
            
            # Summary
            summary = self.analysis_results.get('summary', {})
            f.write(f"Log File: {summary.get('log_file', 'Unknown')}\n")
            f.write(f"Analysis Date: {summary.get('analysis_timestamp', 'Unknown')}\n")
            f.write(f"Total Entries: {summary.get('total_entries', 0)}\n")
            f.write(f"Total Sessions: {summary.get('total_sessions', 0)}\n\n")
            
            # Overview
            overview = summary.get('overview', {})
            f.write("OVERVIEW\n")
            f.write("-" * 20 + "\n")
            f.write(f"Total Operations: {overview.get('total_operations', 0)}\n")
            f.write(f"Total Errors: {overview.get('total_errors', 0)}\n")
            f.write(f"Sync Success Rate: {overview.get('sync_success_rate', 0):.1f}%\n")
            f.write(f"Average Sync Duration: {overview.get('average_sync_duration', 0):.3f}s\n\n")
            
            # Key Findings
            findings = summary.get('key_findings', [])
            if findings:
                f.write("KEY FINDINGS\n")
                f.write("-" * 20 + "\n")
                for finding in findings:
                    f.write(f"• {finding}\n")
                f.write("\n")
            
            # Recommendations
            recommendations = summary.get('recommendations', [])
            if recommendations:
                f.write("RECOMMENDATIONS\n")
                f.write("-" * 20 + "\n")
                for rec in recommendations:
                    f.write(f"• {rec}\n")
                f.write("\n")
            
            # Error Details
            errors = self.analysis_results.get('errors', {})
            if errors.get('total_errors', 0) > 0:
                f.write("ERROR ANALYSIS\n")
                f.write("-" * 20 + "\n")
                f.write(f"Total Errors: {errors['total_errors']}\n")
                
                f.write("\nMost Common Error Messages:\n")
                for message, count in errors['common_error_messages'].most_common(5):
                    f.write(f"  {count}x: {message}\n")
                f.write("\n")
            
            # Performance Details
            perf = self.analysis_results.get('performance', {})
            if perf.get('slowest_operations'):
                f.write("PERFORMANCE ANALYSIS\n")
                f.write("-" * 20 + "\n")
                f.write("Slowest Operations:\n")
                for i, op in enumerate(perf['slowest_operations'][:5], 1):
                    f.write(f"  {i}. {op['operation']}: {op['duration']:.3f}s\n")
                f.write("\n")
    
    def print_summary(self):
        """Print a summary of the analysis to console."""
        if 'summary' not in self.analysis_results:
            self.generate_summary_report()
        
        summary = self.analysis_results['summary']
        
        print("\n" + "=" * 60)
        print("🔍 SMART SYNC DEBUG LOG ANALYSIS SUMMARY")
        print("=" * 60)
        print(f"📁 Log File: {summary['log_file']}")
        print(f"📊 Total Entries: {summary['total_entries']}")
        print(f"🔄 Total Sessions: {summary['total_sessions']}")
        
        overview = summary['overview']
        print(f"\n📈 OVERVIEW:")
        print(f"  • Operations: {overview['total_operations']}")
        print(f"  • Errors: {overview['total_errors']}")
        print(f"  • Sync Success Rate: {overview['sync_success_rate']:.1f}%")
        print(f"  • Average Sync Duration: {overview['average_sync_duration']:.3f}s")
        
        if summary['key_findings']:
            print(f"\n🔍 KEY FINDINGS:")
            for finding in summary['key_findings']:
                print(f"  • {finding}")
        
        if summary['recommendations']:
            print(f"\n💡 RECOMMENDATIONS:")
            for rec in summary['recommendations']:
                print(f"  • {rec}")
        
        print("=" * 60)


def main():
    """Main function for command-line usage."""
    parser = argparse.ArgumentParser(
        description="Analyze Smart Sync debug log files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python debug_log_analyzer.py .smart_sync_debug.log
  python debug_log_analyzer.py --format txt --output report.txt debug.log
  python debug_log_analyzer.py --summary-only debug.log
        """
    )
    
    parser.add_argument('log_file', 
                       help='Path to the Smart Sync debug log file')
    parser.add_argument('--output', '-o',
                       help='Output file for analysis report')
    parser.add_argument('--format', '-f',
                       choices=['json', 'txt'],
                       default='json',
                       help='Output format (default: json)')
    parser.add_argument('--summary-only', '-s',
                       action='store_true',
                       help='Only print summary to console')
    
    args = parser.parse_args()
    
    try:
        # Initialize analyzer
        analyzer = SmartSyncLogAnalyzer(args.log_file)
        
        if args.summary_only:
            # Just print summary
            analyzer.generate_summary_report()
            analyzer.print_summary()
        else:
            # Full analysis
            analyzer.analyze_performance()
            analyzer.analyze_errors()
            analyzer.analyze_smart_sync_operations()
            analyzer.generate_timeline_analysis()
            analyzer.generate_summary_report()
            
            # Print summary
            analyzer.print_summary()
            
            # Export full analysis
            output_file = analyzer.export_analysis(args.output, args.format)
            print(f"\n📄 Full analysis saved to: {output_file}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error analyzing log file: {e}")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)