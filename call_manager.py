import json
import threading
from datetime import datetime, timedelta
from collections import defaultdict
import os

class CallManager:
    def __init__(self):
        self.active_calls = {}
        self.call_history = []
        self.lock = threading.Lock()
        self.data_file = 'data/calls.json'
        self.has_new_updates = False
        
        # Load existing call history
        self.load_call_history()
        
        # Start cleanup timer for orphaned calls
        self.start_cleanup_timer()
        
    def start_call(self, call_id, session_info):
        """Start tracking a new call"""
        with self.lock:
            call_data = {
                'call_id': call_id,
                'start_time': datetime.now().isoformat(),
                'end_time': None,
                'duration': 0,
                'from': session_info.get('from', ''),
                'to': session_info.get('to', ''),
                'from_address': session_info.get('from', ''),
                'to_address': session_info.get('to', ''),
                'status': 'active',
                'quality_metrics': [],
                'avg_mos': 0,
                'min_mos': 5.0,
                'max_mos': 1.0,
                'packet_loss_rate': 0,
                'avg_jitter': 0,
                'avg_delay': 0
            }
            
            self.active_calls[call_id] = call_data
            self.has_new_updates = True
            
            print(f"Call started: {call_id}")
            
    def end_call(self, call_id):
        """End a call and move to history"""
        with self.lock:
            if call_id in self.active_calls:
                call_data = self.active_calls[call_id]
                
                # Calculate final statistics
                end_time = datetime.now()
                start_time = datetime.fromisoformat(call_data['start_time'])
                duration = (end_time - start_time).total_seconds()
                
                call_data['end_time'] = end_time.isoformat()
                call_data['duration'] = duration
                call_data['status'] = 'completed'
                
                # Calculate average metrics
                if call_data['quality_metrics']:
                    metrics = call_data['quality_metrics']
                    call_data['avg_mos'] = sum(m['mos_score'] for m in metrics) / len(metrics)
                    call_data['avg_jitter'] = sum(m['jitter'] for m in metrics) / len(metrics)
                    call_data['avg_delay'] = sum(m['delay'] for m in metrics) / len(metrics)
                    call_data['min_mos'] = min(m['mos_score'] for m in metrics)
                    call_data['max_mos'] = max(m['mos_score'] for m in metrics)
                
                # Move to history
                self.call_history.append(call_data)
                del self.active_calls[call_id]
                
                # Save to file
                self.save_call_history()
                self.has_new_updates = True
                
                print(f"Call ended: {call_id}, Duration: {duration:.2f}s")
                
    def update_call_metrics(self, call_id, metrics):
        """Update quality metrics for an active call"""
        with self.lock:
            if call_id in self.active_calls:
                call_data = self.active_calls[call_id]
                call_data['quality_metrics'].append(metrics)
                
                # Keep only last 100 metrics to prevent memory issues
                if len(call_data['quality_metrics']) > 100:
                    call_data['quality_metrics'] = call_data['quality_metrics'][-100:]
                
                # Update current statistics
                current_metrics = call_data['quality_metrics']
                if current_metrics:
                    latest = current_metrics[-1]
                    call_data['current_mos'] = latest['mos_score']
                    call_data['current_jitter'] = latest['jitter']
                    call_data['current_packet_loss'] = latest['packet_loss_rate']
                    call_data['codec'] = latest['codec']
                    print(f"CALL MANAGER UPDATE - Call {call_id}: MOS={latest['mos_score']:.2f}, Loss={latest['packet_loss_rate']:.2f}%, Jitter={latest['jitter']:.2f}ms")
                
                # Mark as having updates for WebSocket broadcast
                self.has_new_updates = True
                
                if current_metrics:
                    latest = current_metrics[-1]
                    call_data['current_mos'] = latest['mos_score']
                    call_data['packet_loss_rate'] = latest['packet_loss_rate']
                    call_data['current_jitter'] = latest['jitter']
                    call_data['current_delay'] = latest['delay']
                
                self.has_new_updates = True
                
    def get_active_calls(self):
        """Get list of currently active calls"""
        with self.lock:
            return list(self.active_calls.values())
            
    def get_call_history(self, limit=100):
        """Get call history with optional limit"""
        with self.lock:
            # Sort by start time (most recent first)
            sorted_history = sorted(
                self.call_history,
                key=lambda x: x['start_time'],
                reverse=True
            )
            return sorted_history[:limit]
            
    def is_call_active(self, call_id):
        """Check if a call is currently active"""
        with self.lock:
            return call_id in self.active_calls
            
    def has_updates(self):
        """Check if there are new updates"""
        if self.has_new_updates:
            self.has_new_updates = False
            return True
        return False
        
    def get_summary_stats(self):
        """Get summary statistics"""
        with self.lock:
            now = datetime.now()
            today_start = datetime.combine(now.date(), datetime.min.time())
            today_end = datetime.combine(now.date(), datetime.max.time())
            
            # Count today's calls (including active ones)
            today_calls_count = 0
            
            # Count completed calls from today
            for call in self.call_history:
                call_time = datetime.fromisoformat(call['start_time'])
                if today_start <= call_time <= today_end:
                    today_calls_count += 1
            
            # Count active calls started today
            for call_id, call_data in self.active_calls.items():
                call_time = datetime.fromisoformat(call_data['start_time'])
                if today_start <= call_time <= today_end:
                    today_calls_count += 1
            
            # Calculate statistics for different time periods
            stats = {
                'total_calls': len(self.call_history),
                'active_calls': len(self.active_calls),
                'today_calls': today_calls_count,  # Add explicit today count
                'today': self._get_period_stats(now.date(), now.date()),
                'last_24h': self._get_period_stats(now - timedelta(days=1), now),
                'last_7d': self._get_period_stats(now - timedelta(days=7), now),
                'last_30d': self._get_period_stats(now - timedelta(days=30), now)
            }
            
            print(f"DEBUG: Today's calls count: {today_calls_count} (active: {len(self.active_calls)}, completed: {stats['today']['call_count']})")
            
            return stats
            
    def _get_period_stats(self, start_time, end_time):
        """Get statistics for a specific time period"""
        period_calls = []
        
        for call in self.call_history:
            call_time = datetime.fromisoformat(call['start_time'])
            
            # Handle date vs datetime comparison
            if hasattr(start_time, 'date'):
                start_check = start_time
            else:
                start_check = datetime.combine(start_time, datetime.min.time())
                
            if hasattr(end_time, 'date'):
                end_check = end_time
            else:
                end_check = datetime.combine(end_time, datetime.max.time())
                
            if start_check <= call_time <= end_check:
                period_calls.append(call)
                
        if not period_calls:
            return {
                'call_count': 0,
                'avg_duration': 0,
                'avg_mos': 0,
                'avg_packet_loss': 0,
                'avg_jitter': 0,
                'quality_distribution': {}
            }
            
        # Calculate statistics
        total_duration = sum(call['duration'] for call in period_calls)
        total_mos = sum(call['avg_mos'] for call in period_calls if call['avg_mos'] > 0)
        total_packet_loss = sum(call['packet_loss_rate'] for call in period_calls)
        total_jitter = sum(call['avg_jitter'] for call in period_calls)
        
        avg_mos = total_mos / len(period_calls) if total_mos > 0 else 0
        
        # Quality distribution
        quality_dist = defaultdict(int)
        for call in period_calls:
            if call['avg_mos'] >= 4.0:
                quality_dist['excellent'] += 1
            elif call['avg_mos'] >= 3.5:
                quality_dist['good'] += 1
            elif call['avg_mos'] >= 3.0:
                quality_dist['fair'] += 1
            elif call['avg_mos'] >= 2.0:
                quality_dist['poor'] += 1
            else:
                quality_dist['bad'] += 1
                
        return {
            'call_count': len(period_calls),
            'avg_duration': total_duration / len(period_calls),
            'avg_mos': avg_mos,
            'avg_packet_loss': total_packet_loss / len(period_calls),
            'avg_jitter': total_jitter / len(period_calls),
            'quality_distribution': dict(quality_dist)
        }
    
    def clear_call_history(self):
        """Clear all call history"""
        with self.lock:
            self.call_history = []
            self.save_call_history()
            self.has_new_updates = True
            print("Call history cleared")
        
    def save_call_history(self):
        """Save call history to file"""
        try:
            with open(self.data_file, 'w') as f:
                json.dump(self.call_history, f, indent=2)
        except Exception as e:
            print(f"Error saving call history: {e}")
            
    def load_call_history(self):
        """Load call history from file"""
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r') as f:
                    self.call_history = json.load(f)
                print(f"Loaded {len(self.call_history)} calls from history")
        except Exception as e:
            print(f"Error loading call history: {e}")
            self.call_history = []
    
    def cleanup_orphaned_calls(self):
        """Clean up calls that have been active too long (likely orphaned)"""
        with self.lock:
            current_time = datetime.now()
            orphaned_calls = []
            
            for call_id, call_data in self.active_calls.items():
                call_start = datetime.fromisoformat(call_data['start_time'])
                duration = (current_time - call_start).total_seconds()
                
                # Consider calls orphaned if active for more than 10 minutes without metrics
                if duration > 600 and len(call_data['quality_metrics']) == 0:
                    orphaned_calls.append(call_id)
                # Or if active for more than 30 minutes regardless
                elif duration > 1800:
                    orphaned_calls.append(call_id)
            
            for call_id in orphaned_calls:
                print(f"Cleaning up orphaned call: {call_id}")
                self.end_call(call_id)
    
    def start_cleanup_timer(self):
        """Start periodic cleanup of orphaned calls"""
        def cleanup_loop():
            import time
            while True:
                time.sleep(300)  # Check every 5 minutes
                try:
                    self.cleanup_orphaned_calls()
                except Exception as e:
                    print(f"Error in cleanup loop: {e}")
        
        cleanup_thread = threading.Thread(target=cleanup_loop, daemon=True)
        cleanup_thread.start()
