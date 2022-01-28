from django.shortcuts import render,redirect
from elasticsearch import Elasticsearch
from .models import *
from .forms import * 
import os
from django.contrib.staticfiles.storage import staticfiles_storage
import cv2
import pytesseract as tess
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
#models used 
# Question -> id, text, image, upvote, downvote

# Create your views here.
def index(request):
    return render(request, "main/index.html")


# register user view
def registerUser(request):
    if request.user.is_authenticated:
        return  redirect('posts')
    else:

        form = UserCreationForm()
        if request.method =='POST':
            form = UserCreationForm(request.POST)
            if form.is_valid():
                form.save()

        context= {
            "form":form

        }
        return render(request,"main/register.html",context)

#login page view
def loginUser(request):
    
    if request.method =='POST':
        username= request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate (request,username=username,password=password)
        if user is not None :
            login(request,user)
            return redirect('posts')
    return render(request,"main/login.html")

#logout view 
def logoutUser(request):
    logout(request)

    return redirect('login')



# load specific posts

def particularPost(request,id):
    question = Question.objects.get(id=id)
    
    context={
        "question":question
    }
    return render(request, "main/particularPost.html",context)

    
    


# Posting question view 
@login_required(login_url='login')
def forum(request):
    text='' 
    imageocr =''
    image=''
    
    print("check")
    print(request.user)
    if request.method == 'POST':
        # get the data
        form = QuestionForm(request.POST,request.FILES)
        if form.is_valid():
            print("form valid")
            text=form.cleaned_data["text"]
            image = form.cleaned_data["image"]
            answer = form.cleaned_data["answer"]

        

            
    # First, count the total number of documents in the index in the elastic search
        es = Elasticsearch()
        number_of_items = es.count(index='question')['count'] # current total number of docs in the index
                                                              # count function returns a dictionary so take the count key item 

    # Second, update the models use the id from the total number of contents +1 
        number_of_items += 1
        #update the sql server
        # right now id =2 but after connecting elastic server you need to id= number_of_items
        obj = Question.objects.create(id=number_of_items,text=text,image=image,answer=answer)
        obj.save()
    # Third, update the data in the elastic server database
    # call the ocr function and get the string search data to be able to search
        filename=Question.objects.filter(id=number_of_items).values()
       # print("check")
        # if you don't use linux you need to add different format of the path below
        
        image=os.path.join('/mnt/c/Users/Dell/desktop/IOEOverflow/images',filename[0]['image']) # add the iamges path of your pc
       # print(image)
        imageocr= ocrcomp(image) 
        update_els_server(number_of_items,text,imageocr)
        

    form= QuestionForm()
    context={
            'form':form
            }

    return render(request,"main/forum.html",context)




def questionPost(request):
    questions = Question.objects.all().order_by('id')[:10].values() # Getting the required data from the models
    print(questions)
    return render(request,'main/posts.html',{
        'questions':questions
        }) #returning the template with the context
    
    
def search(request):
        form= SearchForm()
        text=''
        search_ids=[]
        question=[]

        if request.method =='POST':
            form = SearchForm(request.POST)
            if form.is_valid():
                text = form.cleaned_data['text']
        # elastic search using the given query
        #call a function
            search_ids = getID_ElasticSearch(text)
            for i in search_ids :
                data= Question.objects.filter(id=i).values()
                question.append(data)

            print(question)
        context={
                "search":form,
                "questions": question

                }
        




        return render(request,'main/search.html',context)


# function for ocr computation 
def ocrcomp(u_img):
    
   # tess.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
   ## for windows


              # function to convert iamge to text
    text = tess.image_to_string(u_img)
    return text

  


# dummy testing function for ocrcomp
def ocrcompdummy(u_img):
    return "hey everyone"
 #   return ocrcomp(u_img)

def update_els_server(id,text,image):
    es = Elasticsearch()
    doc ={
            'text':text,
            'image':image
            } 
    es.create(index='question',id=id,body=doc,doc_type='_doc')

def getID_ElasticSearch(text):
    es = Elasticsearch()
    indices=[]
    doc = {
    "query":{
        "multi_match":{
            
                    "query":text,
                    "fields":["text","image"],
                            "fuzziness": "AUTO"
                                  
            

        }

    }

    }
    data=es.search(index='question',body=doc)
    print(data)
    a= len(data['hits']['hits'])
    data=data['hits']['hits']
    for i in range(0,a):

        indices.append(data[i]['_id'])


    print(indices)
    return indices
    


def getID_ElasticSearch_Dummy(text):

    return [1,2]

