import os
import logging
from flask import Blueprint, render_template, request, flash, redirect, url_for, Response, stream_with_context
from dotenv import load_dotenv

from .redmine_service import RedmineService

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

load_dotenv()

checklist_bp = Blueprint('checklist_bp', __name__,
                        template_folder='templates',
                        static_folder='static')


REDMINE_URL = os.getenv('REDMINE_URL', 'https://redmine.starline.ru')
REDMINE_API_KEY = os.getenv('REDMINE_API_KEY')

@checklist_bp.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        issue_id = request.form.get('issue_id')
        if not issue_id:
            flash('Пожалуйста, введите ID задачи', 'error')
            return redirect(url_for('.index'))
        
        return redirect(url_for('.sort_progress', issue_id=issue_id))

    return render_template('checklist_index.html')

@checklist_bp.route('/sort/<issue_id>')
def sort_progress(issue_id):
    if not REDMINE_API_KEY:
        return "API Key не настроен", 500

    service = RedmineService(REDMINE_URL, REDMINE_API_KEY)
    
    def generate():
        yield "Starting process...\n"
        for status in service.sort_checklists_generator(issue_id):
            yield f"{status}\n"
            
    return Response(stream_with_context(generate()), mimetype='text/plain')
