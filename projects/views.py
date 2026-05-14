from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, HttpResponseForbidden
from .models import Project, Bid, Message
from users.models import CustomUser, Notification
from .forms import ProjectForm, BidForm
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from django.contrib import messages


@login_required
def create_project(request):
    if request.user.role != 'client':
        messages.error(request, "Only clients can post projects.")
        return redirect('dashboard')  

    if request.method == 'POST':
        form = ProjectForm(request.POST)
        if form.is_valid():
            project = form.save(commit=False)
            project.client = request.user
            project.save()
            messages.success(request, "Project created successfully!")
            return redirect('dashboard')
    else:
        form = ProjectForm()

    return render(request, 'create_project.html', {'form': form})


@login_required
def place_bid(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    
    if request.user.role != 'freelancer':
        messages.error(request, "Only freelancers can place bids.")
        return redirect('project_detail', project_id=project.id)

    if project.is_assigned:
        messages.error(request, "This project is no longer accepting bids.")
        return redirect('project_detail', project_id=project.id)

    existing_bid = Bid.objects.filter(project=project, freelancer=request.user).first()
    if existing_bid:
        messages.warning(request, "You have already placed a bid on this project.")
        return redirect('project_detail', project_id=project.id)

    if request.method == 'POST':
        form = BidForm(request.POST)
        if form.is_valid():
            bid = form.save(commit=False)
            bid.project = project
            bid.freelancer = request.user
            bid.save()
            
            # Notify client
            Notification.objects.create(
                user=project.client,
                message=f"New bid received for '{project.title}' from {request.user.username}",
                link=f"/projects/bids/{project.id}/"
            )
            
            messages.success(request, "Bid placed successfully!")
            return redirect('project_list')
    else:
        form = BidForm()

    return render(request, 'place_bid.html', {'project': project, 'form': form})


def project_list(request):
    query = request.GET.get('q')
    skills = request.GET.get('skills')
    min_budget = request.GET.get('min_budget')
    max_budget = request.GET.get('max_budget')
    sort = request.GET.get('sort', '-created_at')

    projects = Project.objects.filter(is_assigned=False)

    if query:
        projects = projects.filter(Q(title__icontains=query) | Q(description__icontains=query))
    
    if skills:
        projects = projects.filter(skills_required__icontains=skills)

    if min_budget:
        try:
            projects = projects.filter(budget__gte=int(min_budget))
        except ValueError: pass
    
    if max_budget:
        try:
            projects = projects.filter(budget__lte=int(max_budget))
        except ValueError: pass

    projects = projects.order_by(sort)

    return render(request, 'project_list.html', {'projects': projects})

def project_detail(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    bids = Bid.objects.filter(project=project)
    has_bid = False
    if request.user.is_authenticated:
        has_bid = Bid.objects.filter(project=project, freelancer=request.user).exists()
    
    return render(request, 'project_detail.html', {
        'project': project,
        'bids': bids,
        'has_bid': has_bid
    })


@login_required
def view_bids(request, project_id):
    project = get_object_or_404(Project, id=project_id)

    if request.user != project.client:
        messages.error(request, "Unauthorized access")
        return redirect('dashboard')

    bids = Bid.objects.filter(project=project).order_by('-amount')

    return render(request, 'view_bids.html', {
        'project': project,
        'bids': bids
    })


@login_required
def select_freelancer(request, bid_id):
    bid = get_object_or_404(Bid, id=bid_id)
    project = bid.project

    if request.user != project.client:
        messages.error(request, "Unauthorized access")
        return redirect('dashboard')

    if project.is_assigned:
        messages.error(request, "This project is already assigned.")
        return redirect('view_bids', project_id=project.id)

    # Update project
    project.is_assigned = True
    project.assigned_to = bid.freelancer
    project.save()

    # Update bid status
    bid.status = 'accepted'
    bid.save()

    # Reject other bids
    Bid.objects.filter(project=project).exclude(id=bid_id).update(status='rejected')

    # Send Notification
    Notification.objects.create(
        user=bid.freelancer,
        message=f"Congratulations! Your bid for '{project.title}' has been accepted.",
        link=f"/projects/{project.id}/"
    )

    messages.success(request, f"Bid accepted! {bid.freelancer.username} has been assigned to the project.")
    return redirect('dashboard')

@login_required
def reject_bid(request, bid_id):
    bid = get_object_or_404(Bid, id=bid_id)
    project = bid.project

    if request.user != project.client:
        messages.error(request, "Unauthorized access")
        return redirect('dashboard')

    bid.status = 'rejected'
    bid.save()

    Notification.objects.create(
        user=bid.freelancer,
        message=f"Your bid for '{project.title}' was rejected.",
        link=f"/projects/{project.id}/"
    )

    messages.info(request, "Bid rejected.")
    return redirect('view_bids', project_id=project.id)

@login_required
def my_projects(request):
    if request.user.role != 'client':
        return redirect('dashboard')
    projects = Project.objects.filter(client=request.user).order_by('-created_at')
    return render(request, 'my_projects.html', {'projects': projects})
    

@login_required
def chat_view(request, project_id, user_id):
    project = get_object_or_404(Project, id=project_id)
    other_user = get_object_or_404(CustomUser, id=user_id)

    # Security check: Allow ONLY the project client and the assigned freelancer to chat
    if not project.is_assigned:
        return HttpResponseForbidden("This project has not been assigned to a freelancer yet.")
    
    if request.user != project.client and request.user != project.assigned_to:
        return HttpResponseForbidden("You are not authorized to access this chat.")
    
    if other_user != project.client and other_user != project.assigned_to:
        return HttpResponseForbidden("The recipient is not a participant in this project.")

    messages_list = Message.objects.filter(
        project=project
    ).filter(
        (Q(sender=request.user) & Q(receiver=other_user)) |
        (Q(sender=other_user) & Q(receiver=request.user))
    ).order_by('timestamp')

    if request.method == 'POST':
        content = request.POST.get('content')
        if content:
            Message.objects.create(
                sender=request.user,
                receiver=other_user,
                project=project,
                content=content
            )
            return redirect('chat', project_id=project.id, user_id=other_user.id)

    return render(request, 'chat.html', {
        'messages': messages_list,
        'other_user': other_user,
        'project': project
    })



@login_required
def my_bids(request):
    if request.user.role != 'freelancer':
        return redirect('dashboard')
    
    bids = Bid.objects.filter(freelancer=request.user).order_by('-created_at')
    return render(request, 'my_bids.html', {'bids': bids})

@login_required
def messages_list(request):
    user = request.user
    # Find all users I have messaged with
    messages_sent = Message.objects.filter(sender=user)
    messages_received = Message.objects.filter(receiver=user)
    
    # Store unique pairs of (project, other_user)
    conversations_map = {}
    
    for m in messages_sent:
        key = (m.project.id, m.receiver.id)
        if key not in conversations_map or m.timestamp > conversations_map[key].timestamp:
            conversations_map[key] = m
            
    for m in messages_received:
        key = (m.project.id, m.sender.id)
        if key not in conversations_map or m.timestamp > conversations_map[key].timestamp:
            conversations_map[key] = m
    
    conversations = []
    for (pid, ouid), last_msg in conversations_map.items():
        project = Project.objects.get(id=pid)
        other_user = CustomUser.objects.get(id=ouid)
        conversations.append({
            'project': project,
            'other_user': other_user,
            'last_message': last_msg
        })
        
    # Sort by last message timestamp
    conversations.sort(key=lambda x: x['last_message'].timestamp, reverse=True)

    return render(request, 'messages_list.html', {'conversations': conversations})
