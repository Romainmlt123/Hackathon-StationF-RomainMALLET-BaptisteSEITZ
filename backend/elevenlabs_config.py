"""
Module pour synchroniser la configuration du Company Profile avec l'agent ElevenLabs.
Ce module permet de mettre à jour l'agent avec les informations spécifiques de l'entreprise.
"""

import os
import requests
from typing import Dict, Any, Optional
from loguru import logger
from dotenv import load_dotenv

load_dotenv()

ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
ELEVENLABS_AGENT_ID = os.getenv("ELEVENLABS_AGENT_ID", "agent_6301ka40ge0dfyrbx84ebjpg898k")


class ElevenLabsAgentConfig:
    """Gestionnaire de configuration pour l'agent ElevenLabs"""
    
    def __init__(self, api_key: str = ELEVENLABS_API_KEY, agent_id: str = ELEVENLABS_AGENT_ID):
        self.api_key = api_key
        self.agent_id = agent_id
        self.base_url = "https://api.elevenlabs.io/v1"
        self.headers = {
            "xi-api-key": self.api_key,
            "Content-Type": "application/json"
        }
    
    def get_agent_config(self) -> Optional[Dict[str, Any]]:
        """Récupère la configuration actuelle de l'agent"""
        url = f"{self.base_url}/convai/agents/{self.agent_id}"
        
        try:
            response = requests.get(url, headers=self.headers)
            if response.status_code == 200:
                logger.info(f"✅ Configuration de l'agent récupérée")
                return response.json()
            else:
                logger.error(f"❌ Erreur {response.status_code}: {response.text}")
                return None
        except Exception as e:
            logger.error(f"❌ Erreur lors de la récupération: {e}")
            return None
    
    def update_agent_prompt(self, company_profile: Dict[str, Any]) -> bool:
        """
        Met à jour le prompt système de l'agent avec les informations de l'entreprise.
        
        Args:
            company_profile: Dictionnaire contenant les infos du Company Profile
                {
                    "company_name": "...",
                    "industry": "...",
                    "description": "...",
                    "address": "...",
                    "email": "...",
                    "website": "...",
                    "hours": {...},
                    "faqs": [...]
                }
        """
        # Construire le prompt enrichi avec les infos de l'entreprise
        system_prompt = self._build_system_prompt(company_profile)
        
        url = f"{self.base_url}/convai/agents/{self.agent_id}"
        
        payload = {
            "conversation_config": {
                "agent": {
                    "prompt": {
                        "prompt": system_prompt
                    }
                }
            }
        }
        
        try:
            response = requests.patch(url, headers=self.headers, json=payload)
            if response.status_code == 200:
                logger.success(f"✅ Agent mis à jour avec le profil de {company_profile.get('company_name', 'l'entreprise')}")
                return True
            else:
                logger.error(f"❌ Erreur {response.status_code}: {response.text}")
                return False
        except Exception as e:
            logger.error(f"❌ Erreur lors de la mise à jour: {e}")
            return False
    
    def _build_system_prompt(self, profile: Dict[str, Any]) -> str:
        """Construit un prompt système enrichi avec les informations de l'entreprise"""
        
        company_name = profile.get("company_name", "notre entreprise")
        industry = profile.get("industry", "")
        description = profile.get("description", "")
        address = profile.get("address", "")
        email = profile.get("email", "")
        website = profile.get("website", "")
        phone = profile.get("phone", "")
        
        # Horaires
        hours = profile.get("hours", {})
        hours_text = self._format_hours(hours)
        
        # Services/Produits
        services = profile.get("services", [])
        services_text = ", ".join(services) if services else ""
        
        # FAQs
        faqs = profile.get("faqs", [])
        faqs_text = self._format_faqs(faqs)
        
        # Construire le prompt
        prompt = f"""Tu es l'assistant vocal intelligent de {company_name}."""
        
        if industry:
            prompt += f"\n\nNous sommes une entreprise dans le secteur {industry}."
        
        if description:
            prompt += f"\n\n{description}"
        
        prompt += f"\n\n## INFORMATIONS DE CONTACT"
        if address:
            prompt += f"\n- Adresse : {address}"
        if phone:
            prompt += f"\n- Téléphone : {phone}"
        if email:
            prompt += f"\n- Email : {email}"
        if website:
            prompt += f"\n- Site web : {website}"
        
        if hours_text:
            prompt += f"\n\n## HORAIRES D'OUVERTURE\n{hours_text}"
        
        if services_text:
            prompt += f"\n\n## NOS SERVICES\n{services_text}"
        
        if faqs_text:
            prompt += f"\n\n## QUESTIONS FRÉQUENTES\n{faqs_text}"
        
        prompt += """

## TON RÔLE
- Réponds de manière professionnelle, chaleureuse et efficace
- Utilise les informations ci-dessus pour répondre aux questions
- Si tu ne connais pas la réponse, propose de transférer à un membre de l'équipe
- Sois proactif : propose des services pertinents selon les besoins du client
- Garde un ton naturel et conversationnel

## CAPACITÉS
- Prendre des rendez-vous et réservations
- Répondre aux questions sur nos services
- Fournir les informations de contact et horaires
- Transférer les appels urgents ou complexes
"""
        
        return prompt
    
    def _format_hours(self, hours: Dict[str, Any]) -> str:
        """Formate les horaires d'ouverture"""
        if not hours:
            return ""
        
        days_fr = {
            "monday": "Lundi",
            "tuesday": "Mardi",
            "wednesday": "Mercredi",
            "thursday": "Jeudi",
            "friday": "Vendredi",
            "saturday": "Samedi",
            "sunday": "Dimanche"
        }
        
        lines = []
        for day_en, day_fr in days_fr.items():
            if day_en in hours:
                day_hours = hours[day_en]
                open_time = day_hours.get("open", "")
                close_time = day_hours.get("close", "")
                if open_time and close_time:
                    lines.append(f"- {day_fr}: {open_time} - {close_time}")
                elif day_hours.get("closed"):
                    lines.append(f"- {day_fr}: Fermé")
        
        return "\n".join(lines)
    
    def _format_faqs(self, faqs: list) -> str:
        """Formate les FAQs"""
        if not faqs:
            return ""
        
        lines = []
        for i, faq in enumerate(faqs, 1):
            question = faq.get("question", "")
            answer = faq.get("answer", "")
            if question and answer:
                lines.append(f"\n**Q{i}: {question}**")
                lines.append(f"R: {answer}")
        
        return "\n".join(lines)
    
    def upload_knowledge_base(self, documents: list) -> bool:
        """
        Upload des documents dans la base de connaissances de l'agent.
        
        Args:
            documents: Liste de chemins vers les fichiers à uploader
        """
        url = f"{self.base_url}/convai/agents/{self.agent_id}/knowledge-base"
        
        # TODO: Implémenter l'upload de fichiers
        # L'API ElevenLabs supporte l'upload de documents PDF, TXT, etc.
        logger.warning("⚠️  Upload de documents pas encore implémenté")
        return False


def sync_company_profile_to_agent(company_profile: Dict[str, Any]) -> bool:
    """
    Fonction principale pour synchroniser le Company Profile vers l'agent ElevenLabs.
    
    Args:
        company_profile: Données du Company Profile depuis le frontend
    
    Returns:
        bool: True si la synchronisation a réussi
    """
    config_manager = ElevenLabsAgentConfig()
    
    # Mettre à jour le prompt système
    success = config_manager.update_agent_prompt(company_profile)
    
    if success:
        logger.success(f"🎉 Agent configuré pour {company_profile.get('company_name', 'l'entreprise')}")
    else:
        logger.error("❌ Échec de la configuration de l'agent")
    
    return success


if __name__ == "__main__":
    # Test avec des données exemple
    test_profile = {
        "company_name": "The Ritz Paris",
        "industry": "Hôtellerie de luxe",
        "description": "Palace parisien emblématique offrant un service d'exception depuis 1898.",
        "address": "15 Place Vendôme, 75001 Paris",
        "email": "reservations@ritzparis.com",
        "website": "https://www.ritzparis.com",
        "phone": "+33 1 43 16 30 30",
        "hours": {
            "monday": {"open": "00:00", "close": "23:59"},
            "tuesday": {"open": "00:00", "close": "23:59"},
            "wednesday": {"open": "00:00", "close": "23:59"},
            "thursday": {"open": "00:00", "close": "23:59"},
            "friday": {"open": "00:00", "close": "23:59"},
            "saturday": {"open": "00:00", "close": "23:59"},
            "sunday": {"open": "00:00", "close": "23:59"}
        },
        "services": [
            "Réservations de chambres et suites",
            "Restaurant L'Espadon (gastronomie française)",
            "Bar Hemingway",
            "Spa Chanel",
            "Service de conciergerie 24/7"
        ],
        "faqs": [
            {
                "question": "Quels sont vos horaires de check-in et check-out ?",
                "answer": "Check-in à partir de 15h, check-out jusqu'à 12h."
            },
            {
                "question": "Avez-vous un parking ?",
                "answer": "Oui, nous avons un parking privé avec voiturier disponible 24/7."
            },
            {
                "question": "Acceptez-vous les animaux de compagnie ?",
                "answer": "Oui, les animaux de compagnie sont les bienvenus moyennant un supplément."
            }
        ]
    }
    
    sync_company_profile_to_agent(test_profile)
