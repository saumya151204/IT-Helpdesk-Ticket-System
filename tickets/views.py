from django.shortcuts import render, redirect
from .models import Ticket, Comment
from django.contrib.auth.decorators import login_required
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.models import User
from django.db.models import Q
from django.contrib.auth import authenticate, login, logout


def home(request):
    return render(request, 'home.html')

from django.shortcuts import render, redirect
from django.contrib.auth.models import User

def register(request):
    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')

        # CHECK IF USER EXISTS
        if User.objects.filter(username=username).exists():
            return render(request, 'register.html', {
                'error': 'Username already exists'
            })

        # CREATE USER
        User.objects.create_user(username=username, password=password)
        return redirect('login')

    return render(request, 'register.html')
@login_required
def dashboard(request):
    tickets = Ticket.objects.filter(user=request.user)

    # Search
    query = request.GET.get('q')
    if query:
        tickets = tickets.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query)
        )

    # Filter by status
    status = request.GET.get('status')
    if status:
        tickets = tickets.filter(status=status)

    # Filter by priority
    priority = request.GET.get('priority')
    if priority:
        tickets = tickets.filter(priority=priority)

    return render(request, 'dashboard.html', {'tickets': tickets})

@login_required
def create_ticket(request):
    if request.method == 'POST':
        title = request.POST['title']
        description = request.POST['description']
        priority = request.POST['priority']

        Ticket.objects.create(
            user=request.user,
            title=title,
            description=description,
            priority=priority
        )
        return redirect('dashboard')

    return render(request, 'create_ticket.html')

def is_admin(user):
    return user.is_staff


@user_passes_test(is_admin)
def admin_dashboard(request):
    tickets = Ticket.objects.all().order_by('-created_at')
    return render(request, 'admin_dashboard.html', {'tickets': tickets})

@user_passes_test(is_admin)
def update_ticket(request, id):
    ticket = Ticket.objects.get(id=id)

    if request.method == 'POST':
        ticket.status = request.POST['status']
        ticket.save()
        return redirect('admin_dashboard')

    return render(request, 'update_ticket.html', {'ticket': ticket})

@login_required
def ticket_detail(request, id):
    ticket = Ticket.objects.get(id=id)
    comments = Comment.objects.filter(ticket=ticket)

    if request.method == 'POST':
        message = request.POST['message']
        Comment.objects.create(
            ticket=ticket,
            user=request.user,
            message=message
        )
        return redirect('ticket_detail', id=id)

    return render(request, 'ticket_detail.html', {
        'ticket': ticket,
        'comments': comments
    })
def user_login(request):
    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect('home')
        else:
            return render(request, 'login.html', {'error': 'Invalid credentials'})

    return render(request, 'login.html')

def user_logout(request):
    logout(request)
    return redirect('login')