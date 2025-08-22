# app/routes/dashboard_routes.py
from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from .. import dashboard_service # This will be created in __init__.py

bp = Blueprint('dashboard', __name__, url_prefix='/dashboard')

@bp.route('/', methods=['GET'])
@login_required
def view_dashboard():
    # Ensure the user is an admin
    if not current_user.is_admin:
        flash('You do not have permission to access the dashboard.', 'error')
        return redirect(url_for('home'))

    # Get the time period from the URL, default to 7 days
    try:
        # 'all' will be passed for all-time stats
        period = request.args.get('period', '7')
        period_days = 0 if period == 'all' else int(period)
    except ValueError:
        period_days = 7

    stats = dashboard_service.get_stats(period_days=period_days)
    
    return render_template(
        'dashboard/index.html', 
        stats=stats, 
        active_period=period
    )