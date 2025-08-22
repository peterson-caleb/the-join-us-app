# app/routes/dashboard_routes.py
from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from .. import dashboard_service 

bp = Blueprint('dashboard', __name__, url_prefix='/dashboard')

@bp.route('/', methods=['GET'])
@login_required
def view_dashboard():
    if not current_user.is_admin:
        flash('You do not have permission to access the dashboard.', 'error')
        return redirect(url_for('home'))

    period = request.args.get('period', '7')
    details_type = request.args.get('details') 

    try:
        period_days = 0 if period == 'all' else int(period)
    except ValueError:
        period_days = 7

    stats = dashboard_service.get_stats(period_days=period_days)
    
    # --- THIS IS THE FIX ---
    details_data = [] # Initialize with an empty list instead of None
    # --- END OF FIX ---

    if details_type:
        if details_type == 'messages_sent':
            details_data = dashboard_service.get_sent_messages_details(period_days)
        elif details_type == 'confirmed_rsvps':
            details_data = dashboard_service.get_rsvp_details(period_days, status='YES')
        elif details_type == 'declined_rsvps':
            details_data = dashboard_service.get_rsvp_details(period_days, status='NO')

    return render_template(
        'dashboard/index.html', 
        stats=stats, 
        active_period=period,
        details_data=details_data,
        show_modal_for=details_type
    )