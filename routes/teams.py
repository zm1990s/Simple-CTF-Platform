import random
import string
from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from models import db, Team, TeamMember

teams_bp = Blueprint('teams', __name__)


def _unique_invite_code():
    """Generate a unique 8-character invite code."""
    for _ in range(10):
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        if not Team.query.filter_by(invite_code=code).first():
            return code
    raise RuntimeError('Could not generate a unique invite code')


@teams_bp.route('/teams')
@login_required
def teams_list():
    """Browse all teams."""
    teams = Team.query.order_by(Team.created_at.desc()).all()
    my_membership = current_user.team_membership
    return render_template('teams/teams.html', teams=teams, my_membership=my_membership)


@teams_bp.route('/teams/create', methods=['GET', 'POST'])
@login_required
def create_team():
    """Create a new team."""
    if current_user.team_membership:
        flash('You are already in a team. Leave your current team first.', 'warning')
        return redirect(url_for('teams.my_team'))

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        description = request.form.get('description', '').strip()

        if not name:
            flash('Team name is required.', 'danger')
            return render_template('teams/create_team.html')

        if len(name) > 100:
            flash('Team name must be 100 characters or fewer.', 'danger')
            return render_template('teams/create_team.html')

        if Team.query.filter_by(name=name).first():
            flash('A team with this name already exists.', 'danger')
            return render_template('teams/create_team.html')

        team = Team(
            name=name,
            description=description,
            invite_code=_unique_invite_code(),
            captain_id=current_user.id,
        )
        db.session.add(team)
        db.session.flush()  # populate team.id

        member = TeamMember(team_id=team.id, user_id=current_user.id)
        db.session.add(member)
        db.session.commit()

        flash(f'Team "{name}" created successfully!', 'success')
        return redirect(url_for('teams.my_team'))

    return render_template('teams/create_team.html')


@teams_bp.route('/teams/my')
@login_required
def my_team():
    """View my current team."""
    membership = current_user.team_membership
    if not membership:
        return redirect(url_for('teams.create_team'))

    team = membership.team
    members = TeamMember.query.filter_by(team_id=team.id).order_by(TeamMember.joined_at).all()
    return render_template('teams/my_team.html', team=team, members=members)


@teams_bp.route('/teams/join', methods=['POST'])
@login_required
def join_team():
    """Join a team by invite code."""
    if current_user.team_membership:
        flash('You are already in a team.', 'warning')
        return redirect(url_for('teams.my_team'))

    invite_code = request.form.get('invite_code', '').strip().upper()
    if not invite_code:
        flash('Please enter an invite code.', 'danger')
        return redirect(url_for('teams.teams_list'))

    team = Team.query.filter_by(invite_code=invite_code).first()
    if not team:
        flash('Invalid invite code.', 'danger')
        return redirect(url_for('teams.teams_list'))

    member = TeamMember(team_id=team.id, user_id=current_user.id)
    db.session.add(member)
    db.session.commit()

    flash(f'Joined team "{team.name}" successfully!', 'success')
    return redirect(url_for('teams.my_team'))


@teams_bp.route('/teams/leave', methods=['POST'])
@login_required
def leave_team():
    """Leave current team. Disbands if captain leaves as last member."""
    membership = current_user.team_membership
    if not membership:
        flash('You are not in a team.', 'warning')
        return redirect(url_for('teams.teams_list'))

    team = membership.team
    team_name = team.name

    if team.captain_id == current_user.id:
        # Find another member to hand captaincy to
        other = TeamMember.query.filter(
            TeamMember.team_id == team.id,
            TeamMember.user_id != current_user.id
        ).first()
        if other:
            team.captain_id = other.user_id
        else:
            # Last member — disband
            db.session.delete(team)
            db.session.commit()
            flash(f'Team "{team_name}" disbanded (you were the last member).', 'info')
            return redirect(url_for('teams.teams_list'))

    db.session.delete(membership)
    db.session.commit()
    flash(f'You have left team "{team_name}".', 'info')
    return redirect(url_for('teams.teams_list'))


@teams_bp.route('/teams/<int:team_id>/kick/<int:user_id>', methods=['POST'])
@login_required
def kick_member(team_id, user_id):
    """Captain removes a member from the team."""
    team = Team.query.get_or_404(team_id)
    if team.captain_id != current_user.id:
        abort(403)
    if user_id == current_user.id:
        flash('Use "Leave Team" to remove yourself.', 'warning')
        return redirect(url_for('teams.my_team'))

    member = TeamMember.query.filter_by(team_id=team_id, user_id=user_id).first_or_404()
    db.session.delete(member)
    db.session.commit()
    flash('Member removed from the team.', 'success')
    return redirect(url_for('teams.my_team'))
