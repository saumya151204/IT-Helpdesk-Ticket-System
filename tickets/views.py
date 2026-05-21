from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.db.models import Q
from .models import Ticket, Comment, Profile


# ── Auto-create profile helper ──
def get_or_create_profile(user):
    profile, _ = Profile.objects.get_or_create(user=user)
    return profile


# ── Home ──
def home(request):
    return render(request, 'home.html')


# ── Register ──
def register(request):
    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')
        confirm  = request.POST.get('confirm_password')

        if password != confirm:
            return render(request, 'register.html', {'error': 'Passwords do not match'})

        if User.objects.filter(username=username).exists():
            return render(request, 'register.html', {'error': 'Username already exists'})

        user = User.objects.create_user(username=username, password=password)
        Profile.objects.create(user=user, role='user')
        return redirect('login')

    return render(request, 'register.html')


# ── Login ──
def user_login(request):
    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            profile = get_or_create_profile(user)

            if profile.role == 'admin' or user.is_superuser:
                return redirect('admin_dashboard')
            elif profile.role == 'staff':
                return redirect('staff_dashboard')
            else:
                return redirect('user_dashboard')
        else:
            return render(request, 'login.html', {'error': 'Invalid credentials'})

    return render(request, 'login.html')


# ── Logout ──
def user_logout(request):
    logout(request)
    return redirect('login')


# ──────────────────────────────────────────
# USER DASHBOARD
# ──────────────────────────────────────────
@login_required
def user_dashboard(request):
    tickets = Ticket.objects.filter(user=request.user)

    query = request.GET.get('q')
    if query:
        tickets = tickets.filter(
            Q(title__icontains=query) | Q(description__icontains=query)
        )

    status   = request.GET.get('status')
    priority = request.GET.get('priority')
    if status:   tickets = tickets.filter(status=status)
    if priority: tickets = tickets.filter(priority=priority)

    stats = {
        'total':       Ticket.objects.filter(user=request.user).count(),
        'open':        Ticket.objects.filter(user=request.user, status='Open').count(),
        'in_progress': Ticket.objects.filter(user=request.user, status='In Progress').count(),
        'resolved':    Ticket.objects.filter(user=request.user, status='Resolved').count(),
    }

    return render(request, 'user_dashboard.html', {'tickets': tickets, 'stats': stats})


# ──────────────────────────────────────────
# STAFF DASHBOARD
# ──────────────────────────────────────────
@login_required
def staff_dashboard(request):
    profile = get_or_create_profile(request.user)
    if profile.role not in ['staff', 'admin'] and not request.user.is_superuser:
        return redirect('user_dashboard')

    tickets = Ticket.objects.filter(assigned_to=request.user)

    query = request.GET.get('q')
    if query:
        tickets = tickets.filter(
            Q(title__icontains=query) | Q(description__icontains=query)
        )

    status = request.GET.get('status')
    if status: tickets = tickets.filter(status=status)

    stats = {
        'total':       Ticket.objects.filter(assigned_to=request.user).count(),
        'open':        Ticket.objects.filter(assigned_to=request.user, status='Open').count(),
        'in_progress': Ticket.objects.filter(assigned_to=request.user, status='In Progress').count(),
        'resolved':    Ticket.objects.filter(assigned_to=request.user, status='Resolved').count(),
    }

    return render(request, 'staff_dashboard.html', {'tickets': tickets, 'stats': stats})


# ──────────────────────────────────────────
# ADMIN DASHBOARD
# ──────────────────────────────────────────
@login_required
def admin_dashboard(request):
    profile = get_or_create_profile(request.user)
    if profile.role != 'admin' and not request.user.is_superuser:
        return redirect('user_dashboard')

    tickets = Ticket.objects.all()

    query    = request.GET.get('q')
    status   = request.GET.get('status')
    priority = request.GET.get('priority')

    if query:    tickets = tickets.filter(Q(title__icontains=query) | Q(description__icontains=query))
    if status:   tickets = tickets.filter(status=status)
    if priority: tickets = tickets.filter(priority=priority)

    staff_users = Profile.objects.filter(role__in=['staff', 'admin'])

    stats = {
        'total':       Ticket.objects.count(),
        'open':        Ticket.objects.filter(status='Open').count(),
        'in_progress': Ticket.objects.filter(status='In Progress').count(),
        'resolved':    Ticket.objects.filter(status='Resolved').count(),
        'total_users': User.objects.count(),
        'total_staff': Profile.objects.filter(role='staff').count(),
    }

    return render(request, 'admin_dashboard.html', {
        'tickets': tickets,
        'stats': stats,
        'staff_users': staff_users,
    })


# ── Update Ticket (Admin/Staff) ──
@login_required
def update_ticket(request, id):
    ticket = get_object_or_404(Ticket, id=id)
    profile = get_or_create_profile(request.user)

    if profile.role not in ['staff', 'admin'] and not request.user.is_superuser:
        return redirect('user_dashboard')

    staff_list = Profile.objects.filter(role__in=['staff', 'admin'])

    if request.method == 'POST':
        ticket.status      = request.POST.get('status', ticket.status)
        ticket.priority    = request.POST.get('priority', ticket.priority)
        assigned_id        = request.POST.get('assigned_to')
        if assigned_id:
            ticket.assigned_to = User.objects.get(id=assigned_id)
        ticket.save()
        return redirect('admin_dashboard')

    return render(request, 'update_ticket.html', {'ticket': ticket, 'staff_list': staff_list})


# ── Create Ticket ──
@login_required
def create_ticket(request):
    if request.method == 'POST':
        Ticket.objects.create(
            user=request.user,
            title=request.POST['title'],
            description=request.POST['description'],
            priority=request.POST['priority'],
        )
        return redirect('user_dashboard')
    return render(request, 'create_ticket.html')


# ── Ticket Detail ──
@login_required
def ticket_detail(request, id):
    ticket   = get_object_or_404(Ticket, id=id)
    comments = Comment.objects.filter(ticket=ticket)

    if request.method == 'POST':
        message = request.POST.get('message')
        Comment.objects.create(ticket=ticket, user=request.user, message=message)
        return redirect('ticket_detail', id=id)

    return render(request, 'ticket_detail.html', {'ticket': ticket, 'comments': comments})