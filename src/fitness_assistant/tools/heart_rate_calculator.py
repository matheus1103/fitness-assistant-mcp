"""
Calculadora de zonas de frequência cardíaca e métricas relacionadas
"""

from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import math


class ZoneMethod(Enum):
    """Métodos para cálculo de zonas de FC"""
    KARVONEN = "karvonen"  # Método Karvonen (mais preciso)
    MAX_HR_PERCENTAGE = "max_hr_percentage"  # Percentual da FC máxima
    MAFFETONE = "maffetone"  # Método MAF (aeróbico)


@dataclass
class HeartRateZone:
    """Representa uma zona de frequência cardíaca"""
    zone_number: int
    name: str
    min_bpm: int
    max_bpm: int
    percentage_range: Tuple[int, int]
    description: str
    benefits: List[str]
    duration_recommendations: str
    perceived_exertion: Tuple[int, int]  # Escala 1-10


@dataclass
class HeartRateAnalysis:
    """Análise completa de frequência cardíaca"""
    user_age: int
    resting_hr: int
    max_hr_estimated: int
    hr_reserve: int
    zones: List[HeartRateZone]
    method_used: str
    recommendations: List[str]
    safety_notes: List[str]


class HeartRateCalculator:
    """Calculadora principal de zonas de frequência cardíaca"""
    
    def __init__(self):
        """Inicializa a calculadora com configurações padrão"""
        
        # Definições das zonas (método Karvonen)
        self.zone_definitions = {
            1: {
                "name": "Recuperação Ativa",
                "percentage": (50, 60),
                "description": "Zona de recuperação e queima de gordura",
                "benefits": [
                    "Acelera recuperação muscular",
                    "Melhora circulação sanguínea",
                    "Queima gordura como combustível",
                    "Reduz stress"
                ],
                "duration": "20-60 minutos",
                "perceived_exertion": (3, 4)
            },
            2: {
                "name": "Aeróbica Base",
                "percentage": (60, 70),
                "description": "Zona aeróbica básica para resistência",
                "benefits": [
                    "Desenvolve base aeróbica",
                    "Melhora eficiência cardíaca",
                    "Aumenta densidade mitocondrial",
                    "Queima gordura eficientemente"
                ],
                "duration": "30-90 minutos",
                "perceived_exertion": (4, 6)
            },
            3: {
                "name": "Aeróbica Intensa",
                "percentage": (70, 80),
                "description": "Zona de tempo/ritmo aeróbico",
                "benefits": [
                    "Melhora VO2 máximo",
                    "Aumenta eficiência aeróbica",
                    "Desenvolve resistência",
                    "Melhora clearance de lactato"
                ],
                "duration": "20-60 minutos",
                "perceived_exertion": (6, 7)
            },
            4: {
                "name": "Limiar Anaeróbico",
                "percentage": (80, 90),
                "description": "Zona do limiar de lactato",
                "benefits": [
                    "Aumenta limiar anaeróbico",
                    "Melhora tolerância ao lactato",
                    "Desenvolve potência aeróbica",
                    "Aumenta velocidade de corrida"
                ],
                "duration": "10-40 minutos",
                "perceived_exertion": (7, 9)
            },
            5: {
                "name": "VO2 Máximo",
                "percentage": (90, 100),
                "description": "Zona de potência máxima",
                "benefits": [
                    "Maximiza VO2 máximo",
                    "Desenvolve potência anaeróbica",
                    "Melhora capacidade neuromuscular",
                    "Aumenta velocidade máxima"
                ],
                "duration": "2-15 minutos (intervalos)",
                "perceived_exertion": (9, 10)
            }
        }
    
    def calculate_max_heart_rate(self, age: int, method: str = "tanaka") -> int:
        """
        Calcula frequência cardíaca máxima estimada
        
        Args:
            age: Idade em anos
            method: Método de cálculo ('tanaka', 'fox', 'nes')
            
        Returns:
            FC máxima estimada em bpm
        """
        
        if method == "tanaka":
            # Fórmula Tanaka (mais moderna e precisa)
            return round(208 - (0.7 * age))
        
        elif method == "fox":
            # Fórmula clássica Fox
            return round(220 - age)
        
        elif method == "nes":
            # Fórmula Nes (para pessoas ativas)
            return round(211 - (0.64 * age))
        
        else:
            # Default para Tanaka
            return round(208 - (0.7 * age))
    
    def calculate_heart_rate_reserve(self, max_hr: int, resting_hr: int) -> int:
        """
        Calcula reserva de frequência cardíaca (método Karvonen)
        
        Args:
            max_hr: FC máxima
            resting_hr: FC de repouso
            
        Returns:
            Reserva de FC em bpm
        """
        return max_hr - resting_hr
    
    def calculate_target_heart_rate(self, hr_reserve: int, resting_hr: int, 
                                  intensity_min: int, intensity_max: int) -> Tuple[int, int]:
        """
        Calcula FC alvo usando método Karvonen
        
        Args:
            hr_reserve: Reserva de FC
            resting_hr: FC de repouso
            intensity_min: Intensidade mínima (%)
            intensity_max: Intensidade máxima (%)
            
        Returns:
            Tupla (FC_min, FC_max) em bpm
        """
        
        fc_min = round(resting_hr + (hr_reserve * intensity_min / 100))
        fc_max = round(resting_hr + (hr_reserve * intensity_max / 100))
        
        return (fc_min, fc_max)
    
    def calculate_zones(self, age: int, resting_hr: int, 
                       method: ZoneMethod = ZoneMethod.KARVONEN) -> HeartRateAnalysis:
        """
        Calcula todas as zonas de frequência cardíaca
        
        Args:
            age: Idade em anos
            resting_hr: FC de repouso em bpm
            method: Método de cálculo das zonas
            
        Returns:
            HeartRateAnalysis com todas as informações
        """
        
        # Validações básicas
        if not 13 <= age <= 100:
            raise ValueError("Idade deve estar entre 13 e 100 anos")
        
        if not 30 <= resting_hr <= 120:
            raise ValueError("FC de repouso deve estar entre 30 e 120 bpm")
        
        # Cálculos básicos
        max_hr = self.calculate_max_heart_rate(age)
        hr_reserve = self.calculate_heart_rate_reserve(max_hr, resting_hr)
        
        # Calcula zonas
        zones = []
        
        for zone_num in range(1, 6):
            zone_def = self.zone_definitions[zone_num]
            intensity_min, intensity_max = zone_def["percentage"]
            
            if method == ZoneMethod.KARVONEN:
                # Método Karvonen (mais preciso)
                fc_min, fc_max = self.calculate_target_heart_rate(
                    hr_reserve, resting_hr, intensity_min, intensity_max
                )
            
            elif method == ZoneMethod.MAX_HR_PERCENTAGE:
                # Percentual da FC máxima
                fc_min = round(max_hr * intensity_min / 100)
                fc_max = round(max_hr * intensity_max / 100)
            
            else:
                # Default para Karvonen
                fc_min, fc_max = self.calculate_target_heart_rate(
                    hr_reserve, resting_hr, intensity_min, intensity_max
                )
            
            zone = HeartRateZone(
                zone_number=zone_num,
                name=zone_def["name"],
                min_bpm=fc_min,
                max_bpm=fc_max,
                percentage_range=zone_def["percentage"],
                description=zone_def["description"],
                benefits=zone_def["benefits"],
                duration_recommendations=zone_def["duration"],
                perceived_exertion=zone_def["perceived_exertion"]
            )
            
            zones.append(zone)
        
        # Gera recomendações
        recommendations = self._generate_recommendations(age, resting_hr, zones)
        safety_notes = self._generate_safety_notes(age, resting_hr)
        
        return HeartRateAnalysis(
            user_age=age,
            resting_hr=resting_hr,
            max_hr_estimated=max_hr,
            hr_reserve=hr_reserve,
            zones=zones,
            method_used=method.value,
            recommendations=recommendations,
            safety_notes=safety_notes
        )
    
    def determine_current_zone(self, current_hr: int, zones: List[HeartRateZone]) -> Optional[HeartRateZone]:
        """
        Determina em qual zona está a FC atual
        
        Args:
            current_hr: FC atual em bpm
            zones: Lista de zonas calculadas
            
        Returns:
            Zona atual ou None se fora das zonas
        """
        
        for zone in zones:
            if zone.min_bpm <= current_hr <= zone.max_bpm:
                return zone
        
        return None
    
    def get_zone_recommendations(self, zone: HeartRateZone, 
                               current_duration: int = 0) -> Dict[str, Any]:
        """
        Gera recomendações específicas para uma zona
        
        Args:
            zone: Zona de FC
            current_duration: Duração atual do exercício em minutos
            
        Returns:
            Dict com recomendações específicas
        """
        
        recommendations = {
            "zone_info": {
                "name": zone.name,
                "description": zone.description,
                "intensity": f"{zone.percentage_range[0]}-{zone.percentage_range[1]}%",
                "heart_rate_range": f"{zone.min_bpm}-{zone.max_bpm} bpm"
            },
            "benefits": zone.benefits,
            "duration_guide": zone.duration_recommendations,
            "perceived_exertion": f"{zone.perceived_exertion[0]}-{zone.perceived_exertion[1]}/10",
            "exercise_suggestions": self._get_exercise_suggestions(zone),
            "duration_feedback": self._get_duration_feedback(zone, current_duration)
        }
        
        return recommendations
    
    def calculate_calories_burned(self, age: int, weight_kg: float, 
                                heart_rate: int, duration_minutes: int,
                                gender: str = "M") -> int:
        """
        Estima calorias queimadas baseado na FC
        
        Args:
            age: Idade em anos
            weight_kg: Peso em kg
            heart_rate: FC média durante exercício
            duration_minutes: Duração em minutos
            gender: Gênero ('M' ou 'F')
            
        Returns:
            Calorias estimadas
        """
        
        # Fórmulas baseadas em estudos científicos
        if gender.upper() == "M":
            # Homens
            calories_per_minute = (
                (-55.0969 + (0.6309 * heart_rate) + (0.1988 * weight_kg) + (0.2017 * age)) / 4.184
            )
        else:
            # Mulheres
            calories_per_minute = (
                (-20.4022 + (0.4472 * heart_rate) - (0.1263 * weight_kg) + (0.074 * age)) / 4.184
            )
        
        # Garante valor mínimo razoável
        calories_per_minute = max(calories_per_minute, 3.0)
        
        total_calories = round(calories_per_minute * duration_minutes)
        
        return max(total_calories, 1)  # Mínimo de 1 caloria
    
    def _generate_recommendations(self, age: int, resting_hr: int, 
                                zones: List[HeartRateZone]) -> List[str]:
        """Gera recomendações personalizadas"""
        
        recommendations = []
        
        # Baseado na FC de repouso
        if resting_hr < 60:
            recommendations.append("FC de repouso excelente! Indica boa condição cardiovascular")
        elif resting_hr > 80:
            recommendations.append("FC de repouso elevada. Considere trabalhar na zona 1-2 inicialmente")
        
        # Baseado na idade
        if age < 30:
            recommendations.append("Pode treinar em todas as zonas com boa recuperação")
        elif age > 50:
            recommendations.append("Foque nas zonas 1-3, com aquecimento prolongado")
        elif age > 65:
            recommendations.append("Priorize zonas 1-2, com supervisão médica para intensidades altas")
        
        # Recomendações gerais
        recommendations.extend([
            "Passe 80% do tempo nas zonas 1-2 para desenvolver base aeróbica",
            "Use zona 3 para treinos de tempo/ritmo 1-2x por semana",
            "Limite zona 4-5 a intervalos específicos com boa recuperação",
            "Monitore FC de repouso para avaliar recuperação"
        ])
        
        return recommendations
    
    def _generate_safety_notes(self, age: int, resting_hr: int) -> List[str]:
        """Gera notas de segurança"""
        
        safety_notes = [
            "Consulte médico antes de iniciar programa de exercícios intensos",
            "Pare imediatamente se sentir dor no peito, tontura ou náusea",
            "Hidrate-se adequadamente antes, durante e após exercícios",
            "Faça aquecimento gradual antes de atingir zonas altas"
        ]
        
        # Notas específicas por idade
        if age > 40:
            safety_notes.append("Considere teste ergométrico para exercícios de alta intensidade")
        
        if age > 60:
            safety_notes.append("Evite mudanças bruscas de intensidade")
        
        # Notas por FC de repouso
        if resting_hr > 100:
            safety_notes.append("FC de repouso muito alta - consulte médico antes de exercitar")
        
        return safety_notes
    
    def _get_exercise_suggestions(self, zone: HeartRateZone) -> List[str]:
        """Sugere exercícios apropriados para a zona"""
        
        suggestions = {
            1: [
                "Caminhada leve",
                "Yoga suave",
                "Natação tranquila",
                "Bicicleta em ritmo confortável"
            ],
            2: [
                "Caminhada acelerada",
                "Corrida leve",
                "Ciclismo moderado",
                "Natação contínua",
                "Elíptico em ritmo steady"
            ],
            3: [
                "Corrida em ritmo de prova",
                "Ciclismo em grupo",
                "Natação com intervalo moderado",
                "Spinning moderado"
            ],
            4: [
                "Intervalos de corrida",
                "Subidas/tiros de velocidade",
                "HIIT moderado",
                "Spinning intenso"
            ],
            5: [
                "Sprints curtos",
                "Intervalos máximos",
                "Subidas máximas",
                "HIIT máximo"
            ]
        }
        
        return suggestions.get(zone.zone_number, ["Exercícios diversos"])
    
    def _get_duration_feedback(self, zone: HeartRateZone, current_duration: int) -> str:
        """Fornece feedback sobre duração atual"""
        
        if current_duration == 0:
            return f"Duração recomendada: {zone.duration_recommendations}"
        
        # Extrai duração máxima recomendada (aproximada)
        max_duration_map = {1: 60, 2: 90, 3: 60, 4: 40, 5: 15}
        max_recommended = max_duration_map.get(zone.zone_number, 30)
        
        if current_duration > max_recommended:
            return f"Duração atual ({current_duration}min) acima do recomendado. Considere reduzir intensidade"
        elif current_duration < 5 and zone.zone_number <= 3:
            return "Duração muito curta para benefícios aeróbicos. Continue por mais tempo"
        else:
            return f"Duração adequada para esta zona ({current_duration}min)"


# Função de conveniência para uso direto
def calculate_heart_rate_zones(age: int, resting_hr: int) -> Dict[str, Any]:
    """
    Função de conveniência para calcular zonas de FC
    
    Args:
        age: Idade em anos
        resting_hr: FC de repouso em bpm
        
    Returns:
        Dict com análise completa formatada
    """
    
    calculator = HeartRateCalculator()
    analysis = calculator.calculate_zones(age, resting_hr)
    
    # Formata resultado para retorno
    result = {
        "user_info": {
            "age": analysis.user_age,
            "resting_heart_rate": analysis.resting_hr,
            "max_heart_rate_estimated": analysis.max_hr_estimated,
            "heart_rate_reserve": analysis.hr_reserve
        },
        "zones": [],
        "method_used": analysis.method_used,
        "recommendations": analysis.recommendations,
        "safety_notes": analysis.safety_notes
    }
    
    for zone in analysis.zones:
        zone_dict = {
            "zone": zone.zone_number,
            "name": zone.name,
            "heart_rate_range": f"{zone.min_bpm}-{zone.max_bpm} bpm",
            "intensity_percentage": f"{zone.percentage_range[0]}-{zone.percentage_range[1]}%",
            "description": zone.description,
            "benefits": zone.benefits,
            "duration": zone.duration_recommendations,
            "perceived_exertion": f"{zone.perceived_exertion[0]}-{zone.perceived_exertion[1]}/10"
        }
        result["zones"].append(zone_dict)
    
    return result


# Para compatibilidade com código existente
def get_heart_rate_zones(age: int, resting_hr: int) -> Dict[str, Any]:
    """Alias para manter compatibilidade"""
    return calculate_heart_rate_zones(age, resting_hr)


if __name__ == "__main__":
    # Exemplo de uso
    calculator = HeartRateCalculator()
    
    # Teste com usuário exemplo
    analysis = calculator.calculate_zones(age=28, resting_hr=65)
    
    print("ANÁLISE DE ZONAS DE FC")
    print("=" * 40)
    print(f"Idade: {analysis.user_age} anos")
    print(f"FC Repouso: {analysis.resting_hr} bpm")
    print(f"FC Máxima: {analysis.max_hr_estimated} bpm")
    print(f"Reserva FC: {analysis.hr_reserve} bpm")
    print()
    
    for zone in analysis.zones:
        print(f"ZONA {zone.zone_number}: {zone.name}")
        print(f"  FC: {zone.min_bpm}-{zone.max_bpm} bpm")
        print(f"  Intensidade: {zone.percentage_range[0]}-{zone.percentage_range[1]}%")
        print(f"  Duração: {zone.duration_recommendations}")
        print(f"  Benefícios: {', '.join(zone.benefits[:2])}")
        print()
    
    print("RECOMENDAÇÕES:")
    for rec in analysis.recommendations[:3]:
        print(f"  • {rec}")