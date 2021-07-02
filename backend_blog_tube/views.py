from django.shortcuts import render
from rest_framework.response import Response
from rest_framework.decorators import api_view,renderer_classes
from rest_framework.renderers import StaticHTMLRenderer
from .models import followings, users, blogs, comments,settings as users_settings,followers
from . import utils
import json,os,shutil
from django.conf import settings
from django.core.files.storage import FileSystemStorage


# Create your views here.

login_data = {}
session = ""


@api_view(['GET'])
def test(request ):
    print(request.GET['hii'])
    return Response({"name" : 'shouryaraj'})


@api_view(['POST']) 
def signup(request):
    global user ,otp_signup
    try:
        data = json.loads(request.headers['userData'])
        if utils.check_email(data['email']):
            uid = utils.generate_user_id()
            user = users( 
                user_id = uid ,
            user_name = data['username'],
            email = data['email'],
            password = utils.encode_fernet(data['password'])
            )

            image_path = os.path.join(os.getcwd(), "uploaded_media" , uid , 'profile')
            if not os.path.exists(image_path):
                os.makedirs(image_path)
            if len(request.FILES) != 0:
                fs =  FileSystemStorage(image_path)
                file = request.FILES['image']
                file_name  = file.name
                file_url = fs.save(f'{uid}_profile'+file_name[ (len(file_name)-(file_name[::-1].find("."))-1):], file)
                print(file_url)
                utils.image_resize(image_path , file_url)

            otp_signup = utils.generate_otp()
            utils.send_otp(otp_signup , data['username'], data['email'])
            print("sucess")
            return Response({'status': "otp"})
        
        else:
            return Response({'status':'exists'})
    except Exception as error :
        print(error)
        return Response({'status' : "fail"})

@api_view(['POST'])
def otp_validation(request):
    try:
        data = request.headers
        if (data['otp'] == otp_signup):
            user_id = user.user_id
            user.save()
            user.refresh_from_db()
            user_settings = users_settings(user_id = user)
            user_settings.save()
            user_follower = followers(user_id = user)
            user_follower.save()
            user_following = followings(user_id = user)
            user_following.save()
            return Response({'staus': "success"})
        else:
            print('fail OTP')
            image_path = os.path.join(os.getcwd(), "uploaded_media" , user.user_id )
            if os.path.exists(image_path):
                shutil.rmtree(os.path.join(settings.MEDIA_ROOT, user.user_id))
            return Response({'status' : "fail"})
    except Exception as e:
        print(e)
        return Response({'status' : "fail"})

@api_view(['POST'])
def login_validation(request):
    data = json.loads(request.headers['credentails'])
    global login_data , session
    
    try:
        user = users.objects.get(email = data['email'])
        password = utils.decode_fernet(user.password)
        if data['password'] == password:
            session = utils.create_session()
            login_data = {
                "user_id": user.user_id,
                "username": user.user_name,
                "email" : user.email,
                "encryp_pass":user.password
            }
            return Response( {'status': 'success' ,
            "login_data" : {
                "user_id": user.user_id,
                "username": user.user_name,
                "email" : user.email,
                "encryp_pass":user.password
            },
            "session":session } )
        else :
            return Response({"status" : "not_match"})
    except Exception as error:
        login_data = {}
        session = ""
        return Response({"status" : "fail"})

@api_view(['POST'])
def send_forgot_opt(request):
    try:
        global otp_forgot,user_forgot
        data = json.loads(request.headers['userdata'])
        email = data['email']


        if not utils.check_email(email):
            user_forgot = users.objects.get(email = data['email'])
            otp_forgot = utils.generate_otp()
            utils.send_otp(otp_forgot ,user_forgot.user_name , email , type = 'forgot_otp' )
            return Response({'status' : 'success'})
        else:
            return Response({'status': 'error'})
    except Exception as error:
        print(error)
        return Response({'status': 'error'})

@api_view(['POST'])
def validate_forgot_otp(request):
    try:
        otp = request.headers['otp']
        if otp == otp_forgot:
            return Response({'status' : 'success'})
        else:
            return Response({'status': 'fail'})
    except:
            return Response({'status': 'fail'})

@api_view(['POST'])
def change_password(request):
    try:
        new_pass = request.headers['newpass']
        
        users.objects.filter(user_id = user_forgot.user_id).update(password = utils.encode_fernet(new_pass))
        
        return Response({'status': 'success'})
    except Exception as error:
        print(error)
        return Response({'status' : 'fail'})

@api_view(['GET','POST'])
@renderer_classes([StaticHTMLRenderer])
def get_profile_photo(request):     #Must send user details for POST if unkown than userID unknown
    if request.method == 'GET':
        try:
            if request.GET['user_id'] == login_data['user_id']:
                user_id = request.GET['user_id']
        except:
            user_id = "unknown"
    if request.method == 'POST':
        if request.headers['session'] == session:
            user_details = login_data
        else: 
            user_details= {"user_id" : "unknown"}
        photo_uid = json.loads(request.headers['photouid'])
        photo_owner = users.objects.get(user_id = photo_uid)
        owner_settings = users_settings.objects.get(user_id = photo_uid)
        if user_details['user_id'] != 'unknown':
            if owner_settings.photo_to_follower :
                if utils.check_is_follower(user_details['user_id'], photo_uid):
                    user_id = photo_uid
                else:
                    user_id = 'unknown'
            else:
                user_id = "unknown"
        else:
            if owner_settings.photo_to_anonymus :
                user_id = photo_uid
            else : 
                user_id = "unknown"

    path =  utils.get_profile_photo_path(user_id)
    print(path)
    img = open(path , 'rb')
    img_data = img.read()
    type = "image/svg+xml" if path[-3 :]== "svg" else "image/*"
    return Response(img_data ,content_type= type )

@api_view(['GET'])
def user_list(request):
    try:
        all_users = users.objects.all()
        user_list = []
        for user in all_users:
            user_details = {}
            user_details['user_id'] = user.user_id
            user_details['user_name'] = user.user_name
            user_details['total_blogs'] = user.blogs_upload
            user_details['followers_count'] = len(json.loads(followers.objects.get(user_id  = user.user_id).followers))
            user_list.append(user_details)
        return Response({'status': 'success' , 'userslist': user_list} )
    except Exception as e:
        print(e)
        return Response({'status':'fail'})

@api_view(['POST'])
def logout_validation(request ):
    global session

    check_session = json.loads(request.headers['session'])
    if session == check_session:
        session = ""
        return Response({"status": "success"})
    else:
        return Response({'status' : 'fail'})

