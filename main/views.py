from django.shortcuts import get_object_or_404, render, redirect
from elasticsearch import Elasticsearch
from .models import *
from .forms import *
import os
from django.contrib.staticfiles.storage import staticfiles_storage
import pytesseract as tess
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.urls import reverse
# models used
# Question -> id, text, image, upvote, downvote

# Create your views here.


def index(request):
    return render(request, "main/index.html")


# register user view
def registerUser(request):
    if request.user.is_authenticated:
        return redirect('posts')
    else:

        form = UserCreationForm()
        if request.method == 'POST':
            form = UserCreationForm(request.POST)
            if form.is_valid():
                form.save()

        context = {
            "form": form

        }
        return render(request, "main/register.html", context)

# login page view


def loginUser(request):
    if request.user.is_authenticated:
        return redirect('posts')
    else:
        if request.method == 'POST':
            username = request.POST.get('username')
            password = request.POST.get('password')
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('posts')
        return render(request, "main/login.html")

# logout view


def logoutUser(request):
    logout(request)

    return redirect('login')


# load specific posts


def particularPost(request, id):
    post = get_object_or_404(Question, id=id)

    # can manually deactivate the donkey comments

    comments = post.comments.filter(active=True)
    new_comment = None

    if request.method == "POST":
        comment_form = CommentForm(data=request.POST)

        if comment_form.is_valid():
            # Create Comment object but don't save to database yet
            new_comment = comment_form.save(commit=False)
            # Assign the current post to the comment
            new_comment.post = post
            # save the comment to database
            new_comment.save()

    else:
        comment_form = CommentForm()

    context = {
        "question": post,
        "comments": comments,
        "new_comment": new_comment,
        "comment_form": comment_form
    }
    return render(request, "main/particularPost.html", context)

# comment section view


def delete_post(request):

    post = get_object_or_404(Question, id=request.POST.get('delete'))
    context = {}
    if request.user.username == post.author:
        #delete = post.id
        deleteElasticSearchEntry(post.id)
        post.delete()
        return redirect('posts')
        # return redirect('particularPost', post.id)
    else:
        delete = "You are not the author."
        context = {
            "deleted": delete
        }
        return render(request, "main/delete.html", context)


# Posting question view
@login_required(login_url='login')
def forum(request):
    text = ''
    imageocr = ''
    image = ''

    if request.method == 'POST':
        # get the data
        form = QuestionForm(request.POST, request.FILES)
        user = request.user.get_username()
        if form.is_valid():
            print("form valid")
            text = form.cleaned_data["text"]
            image = form.cleaned_data["image"]
            answer = form.cleaned_data["answer"]

        number_of_items = TotalEntries.objects.all()[0].value

    # Second, update the models use the id from the total number of contents +1
        number_of_items += 1
        # update the sql server
        # right now id =2 but after connecting elastic server you need to id= number_of_items
        obj = Question.objects.create(
            id=number_of_items, text=text, image=image, answer=answer, author=user)
        obj.save()
    # Third, update the data in the elastic server database
    # call the ocr function and get the string search data to be able to search
        filename = Question.objects.filter(id=number_of_items).values()
       # print("check")
        # if you don't use linux you need to add different format of the path below
## Prayash Laptop
     #   image = os.path.join('/mnt/c/Users/Dell/desktop/IOEOverflow/images',
        #                     filename[0]['image'])  # add the iamges path of your pc
    ## Prayash desktop
        image = os.path.join('/mnt/c/Users/User/desktop/IOEOverflow/images',
                             filename[0]['image'])  # add the iamges path of your pc
       # print(image)
        imageocr = ocrcomp(image)
        update_els_server(number_of_items, text, imageocr)
        newnumber = TotalEntries.objects.all()[0]
        newnumber.value = number_of_items
        newnumber.save()
    form = QuestionForm()
    context = {
        'form': form
    }

    return render(request, "main/forum.html", context)


def questionPost(request):
    # Getting the required data from the models
    questions = Question.objects.all().order_by('id')[:10].values()
    print(questions)
    return render(request, 'main/posts.html', {
        'questions': questions
    })  # returning the template with the context

# this is the function that handles user upvote the user needs to be logged in inorder to use this


@login_required(login_url="login")
def upvote_increment(request, id):
    user = request.user
    question = Question.objects.get(id=id)
    # extract the list of upvoters
    upvoters = question.upvoteList.all()
    downvoters = question.downvoteList.all()
    flag = 0
    for upvoter in upvoters:
        if upvoter == user:
            flag = 1
            break
    if flag == 0:

        # append the user to the upvotelist and increment upvote
        ##Coding remaining##
        question.upvoteList.add(user)
        c = question.upvote
        c += 1
        question.upvote = c
        for downvoter in downvoters:
            if downvoter == user:

                question.downvoteList.remove(user)
                count = question.downvote
                count = count-1
                question.downvote = count
        question.save()
    return redirect('particularPost', id)

# Make a similar function for downvote


@login_required(login_url="login")
def downvote_increment(request, id):
    user = request.user
    question = Question.objects.get(id=id)
    # extract the list of downvoters
    downvoters = question.downvoteList.all()
    upvoters = question.upvoteList.all()
    flag = 0
    for downvoter in downvoters:
        if downvoter == user:
            flag = 1
            break
    if flag == 0:

        # append the user to the downvotelist and increment downvote
        ##Coding remaining##
        question.downvoteList.add(user)
        c = question.downvote
        c += 1
        question.downvote = c
        # check if the user is in upvoter if so remove him from upvoter
        for upvoter in upvoters:
            if upvoter == user:

                question.upvoteList.remove(user)
                count = question.upvote
                count = count-1
                question.upvote = count
        question.save()

    return redirect('particularPost', id)


def search(request):
    form = SearchForm()
    text = ''
    search_ids = []
    question = []

    if request.method == 'POST':
        form = SearchForm(request.POST)
        if form.is_valid():
            text = form.cleaned_data['text']
    # elastic search using the given query
    # call a function
        search_ids = getID_ElasticSearch(text)
        for i in search_ids:
            data = Question.objects.filter(id=i).values()
            question.append(data)

    context = {
        "search": form,
        "questions": question

    }

    return render(request, 'main/search.html', context)


# function for ocr computation
def ocrcomp(u_img):

   # tess.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
   # for windows

    # function to convert iamge to text
    text = tess.image_to_string(u_img)
    return text


# dummy testing function for ocrcomp
def ocrcompdummy(u_img):
    return "hey everyone"
 #   return ocrcomp(u_img)


def update_els_server(id, text, image):
    es = Elasticsearch()
    doc = {
        'text': text,
        'image': image
    }
    es.create(index='question', id=id, body=doc, doc_type='_doc')


def getID_ElasticSearch(text):
    es = Elasticsearch()
    indices = []
    doc = {
        "query": {
            "multi_match": {

                "query": text,
                "fields": ["text", "image"],
               
                "fuzziness": "AUTO"



            }

        }

    }
    data = es.search(index='question', body=doc)

    a = len(data['hits']['hits'])
    data = data['hits']['hits']
    for i in range(0, a):

        indices.append(data[i]['_id'])

    print(indices)
    return indices


def freshStart(request):
    number = TotalEntries.objects.all()[0]
    number.value = 0
    number.save()

    return HttpResponse('sucess')
# dummy function for testing only


def getID_ElasticSearch_Dummy(text):

    return [1, 2]
# This function deletes the respective entry in elastic search pass the id of the entry you want to delete
# This function is not yet tested by likely runs properly


def deleteElasticSearchEntry(id):
    es = Elasticsearch()
    es.delete(index='question', id=id, doc_type='_doc')
    return
