from flask import Blueprint, request, jsonify
import sys
import os
import threading
import time
from datetime import datetime

# Add the mass_registration_bot directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'mass_registration_bot'))

try:
    from campaign_manager import CampaignManager, CampaignConfig
except ImportError:
    print("Warning: Could not import campaign_manager. Make sure the path is correct.")
    CampaignManager = None
    CampaignConfig = None

campaign_bp = Blueprint('campaign', __name__)

# Global variable to store the current campaign manager
current_campaign = None
campaign_thread = None

@campaign_bp.route('/campaigns', methods=['POST'])
def start_campaign():
    """Start a new mass registration campaign"""
    global current_campaign, campaign_thread
    
    if CampaignManager is None or CampaignConfig is None:
        return jsonify({'error': 'Campaign manager not available'}), 500
    
    if current_campaign and current_campaign.is_running:
        return jsonify({'error': 'A campaign is already running'}), 400
    
    data = request.get_json()
    
    try:
        config = CampaignConfig(
            campaign_name=data.get('campaignName', f'Campaign_{datetime.now().strftime("%Y%m%d_%H%M%S")}'),
            target_url=data.get('targetUrl', 'https://manus.im'),
            registration_count=int(data.get('registrationCount', 10)),
            min_interval=int(data.get('minInterval', 5)),
            max_interval=int(data.get('maxInterval', 15)),
            twocaptcha_api_key=data.get('twoCaptchaApiKey', '75c2e3c436c5b8deabe099f794b2b8de'),
            parallel_workers=int(data.get('parallelWorkers', 3))
        )
        
        current_campaign = CampaignManager(config)
        
        # Start campaign in a separate thread
        campaign_thread = threading.Thread(target=current_campaign.start_campaign)
        campaign_thread.daemon = True
        campaign_thread.start()
        
        return jsonify({
            'message': 'Campaign started successfully',
            'campaign_name': config.campaign_name,
            'status': 'running'
        })
        
    except Exception as e:
        return jsonify({'error': f'Failed to start campaign: {str(e)}'}), 500

@campaign_bp.route('/campaigns/status', methods=['GET'])
def get_campaign_status():
    """Get the current campaign status"""
    global current_campaign
    
    if not current_campaign:
        return jsonify({
            'isRunning': False,
            'completed': 0,
            'failed': 0,
            'total': 0,
            'currentProgress': 0
        })
    
    progress = current_campaign.get_progress()
    
    return jsonify({
        'isRunning': current_campaign.is_running,
        'isPaused': current_campaign.is_paused,
        'completed': progress.get('completed', 0),
        'failed': progress.get('failed', 0),
        'total': progress.get('total', 0),
        'currentProgress': (progress.get('completed', 0) / max(progress.get('total', 1), 1)) * 100
    })

@campaign_bp.route('/campaigns/pause', methods=['POST'])
def pause_campaign():
    """Pause the current campaign"""
    global current_campaign
    
    if not current_campaign or not current_campaign.is_running:
        return jsonify({'error': 'No running campaign to pause'}), 400
    
    current_campaign.pause_campaign()
    return jsonify({'message': 'Campaign paused successfully'})

@campaign_bp.route('/campaigns/resume', methods=['POST'])
def resume_campaign():
    """Resume the current campaign"""
    global current_campaign
    
    if not current_campaign or not current_campaign.is_paused:
        return jsonify({'error': 'No paused campaign to resume'}), 400
    
    current_campaign.resume_campaign()
    return jsonify({'message': 'Campaign resumed successfully'})

@campaign_bp.route('/campaigns/stop', methods=['POST'])
def stop_campaign():
    """Stop the current campaign"""
    global current_campaign
    
    if not current_campaign:
        return jsonify({'error': 'No campaign to stop'}), 400
    
    current_campaign.stop_campaign()
    return jsonify({'message': 'Campaign stopped successfully'})

@campaign_bp.route('/campaigns/reports', methods=['GET'])
def get_campaign_reports():
    """Get campaign reports"""
    # This would typically read from a database or file system
    # For now, returning mock data
    reports = [
        {
            'id': 1,
            'name': 'Campanha Teste 1',
            'date': '2025-01-15',
            'success': 85,
            'total': 100,
            'success_rate': 85
        },
        {
            'id': 2,
            'name': 'Campanha Teste 2',
            'date': '2025-01-14',
            'success': 92,
            'total': 150,
            'success_rate': 61
        }
    ]
    
    return jsonify(reports)

@campaign_bp.route('/campaigns/config', methods=['GET'])
def get_default_config():
    """Get default campaign configuration"""
    return jsonify({
        'campaignName': '',
        'targetUrl': 'https://manus.im',
        'registrationCount': 10,
        'minInterval': 5,
        'maxInterval': 15,
        'twoCaptchaApiKey': '',
        'parallelWorkers': 3
    })

