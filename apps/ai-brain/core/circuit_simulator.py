import math
from pydantic import BaseModel
from typing import List, Optional

class CircuitComponent(BaseModel):
    id: str
    type: str # 'battery', 'resistor', 'led'
    nodes: List[str] # ["n1", "0"]
    value: Optional[float] = None # ex: 9 pour 9V, 330 pour 330 Ohms

class CircuitRequest(BaseModel):
    components: List[CircuitComponent]

class CircuitSimulator:
    def __init__(self):
        self.use_pyspice = False
        try:
            import os
            import sys
            # Astuce pour Windows : forcer PySpice à voir le dossier
            if sys.platform == "win32" and r"C:\Spice64\bin" not in os.environ["PATH"]:
                os.environ["PATH"] = r"C:\Spice64\bin" + os.pathsep + os.environ["PATH"]
                
            # On tente d'importer PySpice
            import PySpice.Logging.Logging as Logging
            from PySpice.Spice.Netlist import Circuit
            import PySpice.Unit as U    
            self.Circuit = Circuit
            self.use_pyspice = True
            print(" PySpice initialisé avec succès !")
        except ImportError:
            print(" PySpice non détecté ou ngspice manquant. Utilisation du simulateur mathématique de secours (Loi d'Ohm).")

    def simulate(self, request: CircuitRequest) -> dict:
        """
        Simule le circuit. Si PySpice est installé, il génère la vraie Netlist.
        Sinon, il utilise un algorithme de secours basé sur la loi d'Ohm pour le MVP.
        """
        if self.use_pyspice:
            return self._simulate_with_pyspice(request)
        else:
            return self._simulate_with_fallback(request)

    def _simulate_with_fallback(self, request: CircuitRequest) -> dict:
        """
        Simulateur de secours : Loi d'Ohm basique (V = R * I).
        Ceci permet au PFE de fonctionner même si ngspice plante sous Windows.
        """
        voltage = 0
        resistance = 0
        has_led = False

        for comp in request.components:
            if comp.type == 'battery':
                voltage += (comp.value or 9)
            elif comp.type == 'resistor':
                resistance += (comp.value or 0)
            elif comp.type == 'led':
                has_led = True

        if resistance == 0 and has_led and voltage > 3:
            return {"status": "success", "led_status": "EXPLODED", "current_mA": 9999.99, "raw_message": "Overcurrent detected (short circuit)"}
        
        if resistance == 0:
             return {"status": "success", "led_status": "OFF", "current_mA": 0, "message": "Circuit ouvert ou court-circuit total."}

        # Calcul du courant I = V / R (On simplifie la chute de tension de la LED)
        # Vérification du courant (La LED claque à 30mA, mais on met un seuil d'alerte pédagogique à 20mA)
        current_A = (voltage - 2.0) / resistance if has_led and voltage > 2.0 else voltage / resistance
        current_mA = max(0, current_A * 1000)
        
        status = "ON"
        if has_led and current_mA > 20:
            status = "EXPLODED"
        elif not has_led:
            status = "NONE"
            
        return {
            "status": "success",
            "current_mA": round(current_mA, 2),
            "voltage_V": round(voltage, 2),
            "led_status": status,
            "raw_message": "Overcurrent detected" if status == "EXPLODED" else "Normal operation"
        }

    def _simulate_with_pyspice(self, request: CircuitRequest) -> dict:
        """
        Véritable simulation Ngspice.
        """
        circuit = self.Circuit('TechKids Circuit')
        
        try:
            for comp in request.components:
                n1 = comp.nodes[0]
                n2 = comp.nodes[1] if len(comp.nodes) > 1 else '0'
                
                if comp.type == 'battery':
                    circuit.V(comp.id, n1, n2, comp.value)
                elif comp.type == 'resistor':
                    circuit.R(comp.id, n1, n2, comp.value)
                elif comp.type == 'led':
                    # Modèle standard de LED dans SPICE
                    circuit.model('MyLED', 'D', IS=1e-19, N=1.6, RS=1.5)
                    circuit.Diode(comp.id, n1, n2, model='MyLED')

            simulator = circuit.simulator(temperature=25, nominal_temperature=25)
            analysis = simulator.operating_point()
            
            # TODO: Extraire le vrai courant de l'analyse ngspice
            # Ceci est un pseudo-code car l'API PySpice dépend du noeud exact
            return {"status": "success", "message": "Simulation PySpice réussie !"}
            
        except Exception as e:
            return {"status": "error", "message": f"Erreur de simulation SPICE: {str(e)}"}
