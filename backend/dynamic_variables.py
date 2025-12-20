"""
Module pour gérer les variables dynamiques dans les prompts ElevenLabs.

Les variables dynamiques sont injectées à chaque appel et permettent d'avoir
des données en temps réel sans avoir à resynchroniser l'agent.

Cas d'usage :
- Disponibilités en temps réel (tables, chambres, créneaux)
- Stock de produits
- Météo, événements du jour
- Nom du client (si identifié depuis le numéro)
- Promotions en cours
"""

import os
import requests
from typing import Dict, Any, Optional, Callable
from datetime import datetime
from loguru import logger
from dotenv import load_dotenv

load_dotenv()

ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
ELEVENLABS_AGENT_ID = os.getenv("ELEVENLABS_AGENT_ID")


# ========== FONCTIONS DE RÉCUPÉRATION DE DONNÉES ==========

def get_current_datetime() -> Dict[str, str]:
    """Retourne date et heure actuelles"""
    now = datetime.now()
    return {
        "date_actuelle": now.strftime("%d/%m/%Y"),
        "heure_actuelle": now.strftime("%H:%M"),
        "jour_semaine": now.strftime("%A")
    }


def get_client_info(phone_number: str) -> Dict[str, str]:
    """
    Récupère les infos du client depuis la base de données.
    Peut être appelé au début de chaque appel.
    """
    # TODO: Intégrer avec Supabase pour récupérer les infos client
    # Pour l'instant, retour exemple
    return {
        "nom_client": "Client",
        "historique_achats": "Aucun",
        "statut_fidelite": "Standard"
    }


def get_realtime_availability() -> Dict[str, Any]:
    """
    Récupère les disponibilités en temps réel.
    À adapter selon votre métier (restaurant, hôtel, service, etc.)
    """
    # TODO: Intégrer avec votre système de réservation
    # Exemple pour un restaurant
    return {
        "tables_disponibles_ce_soir": "3 tables à 20h, 5 tables à 21h30",
        "temps_attente_estime": "15 minutes",
        "plat_du_jour": "Homard breton aux herbes"
    }


def get_business_status() -> Dict[str, str]:
    """Vérifie si l'entreprise est actuellement ouverte"""
    now = datetime.now()
    hour = now.hour
    day = now.strftime("%A").lower()
    
    # TODO: Récupérer depuis le Company Profile
    # Pour l'instant, logique simple
    if day in ["saturday", "sunday"]:
        if 10 <= hour < 18:
            return {
                "statut_ouverture": "ouvert",
                "fermeture_dans": f"{18 - hour} heures"
            }
    else:
        if 9 <= hour < 18:
            return {
                "statut_ouverture": "ouvert",
                "fermeture_dans": f"{18 - hour} heures"
            }
    
    return {
        "statut_ouverture": "fermé",
        "ouverture_demain": "9h00"
    }


def get_promotions() -> Dict[str, str]:
    """Récupère les promotions en cours"""
    # TODO: Intégrer avec votre système de promotions
    return {
        "promotion_en_cours": "20% sur tous les desserts cette semaine",
        "code_promo": "DESSERT20"
    }


# ========== CONFIGURATION DES VARIABLES ==========

# Dictionnaire des variables disponibles et leurs fonctions de récupération
AVAILABLE_VARIABLES: Dict[str, Callable] = {
    "datetime": get_current_datetime,
    "availability": get_realtime_availability,
    "business_status": get_business_status,
    "promotions": get_promotions,
}


class DynamicVariablesManager:
    """Gestionnaire des variables dynamiques pour ElevenLabs"""
    
    def __init__(self, api_key: str = ELEVENLABS_API_KEY, agent_id: str = ELEVENLABS_AGENT_ID):
        self.api_key = api_key
        self.agent_id = agent_id
        self.base_url = "https://api.elevenlabs.io/v1"
        self.headers = {
            "xi-api-key": self.api_key,
            "Content-Type": "application/json"
        }
    
    def configure_dynamic_variables(self, variables_config: Dict[str, str]) -> bool:
        """
        Configure les variables dynamiques dans le prompt de l'agent.
        
        Les variables dans le prompt sont définies avec {{variable_name}}.
        ElevenLabs les remplacera par les valeurs fournies lors de chaque appel.
        
        Args:
            variables_config: Dict des variables à configurer
                Exemple:
                {
                    "disponibilites": "Tables disponibles en temps réel",
                    "nom_client": "Nom du client identifié",
                    "plat_du_jour": "Plat du jour actuel"
                }
        
        Returns:
            bool: True si succès
        """
        url = f"{self.base_url}/convai/agents/{self.agent_id}"
        
        # Récupérer la config actuelle
        response = requests.get(url, headers=self.headers)
        if response.status_code != 200:
            logger.error(f"❌ Impossible de récupérer la config: {response.status_code}")
            return False
        
        current_config = response.json()
        current_prompt = current_config.get("conversation_config", {}).get("agent", {}).get("prompt", {}).get("prompt", "")
        
        # Ajouter les variables au prompt
        variables_section = self._build_variables_section(variables_config)
        
        # Si le prompt contient déjà une section variables, la remplacer
        if "## VARIABLES DYNAMIQUES" in current_prompt:
            parts = current_prompt.split("## VARIABLES DYNAMIQUES")
            # Garder la partie avant, ajouter la nouvelle section
            new_prompt = parts[0].strip() + "\n\n" + variables_section
        else:
            # Ajouter la section à la fin
            new_prompt = current_prompt.strip() + "\n\n" + variables_section
        
        # Mettre à jour l'agent
        payload = {
            "conversation_config": {
                "agent": {
                    "prompt": {
                        "prompt": new_prompt
                    }
                }
            }
        }
        
        try:
            response = requests.patch(url, headers=self.headers, json=payload)
            if response.status_code == 200:
                logger.success(f"✅ Variables dynamiques configurées : {', '.join(variables_config.keys())}")
                return True
            else:
                logger.error(f"❌ Erreur {response.status_code}: {response.text}")
                return False
        except Exception as e:
            logger.error(f"❌ Erreur lors de la mise à jour: {e}")
            return False
    
    def _build_variables_section(self, variables_config: Dict[str, str]) -> str:
        """Construit la section des variables dans le prompt"""
        section = "## VARIABLES DYNAMIQUES\n\n"
        section += "Les informations suivantes sont mises à jour en temps réel pour chaque appel :\n\n"
        
        for var_name, description in variables_config.items():
            section += f"- **{{{{{var_name}}}}}** : {description}\n"
        
        section += "\n💡 Utilise ces variables pour donner des réponses ultra-précises et à jour."
        
        return section
    
    def get_variables_for_call(
        self, 
        caller_number: Optional[str] = None,
        enabled_variables: Optional[list] = None
    ) -> Dict[str, Any]:
        """
        Récupère les valeurs actuelles des variables pour un appel.
        
        Cette fonction serait appelée au début de chaque appel pour
        obtenir les données fraîches.
        
        Args:
            caller_number: Numéro du caller pour personnalisation
            enabled_variables: Liste des variables à récupérer (None = toutes)
        
        Returns:
            Dict contenant toutes les variables et leurs valeurs
        """
        variables = {}
        
        # Si pas de liste spécifiée, prendre toutes les variables
        if enabled_variables is None:
            enabled_variables = list(AVAILABLE_VARIABLES.keys())
        
        # Récupérer chaque variable
        for var_name in enabled_variables:
            if var_name in AVAILABLE_VARIABLES:
                try:
                    data = AVAILABLE_VARIABLES[var_name]()
                    variables.update(data)
                    logger.debug(f"✅ Variable '{var_name}' récupérée")
                except Exception as e:
                    logger.error(f"❌ Erreur récupération '{var_name}': {e}")
        
        # Ajouter les infos client si numéro fourni
        if caller_number:
            try:
                client_info = get_client_info(caller_number)
                variables.update(client_info)
            except Exception as e:
                logger.error(f"❌ Erreur infos client: {e}")
        
        logger.info(f"📊 Variables pour l'appel : {list(variables.keys())}")
        return variables
    
    def inject_variables_to_conversation(
        self, 
        conversation_id: str, 
        variables: Dict[str, Any]
    ) -> bool:
        """
        Injecte les variables dans une conversation en cours.
        
        Note: Cette fonctionnalité dépend de l'API ElevenLabs.
        À vérifier dans leur documentation si l'injection en cours
        de conversation est supportée.
        
        Args:
            conversation_id: ID de la conversation
            variables: Variables à injecter
        """
        # TODO: À implémenter selon la doc ElevenLabs
        logger.warning("⚠️  Injection de variables en cours de conversation pas encore implémentée")
        return False


# ========== EXEMPLES D'UTILISATION ==========

def configure_restaurant_variables():
    """Exemple de configuration pour un restaurant"""
    manager = DynamicVariablesManager()
    
    variables = {
        "date_actuelle": "Date du jour",
        "heure_actuelle": "Heure actuelle",
        "tables_disponibles_ce_soir": "Disponibilités des tables ce soir",
        "plat_du_jour": "Plat du jour actuel",
        "promotion_en_cours": "Promotion en cours",
        "nom_client": "Nom du client si identifié",
        "statut_ouverture": "Statut d'ouverture actuel"
    }
    
    return manager.configure_dynamic_variables(variables)


def configure_hotel_variables():
    """Exemple de configuration pour un hôtel"""
    manager = DynamicVariablesManager()
    
    variables = {
        "date_actuelle": "Date du jour",
        "chambres_disponibles": "Chambres disponibles ce soir",
        "tarif_nuitee": "Tarif de la nuitée ce soir",
        "nom_client": "Nom du client si identifié",
        "statut_reservation": "Statut de la réservation du client",
        "evenements_hotel": "Événements spéciaux à l'hôtel aujourd'hui"
    }
    
    return manager.configure_dynamic_variables(variables)


def configure_ecommerce_variables():
    """Exemple de configuration pour un e-commerce"""
    manager = DynamicVariablesManager()
    
    variables = {
        "promotion_en_cours": "Promotion actuellement active",
        "code_promo": "Code promo du moment",
        "stock_produit": "Disponibilité en stock",
        "delai_livraison": "Délai de livraison estimé",
        "nom_client": "Nom du client si identifié",
        "statut_commande": "Statut de la dernière commande"
    }
    
    return manager.configure_dynamic_variables(variables)


if __name__ == "__main__":
    # Test : Configurer les variables pour un restaurant
    logger.info("🧪 Test de configuration des variables dynamiques")
    
    success = configure_restaurant_variables()
    
    if success:
        logger.success("✅ Variables configurées avec succès !")
        
        # Simuler la récupération des variables pour un appel
        manager = DynamicVariablesManager()
        variables = manager.get_variables_for_call(
            caller_number="+33612345678",
            enabled_variables=["datetime", "availability", "business_status"]
        )
        
        logger.info(f"📊 Variables récupérées : {variables}")
    else:
        logger.error("❌ Échec de la configuration")
