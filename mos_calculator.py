import math
import numpy as np

class MOSCalculator:
    """
    Calculate Mean Opinion Score (MOS) using E-Model algorithm
    for no-reference quality assessment
    """
    
    def __init__(self):
        # E-Model parameters
        self.Ro = 93.2  # Basic signal-to-noise ratio
        self.Is = 1.41  # Simultaneous impairment factor
        self.Id = 0     # Delay impairment factor (calculated)
        self.Ie_eff = 0 # Equipment impairment factor (calculated)
        self.A = 0      # Advantage factor
        
    def calculate_mos(self, packet_loss_rate=0, jitter=0, delay=0, codec='G.711'):
        """
        Calculate MOS score using E-Model algorithm
        
        Args:
            packet_loss_rate: Packet loss percentage (0-100)
            jitter: Jitter in milliseconds
            delay: One-way delay in milliseconds
            codec: Audio codec used
            
        Returns:
            MOS score (1.0 - 5.0)
        """
        try:
            # Calculate impairment factors
            Id = self._calculate_delay_impairment(delay)
            Ie_eff = self._calculate_equipment_impairment(packet_loss_rate, jitter, codec)
            
            # Calculate R-factor
            R = self.Ro - self.Is - Id - Ie_eff + self.A
            
            # Ensure R is within valid range
            R = max(0, min(100, R))
            
            # Convert R-factor to MOS
            mos = self._r_to_mos(R)
            
            return round(mos, 2)
            
        except Exception as e:
            print(f"Error calculating MOS: {e}")
            return 1.0  # Return minimum MOS on error
            
    def _calculate_delay_impairment(self, delay):
        """Calculate delay impairment factor Id"""
        if delay <= 100:
            return 0
        elif delay <= 200:
            return 0.024 * delay - 2.4
        else:
            return 0.11 * (delay - 177.3) + 2.4
            
    def _calculate_equipment_impairment(self, packet_loss_rate, jitter, codec):
        """Calculate equipment impairment factor Ie_eff"""
        # Base equipment impairment for different codecs
        codec_impairments = {
            'G.711': 0,      # PCMU/PCMA
            'G.729': 10,     # G.729
            'G.723.1': 15,   # G.723.1
            'GSM': 20,       # GSM
            'iLBC': 8        # iLBC
        }
        
        Ie = codec_impairments.get(codec, 0)
        
        # Packet loss impairment
        if packet_loss_rate > 0:
            # Burstiness factor (simplified)
            Bpl = 1  # Random packet loss assumption
            
            # Packet loss robustness factor (codec dependent)
            Ppl = 1 if codec == 'G.711' else 2
            
            # Calculate packet loss impairment
            loss_impairment = Ie + (95 - Ie) * (packet_loss_rate / (packet_loss_rate + Bpl))
            Ie = loss_impairment
            
        # Jitter impairment (simplified model)
        if jitter > 20:  # Jitter above 20ms causes noticeable impairment
            jitter_impairment = min(20, (jitter - 20) * 0.5)
            Ie += jitter_impairment
            
        return Ie
        
    def _r_to_mos(self, R):
        """Convert R-factor to MOS score"""
        if R < 0:
            return 1.0
        elif R > 100:
            return 4.5
        else:
            # ITU-T G.107 conversion formula
            if R < 6.5:
                return 1.0
            elif R < 50:
                return 1.0 + 0.035 * R + 7e-6 * R * (R - 60) * (100 - R)
            elif R < 93.2:
                return 1.0 + 0.035 * R + 7e-6 * R * (R - 60) * (100 - R)
            else:
                return 4.5
                
    def calculate_quality_category(self, mos_score):
        """Categorize quality based on MOS score"""
        if mos_score >= 4.0:
            return "Excellent"
        elif mos_score >= 3.5:
            return "Good"
        elif mos_score >= 3.0:
            return "Fair"
        elif mos_score >= 2.0:
            return "Poor"
        else:
            return "Bad"
            
    def get_quality_recommendations(self, packet_loss_rate, jitter, delay):
        """Get recommendations for improving quality"""
        recommendations = []
        
        if packet_loss_rate > 5:
            recommendations.append("High packet loss detected. Check network congestion and QoS settings.")
            
        if jitter > 50:
            recommendations.append("High jitter detected. Consider implementing jitter buffer or QoS prioritization.")
            
        if delay > 150:
            recommendations.append("High delay detected. Check network routing and consider geographic proximity.")
            
        if not recommendations:
            recommendations.append("Call quality metrics are within acceptable ranges.")
            
        return recommendations
        
    def calculate_detailed_metrics(self, packet_loss_rate, jitter, delay, codec='G.711'):
        """Calculate detailed quality metrics and analysis"""
        mos_score = self.calculate_mos(packet_loss_rate, jitter, delay, codec)
        quality_category = self.calculate_quality_category(mos_score)
        recommendations = self.get_quality_recommendations(packet_loss_rate, jitter, delay)
        
        # Calculate R-factor components for detailed analysis
        Id = self._calculate_delay_impairment(delay)
        Ie_eff = self._calculate_equipment_impairment(packet_loss_rate, jitter, codec)
        R = self.Ro - self.Is - Id - Ie_eff + self.A
        
        return {
            'mos_score': mos_score,
            'quality_category': quality_category,
            'recommendations': recommendations,
            'r_factor': max(0, min(100, R)),
            'impairment_factors': {
                'delay_impairment': Id,
                'equipment_impairment': Ie_eff,
                'simultaneous_impairment': self.Is
            },
            'network_metrics': {
                'packet_loss_rate': packet_loss_rate,
                'jitter': jitter,
                'delay': delay,
                'codec': codec
            }
        }
