from django.http import HttpResponse
from django.contrib.auth import (
    authenticate,
    login as login_user,
    logout as logout_user
)
from users.models import User, Phone, Verification
from tuition.models import Ad
from django.contrib import messages
from django.shortcuts import render, redirect
from django.urls import reverse
from django.utils import timezone
from .decorators import client_required
from time import time


@client_required
def home(request):
    """Show only the ads posted by the client which are not timed out and not already taken"""
    return render(request, 'client/feed.html', context={
        'feed_list': get_feed_list(
            request,
            Ad.objects.filter(timeout__gte=timezone.now(), client=request.user, taken=False).order_by('-ad_time')
        ),
        'display_url': True,
        'client_home': 'active',
    })


@client_required
def view_applicants(request):
    # TODO: View applicants and hire them if needed
    pass


@client_required
def new(request):
    # TODO: Implement create new add
    pass


@client_required
def view_profile(request, profile_id):
    """View tutor profile"""
    # TODO: Implement tutor profile
    user = User.objects.filter(pk=profile_id, is_tutor=True)
    if user is not None:
        pass
    else:
        redirect('client-home')


@client_required
def history(request):
    # TODO: Implement history
    pass


@client_required
def running(request):
    """Show ads that are assigned by the client"""
    # TODO: Show running jobs, ability to end them here
    pass


@client_required
def settings(request):
    if request.POST:
        name = request.POST.get('full_name', '')
        bio = request.POST.get('bio', '')
        location = request.POST.get('location', '')
        gender = request.POST.get('gender', '')
        email1 = request.POST.get('email1', '')
        email2 = request.POST.get('email2', '')
        phone = request.POST.get('phone', '')
        old_pass = request.POST.get('old_password', '')
        pass1 = request.POST.get('password1', '')
        pass2 = request.POST.get('password2', '')
        doc_type = request.POST.get('document_type', '')
        user = User.objects.get(pk=request.user.pk)
        # Change name
        if name != '':
            user.name = name
        # Change bio
        if bio != '':
            user.bio = bio
        # Change location
        if location != '':
            user.location = location
        # Change gender
        if gender != '':
            if gender == 'male':
                user.gender = 'Male'
            elif gender == 'female':
                user.gender = 'Female'
        # Change password
        if old_pass != '':
            chk_user = authenticate(email=user.email, password=old_pass, is_active=True)
            if chk_user is not None:
                if pass1 == pass2 and pass1 != '':
                    user.set_password(pass1)
                else:
                    messages.error(request, 'Passwords do not match!')
                    return redirect(request.path_info)
            else:
                messages.error(request, 'Wrong password. Please try again.')
                return redirect(request.path_info)
        # Add email
        if email1 != '' and email1 == email2:
            if User.objects.filter(email=email1).exists():
                messages.error(request, 'Email already exists, please try with a new one.')
                return redirect(request.path_info)
            user.email = email1
        # Add phone
        if phone != '':
            if user.phone_set.exists():
                user.phone_set.update(phone_no=phone)
            else:
                user.phone_set.create(phone_no=phone)
        # Add verification info
        if request.FILES.get('verification_document', False) and doc_type != '':
            if user.verification_set.count():
                messages.error(request, 'Required file for verification is already uploaded.')
                return redirect(request.path_info)
            file_name = handle_verification_file(request.FILES['verification_document'])
            user.verification_set.create(type=doc_type, file=file_name)
        # Upload user photo
        if request.FILES.get('profile_img'):
            file_name = handle_profile_image(request.FILES['profile_img'])
            user.profile_img = file_name
        user.save()
        messages.success(request, 'Changes are saved successfully.')
        return redirect(request.path_info)
    else:
        user = User.objects.get(pk=request.user.pk)
        phone = Phone.objects.filter(user=user)
        verification = Verification.objects.filter(user=user)
        return render(request, 'client/settings.html', context={
            'verification': verification[0] if verification.exists() else False,
            'client_settings': 'active',
            'user': user,
            'phone': phone[0].phone_no if phone.exists() else False,
        })


@client_required
def logout(request):
    logout_user(request)
    messages.info(request, 'You\'ve been successfully logged out!')
    return redirect('home-page')


def login(request):
    email = request.POST['email']
    password = request.POST['password']
    user = authenticate(request, email=email, password=password, is_active=True)
    if user is not None:
        if user.is_client:
            login_user(request, user)
            return redirect('client-home')
        else:
            messages.error(request, 'Client not found, are you a tutor?')
            return redirect('{}?tab=client&email={}'.format(reverse('login-page'), email))
    else:
        messages.error(request, 'Invalid email or password! Please enter the right user credentials to login.')
        return redirect('{}?tab=client&email={}'.format(reverse('login-page'), email))


# Helper functions #


def get_feed(request, ad):
    return {
        'ad': ad,
        'pk': ad.pk,
        'title': ad.title,
        'description': ad.description,
        'grade': ad.grade,
        'type': ad.type,
        'subjects': ad.subjects,
        'salary': ad.salary,
        'gender': ad.gender,
        'std_count': ad.std_count,
        'days': ad.days,
        'time': ad.time,
        'location': ad.location,
        'client': ad.client,
        'proposals': ad.proposal_set.count(),
    }


def get_feed_list(request, ads):
    ad_list = []
    for ad in ads:
        ad_list.append(get_feed(request, ad))
    return ad_list


def handle_verification_file(f):
    file_name = 'file_{}_{}'.format(int(time()), f.name)
    with open('/Volumes/Fallout/v_files/{}'.format(file_name), 'wb+') as destination:
        for chunk in f.chunks():
            destination.write(chunk)
    return file_name


def handle_profile_image(f):
    file_name = 'file_{}_{}'.format(int(time()), f.name)
    with open('/Volumes/Fallout/Projects/TuitionManagament/TuitionMGMT/TuitionManagement/users/static/profile_imgs/{}'.format(file_name), 'wb+') as destination:
        for chunk in f.chunks():
            destination.write(chunk)
    return file_name
