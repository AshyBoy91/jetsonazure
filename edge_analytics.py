"""
Edge Analytics Module for Azure IoT Edge
Performs local data processing and analysis on Jetson Nano
"""

import asyncio
import logging
import statistics
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import json


class EdgeAnalytics:
    """Local analytics processing for IoT Edge"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.analytics_history = []
        self.max_history_size = 50
        
    async def get_comprehensive_analytics(self, telemetry_buffer: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate comprehensive analytics from telemetry buffer"""
        if not telemetry_buffer:
            return {"error": "No telemetry data available"}
        
        try:
            analytics = {
                "timestamp": datetime.utcnow().isoformat(),
                "data_points": len(telemetry_buffer),
                "system_summary": await self._analyze_system_metrics(telemetry_buffer),
                "health_score": await self._calculate_health_score(telemetry_buffer)
            }
            
            # Add to history
            self.analytics_history.append(analytics)
            if len(self.analytics_history) > self.max_history_size:
                self.analytics_history.pop(0)
            
            return analytics
            
        except Exception as e:
            self.logger.error(f"Error generating comprehensive analytics: {e}")
            return {"error": f"Analytics generation failed: {str(e)}"}
    
    async def get_quick_insights(self, telemetry_buffer: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate quick insights for real-time processing"""
        if not telemetry_buffer:
            return {}
        
        try:
            recent_data = telemetry_buffer[-10:]  # Last 10 data points
            
            insights = {
                "avg_cpu": self._safe_average([d.get('cpu_percent', 0) for d in recent_data]),
                "avg_memory": self._safe_average([d.get('memory_percent', 0) for d in recent_data]),
                "avg_disk": self._safe_average([d.get('disk_percent', 0) for d in recent_data]),
                "max_temperature": self._get_max_temperature(recent_data),
                "trend": self._get_simple_trend(recent_data)
            }
            
            return insights
            
        except Exception as e:
            self.logger.error(f"Error generating quick insights: {e}")
            return {}
    
    async def generate_system_report(self, telemetry_buffer: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate detailed system report"""
        try:
            report = {
                "report_type": "system_health",
                "timestamp": datetime.utcnow().isoformat(),
                "summary": await self._generate_system_summary(telemetry_buffer),
                "detailed_metrics": await self._generate_detailed_metrics(telemetry_buffer),
                "performance_analysis": await self._analyze_performance_patterns(telemetry_buffer),
                "health_score": await self._calculate_health_score(telemetry_buffer)
            }
            
            return report
            
        except Exception as e:
            self.logger.error(f"Error generating system report: {e}")
            return {"error": f"Report generation failed: {str(e)}"}
    
    async def generate_periodic_report(self, telemetry_buffer: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate periodic analytics report"""
        try:
            report = {
                "report_type": "periodic_analytics",
                "timestamp": datetime.utcnow().isoformat(),
                "period_summary": await self._analyze_period_data(telemetry_buffer),
                "anomalies": await self._detect_anomalies(telemetry_buffer),
                "efficiency_metrics": await self._calculate_efficiency_metrics(telemetry_buffer)
            }
            
            return report
            
        except Exception as e:
            self.logger.error(f"Error generating periodic report: {e}")
            return {"error": f"Periodic report generation failed: {str(e)}"}
    
    async def analyze_recent_data(self, telemetry_buffer: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze recent telemetry data"""
        try:
            recent_data = telemetry_buffer[-20:] if len(telemetry_buffer) > 20 else telemetry_buffer
            
            analysis = {
                "data_points": len(recent_data),
                "time_span_minutes": self._calculate_time_span(recent_data),
                "resource_utilization": await self._analyze_resource_utilization(recent_data),
                "stability_analysis": await self._analyze_system_stability(recent_data),
                "performance_score": await self._calculate_performance_score(recent_data)
            }
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"Error analyzing recent data: {e}")
            return {"error": f"Recent data analysis failed: {str(e)}"}
    
    def _get_time_range(self, telemetry_buffer: List[Dict[str, Any]]) -> Dict[str, str]:
        """Get time range of telemetry data"""
        if not telemetry_buffer:
            return {}
        
        timestamps = [d.get('timestamp') for d in telemetry_buffer if d.get('timestamp')]
        if not timestamps:
            return {}
        
        return {
            "start": min(timestamps),
            "end": max(timestamps),
            "duration_minutes": self._calculate_time_span(telemetry_buffer)
        }
    
    async def _analyze_system_metrics(self, telemetry_buffer: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze system metrics from telemetry data"""
        cpu_values = [d.get('cpu_percent', 0) for d in telemetry_buffer]
        memory_values = [d.get('memory_percent', 0) for d in telemetry_buffer]
        
        return {
            "cpu": {
                "average": self._safe_average(cpu_values),
                "max": max(cpu_values) if cpu_values else 0,
                "current": cpu_values[-1] if cpu_values else 0
            },
            "memory": {
                "average": self._safe_average(memory_values),
                "max": max(memory_values) if memory_values else 0,
                "current": memory_values[-1] if memory_values else 0
            }
        }
    
    async def _calculate_health_score(self, telemetry_buffer: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate overall system health score"""
        if not telemetry_buffer:
            return {"score": 0, "status": "unknown"}
        
        recent_data = telemetry_buffer[-10:]
        
        # Score components (0-100 each)
        cpu_score = max(0, 100 - self._safe_average([d.get('cpu_percent', 0) for d in recent_data]))
        memory_score = max(0, 100 - self._safe_average([d.get('memory_percent', 0) for d in recent_data]))
        
        # Overall score
        overall_score = (cpu_score + memory_score) / 2
        
        # Determine status
        if overall_score >= 80:
            status = "excellent"
        elif overall_score >= 60:
            status = "good"
        else:
            status = "needs_attention"
        
        return {
            "score": round(overall_score, 2),
            "status": status
        }
    
    async def _generate_system_summary(self, telemetry_buffer: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate system summary"""
        if not telemetry_buffer:
            return {}
        
        latest = telemetry_buffer[-1]
        
        return {
            "device_id": latest.get('device_id', 'unknown'),
            "timestamp": latest.get('timestamp'),
            "uptime_seconds": latest.get('uptime_seconds', 0),
            "is_jetson": latest.get('is_jetson', False),
            "connectivity_status": latest.get('network', {}).get('connectivity', {}),
            "edge_processing_active": latest.get('edge_processed', False)
        }
    
    async def _generate_detailed_metrics(self, telemetry_buffer: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate detailed metrics analysis"""
        return await self._analyze_system_metrics(telemetry_buffer)
    
    async def _analyze_performance_patterns(self, telemetry_buffer: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze performance patterns"""
        return await self._analyze_system_metrics(telemetry_buffer)
    
    async def _analyze_period_data(self, telemetry_buffer: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze data for periodic reporting"""
        return {
            "total_data_points": len(telemetry_buffer),
            "time_range": self._get_time_range(telemetry_buffer),
            "system_metrics": await self._analyze_system_metrics(telemetry_buffer)
        }
    
    async def _detect_anomalies(self, telemetry_buffer: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Detect anomalies in telemetry data"""
        anomalies = []
        
        if len(telemetry_buffer) < 10:
            return anomalies
        
        # Simple anomaly detection based on standard deviation
        cpu_values = [d.get('cpu_percent', 0) for d in telemetry_buffer]
        if len(cpu_values) > 5:
            cpu_mean = statistics.mean(cpu_values)
            cpu_stdev = statistics.stdev(cpu_values) if len(cpu_values) > 1 else 0
            
            for i, value in enumerate(cpu_values):
                if cpu_stdev > 0 and abs(value - cpu_mean) > 2 * cpu_stdev:
                    anomalies.append({
                        "type": "cpu_anomaly",
                        "timestamp": telemetry_buffer[i].get('timestamp'),
                        "value": value,
                        "expected_range": f"{cpu_mean - 2*cpu_stdev:.1f} - {cpu_mean + 2*cpu_stdev:.1f}"
                    })
        
        return anomalies
    
    async def _calculate_efficiency_metrics(self, telemetry_buffer: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate system efficiency metrics"""
        return {
            "data_collection_efficiency": len(telemetry_buffer),
            "processing_efficiency": "active" if telemetry_buffer else "inactive",
            "average_response_time": "real-time"  # Placeholder
        }
    
    async def _analyze_resource_utilization(self, recent_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze resource utilization patterns"""
        return await self._analyze_system_metrics(recent_data)
    
    async def _analyze_system_stability(self, recent_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze system stability"""
        if len(recent_data) < 3:
            return {"status": "insufficient_data"}
        
        cpu_values = [d.get('cpu_percent', 0) for d in recent_data]
        cpu_variance = statistics.variance(cpu_values) if len(cpu_values) > 1 else 0
        
        stability_score = max(0, 100 - cpu_variance)
        
        return {
            "stability_score": round(stability_score, 2),
            "status": "stable" if stability_score > 80 else "unstable",
            "cpu_variance": round(cpu_variance, 2)
        }
    
    async def _calculate_performance_score(self, recent_data: List[Dict[str, Any]]) -> float:
        """Calculate overall performance score"""
        health_data = await self._calculate_health_score(recent_data)
        return health_data.get("score", 0)
    
    def _safe_average(self, values: List[float]) -> float:
        """Safely calculate average of values"""
        clean_values = [v for v in values if v is not None and isinstance(v, (int, float))]
        return statistics.mean(clean_values) if clean_values else 0
    
    def _get_max_temperature(self, data_points: List[Dict[str, Any]]) -> float:
        """Get maximum temperature from data points"""
        max_temp = 0
        for data in data_points:
            temps = data.get('temperatures', {})
            if temps:
                current_max = max(temps.values()) if temps.values() else 0
                max_temp = max(max_temp, current_max)
        return max_temp
    
    def _get_simple_trend(self, recent_data: List[Dict[str, Any]]) -> str:
        """Get simple trend analysis"""
        if len(recent_data) < 3:
            return "insufficient_data"
        
        cpu_values = [d.get('cpu_percent', 0) for d in recent_data[-3:]]
        
        if len(cpu_values) == 3:
            if cpu_values[2] > cpu_values[1] > cpu_values[0]:
                return "increasing"
            elif cpu_values[2] < cpu_values[1] < cpu_values[0]:
                return "decreasing"
            else:
                return "stable"
        
        return "stable"
    
    def _calculate_time_span(self, data_points: List[Dict[str, Any]]) -> float:
        """Calculate time span of data points in minutes"""
        if len(data_points) < 2:
            return 0
        
        timestamps = [d.get('timestamp') for d in data_points if d.get('timestamp')]
        if len(timestamps) < 2:
            return 0
        
        try:
            start_time = datetime.fromisoformat(timestamps[0].replace('Z', '+00:00'))
            end_time = datetime.fromisoformat(timestamps[-1].replace('Z', '+00:00'))
            return (end_time - start_time).total_seconds() / 60
        except Exception:
            return 0 