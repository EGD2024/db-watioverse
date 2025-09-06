#!/usr/bin/env python3
"""
API REST para Cuestionarios Dinámicos
Proporciona endpoints para gestionar cuestionarios de completitud de datos
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import logging
from questionnaire_manager import QuestionnaireManager

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Inicializar gestor de cuestionarios
questionnaire_manager = QuestionnaireManager()

@app.route('/api/questionnaire/<session_token>', methods=['GET'])
def get_questionnaire(session_token):
    """Obtener cuestionario por token de sesión"""
    try:
        questionnaire_data = questionnaire_manager.get_questionnaire_data(session_token)
        
        if not questionnaire_data:
            return jsonify({
                'error': 'Cuestionario no encontrado o expirado',
                'session_token': session_token
            }), 404
        
        return jsonify({
            'success': True,
            'data': questionnaire_data
        })
        
    except Exception as e:
        logger.error(f"Error obteniendo cuestionario: {e}")
        return jsonify({
            'error': 'Error interno del servidor',
            'details': str(e)
        }), 500

@app.route('/api/questionnaire/<session_token>/response', methods=['POST'])
def save_response(session_token):
    """Guardar respuesta del cuestionario"""
    try:
        data = request.get_json()
        
        if not data or 'field_name' not in data or 'response_value' not in data:
            return jsonify({
                'error': 'Datos requeridos: field_name, response_value'
            }), 400
        
        success = questionnaire_manager.save_response(
            session_token,
            data['field_name'],
            data['response_value']
        )
        
        if success:
            # Obtener progreso actualizado
            questionnaire_data = questionnaire_manager.get_questionnaire_data(session_token)
            
            return jsonify({
                'success': True,
                'message': 'Respuesta guardada correctamente',
                'completion_percentage': questionnaire_data.get('completion_percentage', 0) if questionnaire_data else 0
            })
        else:
            return jsonify({
                'error': 'No se pudo guardar la respuesta'
            }), 400
            
    except Exception as e:
        logger.error(f"Error guardando respuesta: {e}")
        return jsonify({
            'error': 'Error interno del servidor',
            'details': str(e)
        }), 500

@app.route('/api/questionnaire/<session_token>/responses', methods=['GET'])
def get_responses(session_token):
    """Obtener todas las respuestas de una sesión"""
    try:
        responses = questionnaire_manager.get_completed_responses(session_token)
        
        return jsonify({
            'success': True,
            'data': responses
        })
        
    except Exception as e:
        logger.error(f"Error obteniendo respuestas: {e}")
        return jsonify({
            'error': 'Error interno del servidor',
            'details': str(e)
        }), 500

@app.route('/api/questionnaire/create', methods=['POST'])
def create_questionnaire():
    """Crear nuevo cuestionario"""
    try:
        data = request.get_json()
        
        if not data or 'cups' not in data or 'missing_fields' not in data:
            return jsonify({
                'error': 'Datos requeridos: cups, missing_fields'
            }), 400
        
        session_token = questionnaire_manager.create_questionnaire_session(
            data['cups'],
            data['missing_fields'],
            data.get('document_id')
        )
        
        if session_token:
            return jsonify({
                'success': True,
                'session_token': session_token,
                'message': 'Cuestionario creado correctamente'
            })
        else:
            return jsonify({
                'error': 'No se pudo crear el cuestionario'
            }), 400
            
    except Exception as e:
        logger.error(f"Error creando cuestionario: {e}")
        return jsonify({
            'error': 'Error interno del servidor',
            'details': str(e)
        }), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Endpoint de salud"""
    return jsonify({
        'status': 'healthy',
        'service': 'questionnaire-api',
        'timestamp': datetime.now().isoformat()
    })

if __name__ == '__main__':
    logger.info("🚀 Iniciando API de Cuestionarios Dinámicos...")
    app.run(host='0.0.0.0', port=5001, debug=True)
