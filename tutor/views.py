from django.shortcuts import render, redirect
from users.models import User, Verification, Phone
from tuition.models import Ad, Assignee, Proposal, Question, Answer
from django.utils import timezone
from django.contrib.auth import (
    logout as logout_user,
    login as login_user,
    authenticate,
)
from django.contrib import messages
from django.urls import reverse
from .decorators import tutor_required
from time import time
import os


@tutor_required
def feed(request):
    if is_profile_incomplete(request):
        messages.info(request, 'Your profile is incomplete. Please fill out all the fields to get started.')
        return redirect('tutor-edit-profile', request.user.pk)
    ads = Ad.objects.filter(timeout__gte=timezone.now(), taken=False).exclude(client=request.user).order_by('-ad_time')
    return render(request, 'tutor/feed.html', context={
        'feed_list': get_feed_list(request, ads),
        'display_url': True,
        'tutor_feed': 'active',
    })


@tutor_required
def view_profile(request, profile_id):
    """View user or client profile"""
    if request.user.pk == profile_id:
        if is_profile_incomplete(request):
            messages.info(request, 'Your profile is incomplete. Please fill out all the fields to get started.')
            return redirect('tutor-edit-profile', request.user.pk)
        user = User.objects.get(pk=profile_id)
        work_history = Assignee.objects.filter(tutor=request.user, to_date__lte=timezone.now())
        return render(request, 'tutor/view_profile.html', context={
            'profile': user,
            'education': user.education_set.all().order_by('-to_year'),
            'work_history': work_history,
            'tutor_profile': 'active',
            'editable': True,
            'profile_img': os.path.basename(user.profile_img),
        })
    else:
        user = User.objects.filter(pk=profile_id, is_client=True)
        if user.exists():
            work_history = Ad.objects.filter(client=user[0], taken=True)
            return render(request, 'tutor/client_profile.html', context={
                'profile': user[0],
                'work_history': work_history,
                'profile_img': os.path.basename(user.profile_img),
            })
        else:
            return redirect('tutor-profile', request.user.pk)


@tutor_required
def edit_profile(request, profile_id):
    if request.POST:
        # TODO: Handle edit profile
        pass
    else:
        if request.user.pk == profile_id:
            user = User.objects.get(pk=profile_id)
            return render(request, 'tutor/edit_profile.html', context={
                'profile': user,
                'education': user.education_set.all().order_by('-to_year'),
                'tutor_profile': 'active',
            })
        else:
            return redirect('tutor-profile', profile_id)


@tutor_required
def history(request):
    # TODO: show feedback for archived history
    # FIXME: There may be duplicate values
    archived_list = []
    archived_jobs = Assignee.objects.filter(tutor=request.user, to_date__lte=timezone.now())
    for obj in archived_jobs:
        archived_list.append(obj.ad)
    active_list = []
    active_jobs = Assignee.objects.filter(tutor=request.user, to_date__gt=timezone.now())
    for obj in active_jobs:
        active_list.append(obj.ad)
    active_jobs = Assignee.objects.filter(tutor=request.user, to_date__isnull=True)
    for obj in active_jobs:
        active_list.append(obj.ad)
    proposed = Proposal.objects.filter(tutor=request.user)
    for obj in proposed:
        if obj.ad.timeout >= timezone.now():
            active_list.append(obj.ad)
        else:
            archived_list.append(obj.ad)

    return render(request, 'tutor/history.html', context={
        'feed_active': {'list': get_feed_list(request, active_list), 'count': len(active_list)},
        'feed_archive': {'list': get_feed_list(request, archived_list), 'count': len(archived_list)},
        'tutor_history': 'active',
    })


@tutor_required
def settings(request):
    if request.POST:
        email1 = request.POST.get('email1', '')
        email2 = request.POST.get('email2', '')
        phone = request.POST.get('phone', '')
        old_pass = request.POST.get('old_password', '')
        pass1 = request.POST.get('password1', '')
        pass2 = request.POST.get('password2', '')
        doc_type = request.POST.get('document_type', '')
        user = User.objects.get(pk=request.user.pk)
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
        if request.FILES and doc_type != '':
            if user.verification_set.count():
                messages.error(request, 'Required file for verification is already uploaded.')
                return redirect(request.path_info)
            file_name = handle_verification_file(request.FILES['verification_document'])
            user.verification_set.create(type=doc_type, file=file_name)
        user.save()
        messages.success(request, 'Changes are saved successfully.')
        return redirect(request.path_info)
    else:
        user = User.objects.get(pk=request.user.pk)
        phone = Phone.objects.filter(user=user)
        verification = Verification.objects.filter(user=user)
        return render(request, 'tutor/settings.html', context={
            'verification': verification[0] if verification.exists() else False,
            'tutor_settings': 'active',
            'email': user.email,
            'phone': phone[0].phone_no if phone.exists() else False,
        })


@tutor_required
def apply(request, ad_id):
    ad = Ad.objects.filter(pk=ad_id, taken=False, timeout__gte=timezone.now()).exclude(client=request.user)
    if not ad.exists():
        return redirect('tutor-feed')

    if request.POST:
        proposal = request.POST.get('proposal', '')  # Optional
        # Check if already has a proposal
        if Proposal.objects.filter(ad_id=ad_id, tutor=request.user).exists():
            messages.error(request, 'You\'ve already submitted a proposal for this ad.')
            return redirect(request.path_info)
        # Add the newly added proposal
        prop = Proposal.objects.create(ad_id=ad_id, tutor=request.user, proposal=proposal)
        # Add answers
        questions = Question.objects.filter(ad_id=ad_id)
        for question in questions:
            answer = request.POST.get('q_{}'.format(question.pk))
            Answer.objects.create(question=question, proposal=prop, answer=answer)
        messages.success(request, 'Successfully applied!')
        return redirect(request.path_info)
    else:
        return render(request, 'tutor/apply.html', context={'feed': get_feed(request, ad[0])})


@tutor_required
def logout(request):
    logout_user(request)
    messages.info(request, 'You\'ve been successfully logged out!')
    return redirect('home-page')


def login(request):
    email = request.POST['email']
    password = request.POST['password']
    user = authenticate(request, email=email, password=password, is_active=True)
    if user is not None:
        if user.is_tutor:
            login_user(request, user)
            return redirect('tutor-home')
        else:
            messages.error(request, 'Tutor not found, are you a client?')
            return redirect('{}?tab=tutor&email={}'.format(reverse('login-page'), email))
    else:
        messages.error(request, 'Invalid email or password! Please enter the right user credentials to login.')
        return redirect('{}?tab=tutor&email={}'.format(reverse('login-page'), email))


# Helper functions #


def get_feed(request, ad):
    proposal = ad.proposal_set.filter(tutor=request.user)
    return {
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
        'already_applied': proposal.exists(),
        'proposal': proposal[0].proposal if proposal.exists() else False,
        'questions': ad.question_set,
        'answers': proposal[0].answer_set if proposal.exists() else False,
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


def is_profile_incomplete(request):
    user = User.objects.get(pk=request.user.pk)
    if user.name == '' or user.bio == '' or user.location == '' or user.gender == '' or user.title == ''\
            or user.overview == '' or user.expertise == '' or user.profile_img == '':
        return True
    return False


def handle_profile_image(f):
    file_name = 'file_{}_{}'.format(int(time()), f.name)
    with open('/Volumes/Fallout/Projects/TuitionManagament/TuitionMGMT/TuitionManagement/users/static/profile_imgs/{}'.format(file_name), 'wb+') as destination:
        for chunk in f.chunks():
            destination.write(chunk)
    return file_name
