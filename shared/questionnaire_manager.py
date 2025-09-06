#!/usr/bin/env python3
"""
Gestor de Cuestionarios Dinámicos
Maneja la generación, almacenamiento y procesamiento de cuestionarios
basados en campos faltantes detectados por el validador de integridad.
"""

import json
import uuid
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import psycopg2
from psycopg2.extras import RealDictCursor

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class QuestionnaireManager:
    """Gestor de cuestionarios dinámicos para completar datos faltantes"""
    
    def __init__(self, db_config: Dict[str, str] = None):
        """
        Inicializar gestor de cuestionarios
        
        Args:
            db_config: Configuración de conexión a BD N1
        """
        self.db_config = db_config or {
            'host': 'localhost',
            'port': '5432',
            'database': 'db_N1',
            'user': 'postgres',
            'password': 'password'
        }
        
        # Mapeo de campos críticos detectados por análisis masivo
        self.critical_fields = {
            'cups': {
                'question': '¿Cuál es el código CUPS de su punto de suministro?',
                'type': 'text',
                'validation': r'^ES\d{18}[A-Z]{2}\d{1}[A-Z]{1}$',
                'help': 'El CUPS es un código único que identifica su punto de suministro. Lo encuentra en su factura.'
            },
            'potencia_contratada': {
                'question': '¿Cuál es su potencia contratada en kW?',
                'type': 'number',
                'validation': r'^\d+(\.\d{1,2})?$',
                'help': 'La potencia contratada aparece en su factura eléctrica, expresada en kW.'
            },
            'tarifa_acceso': {
                'question': '¿Qué tarifa de acceso tiene contratada?',
                'type': 'select',
                'options': ['2.0TD', '3.0TD', '6.1TD', '6.2TD', '6.3TD', '6.4TD'],
                'help': 'La tarifa de acceso aparece en su factura eléctrica.'
            }
        }
    
    def _get_db_connection(self):
        """Obtener conexión a base de datos N1"""
        try:
            conn = psycopg2.connect(**self.db_config)
            return conn
        except Exception as e:
            logger.error(f"Error conectando a BD N1: {e}")
            return None
    
    def create_questionnaire_session(self, cups: str, missing_fields: List[str], 
                                   document_id: Optional[int] = None) -> Optional[str]:
        """
        Crear sesión de cuestionario para campos faltantes
        
        Args:
            cups: Código CUPS del cliente
            missing_fields: Lista de campos faltantes
            document_id: ID del documento en BD (opcional)
            
        Returns:
            Token de sesión único o None si falla
        """
        try:
            conn = self._get_db_connection()
            if not conn:
                return None
            
            cursor = conn.cursor()
            
            # Generar token único
            session_token = str(uuid.uuid4())
            
            # Filtrar solo campos críticos que tenemos configurados
            critical_missing = [field for field in missing_fields 
                              if field in self.critical_fields]
            
            if not critical_missing:
                logger.info(f"No hay campos críticos faltantes para CUPS {cups}")
                return None
            
            # Insertar sesión de cuestionario
            cursor.execute("""
                INSERT INTO questionnaire_sessions 
                (session_token, cups, missing_fields, total_questions, document_id)
                VALUES (%s, %s, %s, %s, %s)
            """, (
                session_token,
                cups,
                json.dumps(critical_missing),
                len(critical_missing),
                document_id
            ))
            
            conn.commit()
            logger.info(f"✅ Sesión cuestionario creada: {session_token} para CUPS {cups}")
            logger.info(f"   📋 Campos faltantes: {critical_missing}")
            
            return session_token
            
        except Exception as e:
            logger.error(f"Error creando sesión cuestionario: {e}")
            return None
        finally:
            if conn:
                conn.close()
    
    def get_questionnaire_data(self, session_token: str) -> Optional[Dict[str, Any]]:
        """
        Obtener datos del cuestionario para una sesión
        
        Args:
            session_token: Token de sesión
            
        Returns:
            Datos del cuestionario o None si no existe
        """
        try:
            conn = self._get_db_connection()
            if not conn:
                return None
            
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            # Obtener sesión
            cursor.execute("""
                SELECT * FROM questionnaire_sessions 
                WHERE session_token = %s AND status != 'expired'
            """, (session_token,))
            
            session = cursor.fetchone()
            if not session:
                logger.warning(f"Sesión no encontrada o expirada: {session_token}")
                return None
            
            # Generar preguntas basadas en campos faltantes
            missing_fields = json.loads(session['missing_fields'])
            questions = []
            
            for field in missing_fields:
                if field in self.critical_fields:
                    field_config = self.critical_fields[field]
                    question = {
                        'field_name': field,
                        'question_text': field_config['question'],
                        'field_type': field_config['type'],
                        'help_text': field_config['help'],
                        'is_critical': True
                    }
                    
                    if 'options' in field_config:
                        question['options'] = field_config['options']
                    if 'validation' in field_config:
                        question['validation_pattern'] = field_config['validation']
                    
                    questions.append(question)
            
            return {
                'session_token': session_token,
                'cups': session['cups'],
                'questions': questions,
                'total_questions': len(questions),
                'completion_percentage': session['completion_percentage'],
                'status': session['status'],
                'expires_at': session['expires_at'].isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo cuestionario: {e}")
            return None
        finally:
            if conn:
                conn.close()
    
    def save_response(self, session_token: str, field_name: str, 
                     response_value: str) -> bool:
        """
        Guardar respuesta del cuestionario
        
        Args:
            session_token: Token de sesión
            field_name: Nombre del campo
            response_value: Valor de la respuesta
            
        Returns:
            True si se guardó correctamente
        """
        try:
            conn = self._get_db_connection()
            if not conn:
                return False
            
            cursor = conn.cursor()
            
            # Validar respuesta si hay patrón de validación
            if field_name in self.critical_fields:
                field_config = self.critical_fields[field_name]
                if 'validation' in field_config:
                    import re
                    if not re.match(field_config['validation'], response_value):
                        logger.warning(f"Respuesta no válida para {field_name}: {response_value}")
                        return False
            
            # Obtener información de la sesión
            cursor.execute("""
                SELECT id, document_id FROM questionnaire_sessions 
                WHERE session_token = %s
            """, (session_token,))
            
            session = cursor.fetchone()
            if not session:
                return False
            
            session_id, document_id = session
            
            # Obtener ID de pregunta (crear si no existe)
            cursor.execute("""
                SELECT id FROM questionnaire_questions 
                WHERE field_name = %s
            """, (field_name,))
            
            question = cursor.fetchone()
            if not question:
                # Crear pregunta si no existe
                field_config = self.critical_fields.get(field_name, {})
                cursor.execute("""
                    INSERT INTO questionnaire_questions 
                    (field_name, question_text, field_type, is_critical)
                    VALUES (%s, %s, %s, %s)
                    RETURNING id
                """, (
                    field_name,
                    field_config.get('question', f'Valor para {field_name}'),
                    field_config.get('type', 'text'),
                    True
                ))
                question_id = cursor.fetchone()[0]
            else:
                question_id = question[0]
            
            # Guardar respuesta
            cursor.execute("""
                INSERT INTO questionnaire_responses 
                (document_id, question_id, response_value, user_session, is_validated)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (document_id, question_id) 
                DO UPDATE SET 
                    response_value = EXCLUDED.response_value,
                    response_timestamp = CURRENT_TIMESTAMP,
                    is_validated = EXCLUDED.is_validated
            """, (document_id, question_id, response_value, session_token, True))
            
            # Actualizar progreso de sesión
            cursor.execute("""
                UPDATE questionnaire_sessions 
                SET answered_questions = answered_questions + 1,
                    completion_percentage = (answered_questions + 1) * 100.0 / total_questions,
                    status = CASE 
                        WHEN (answered_questions + 1) >= total_questions THEN 'completed'
                        ELSE 'in_progress'
                    END,
                    completed_at = CASE 
                        WHEN (answered_questions + 1) >= total_questions THEN CURRENT_TIMESTAMP
                        ELSE completed_at
                    END
                WHERE session_token = %s
            """, (session_token,))
            
            conn.commit()
            logger.info(f"✅ Respuesta guardada: {field_name} = {response_value}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error guardando respuesta: {e}")
            return False
        finally:
            if conn:
                conn.close()
    
    def get_completed_responses(self, session_token: str) -> Dict[str, str]:
        """
        Obtener respuestas completadas para una sesión
        
        Args:
            session_token: Token de sesión
            
        Returns:
            Diccionario con respuestas completadas
        """
        try:
            conn = self._get_db_connection()
            if not conn:
                return {}
            
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            cursor.execute("""
                SELECT qq.field_name, qr.response_value
                FROM questionnaire_responses qr
                JOIN questionnaire_questions qq ON qr.question_id = qq.id
                JOIN questionnaire_sessions qs ON qr.document_id = qs.document_id
                WHERE qs.session_token = %s AND qr.is_validated = TRUE
            """, (session_token,))
            
            responses = cursor.fetchall()
            return {row['field_name']: row['response_value'] for row in responses}
            
        except Exception as e:
            logger.error(f"Error obteniendo respuestas: {e}")
            return {}
        finally:
            if conn:
                conn.close()
    
    def generate_questionnaire_from_validation(self, validation_report: Dict[str, Any]) -> Optional[str]:
        """
        Generar cuestionario basado en reporte de validación de integridad
        
        Args:
            validation_report: Reporte del IntegrityValidator
            
        Returns:
            Token de sesión del cuestionario generado
        """
        try:
            if not validation_report.get('missing_critical_fields'):
                logger.info("No hay campos críticos faltantes, no se genera cuestionario")
                return None
            
            cups = validation_report.get('cups', 'UNKNOWN')
            missing_fields = validation_report['missing_critical_fields']
            
            session_token = self.create_questionnaire_session(cups, missing_fields)
            
            if session_token:
                logger.info(f"🎯 Cuestionario generado automáticamente para CUPS {cups}")
                logger.info(f"   🔗 Token: {session_token}")
                logger.info(f"   📋 Campos: {missing_fields}")
            
            return session_token
            
        except Exception as e:
            logger.error(f"Error generando cuestionario desde validación: {e}")
            return None

def main():
    """Función principal para pruebas"""
    manager = QuestionnaireManager()
    
    # Ejemplo de uso
    print("🧪 Probando QuestionnaireManager...")
    
    # Simular campos faltantes
    missing_fields = ['cups', 'potencia_contratada']
    session_token = manager.create_questionnaire_session('ES0022000001234567AB1C', missing_fields)
    
    if session_token:
        print(f"✅ Sesión creada: {session_token}")
        
        # Obtener cuestionario
        questionnaire = manager.get_questionnaire_data(session_token)
        if questionnaire:
            print(f"📋 Cuestionario: {len(questionnaire['questions'])} preguntas")
            for q in questionnaire['questions']:
                print(f"   - {q['question_text']}")

if __name__ == "__main__":
    main()
