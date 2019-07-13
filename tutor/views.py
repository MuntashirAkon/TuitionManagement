from django.shortcuts import render
from django.http import HttpResponse


@tutor_required
def settings(request):
    if request.POST:
        email1 = request.POST['email1']
        email2 = request.POST['email2']
        phone = request.POST['phone']
        old_pass = request.POST['old_password']
        pass1 = request.POST['password1']
        pass2 = request.POST['password2']
        doc_type = request.POST['document_type']
        # TODO Implement settings
    else:
        return render(request, 'tutor/settings.html', context={
            'verified': False,
            'id_type': 'Student ID',
            'tutor_settings': 'active',
        })


@tutor_required
def apply(request, ad_id):
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
        ad = Ad.objects.filter(pk=ad_id, taken=False, timeout__gte=timezone.now())
        if ad.exists():
            return render(request, 'tutor/apply.html', context={'feed': get_feed(request, ad[0])})
        else:
            return redirect('tutor-feed')


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
        'verified': False,  # TODO
        'questions': ad.question_set,
        'answers': proposal[0].answer_set if proposal.exists() else False,
    }


def get_feed_list(request, ads):
    ad_list = []
    for ad in ads:
        ad_list.append(get_feed(request, ad))
    return ad_list
