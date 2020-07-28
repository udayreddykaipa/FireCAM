#import function is used to include libraries,
#before interpreting starts
import numpy as np
import cv2
import logging
import time
import smtplib
import firebase_admin # sudo pip install firebase-admin
from firebase_admin import credentials
from firebase_admin import db
from firebase_admin import auth
from firebase_admin import storage
from google.cloud import storage
#from threading import *
import threading
from datetime import datetime


global UID
global connflag
global fireflag
cred = credentials.Certificate('/home/pi/Desktop/major/cv-cam-firebase-adminsdk-o6qvt-d5c758eb05.json')
firebase_admin.initialize_app(cred, {
        'databaseURL': 'https://cv-cam.firebaseio.com',
        'storageBucket': 'cv-cam.appspot.com'
        })

def setup():
    fi = open("/home/pi/Desktop/major/config.json", "w+")
    print("Entering configuration menu:")
    Email=str(input("Enter Email name :"))
    pwd=str(input("Enter Password :"))
    fi.writelines(Email)     
    fi.close()
    try:
        user=firebase_admin.auth.create_user(email=Email,password=pwd)
    except:
        print("Failed create an user, Enter valid details or user exists")
        checkSetup()
        return 

    global UID
    UID=user.uid
    ref = db.reference('devices/'+UID)  #+'/value')#.value()
    ref.child("connection").set('0')
    ref.child("fire").set("0")
    ref.child("lastTS").set(datetime.now().strftime("%d-%b-%Y (%H:%M:%S.%f)"))
    #ref.child("deviceNumber").set('')
    ref.child("fireTS").set('')
    return

def checkSetup():
    
    try:
        fi = open("/home/pi/Desktop/major/config.json", "r")
        Email=fi.readline()
        print("User Exisits : "+Email)
        fi.close()
        print("would like enter setup (y/N)")
        
        x=str('N')
        if (x=='y' or x=='Y'):
            setup()
                
    except:
        print("NO json file found")
        setup()

    return 
      

def alertfun(msg):#alert on camera fail or disconnection
    li = ["m.phanisai007@gmail.com",
          "santhoshyadav09@gmail.com",
          "help.eceprojects@gmail.com"]
    #li is list of mail Id that gets alerts
    for i in range(len(li)): # iterate through all mail Ids
        s = smtplib.SMTP('smtp.gmail.com', 587) 
        s.starttls() 
        s.login("help.eceprojects@gmail.com", "vidyajyothi@03")
        #logins to a mailId (admin) to send mail
        
        sub="CCTV Alert !" #subject
        message = 'Subject: {}\n\n{}'.format(sub, msg)
        print(message)
        s.sendmail("help.eceprojects@gmail.com", li[i], message)
        s.quit()

def camConnCheck():
    print("camconncheck")
    global connflag
    if(connflag):
        flag="0"
    else:
        flag="1"
    ref = db.reference('devices/'+UID)  #+'/value')#.value()
    ref.child("connection").set(flag)
    time.sleep(10)
    camConnCheck()


def UploadImg():
    time.sleep(10)
    global UID
    bucket = firebase_admin.storage.bucket("cv-cam.appspot.com")
    imageBlob = bucket.blob(UID+'/profile.jpg')
    res=imageBlob.upload_from_filename(r'/home/pi/Desktop/major/profile.jpg')
    #upload_blob('profile.JPG','profile.jpg')
    print("uploaded")
    ref = db.reference('devices/'+UID)  #+'/value')#.value()
    ref.child("ImgTS").set(str(datetime.now()))
    time.sleep(110)
    UploadImg()

def uploadfireImg():
    global UID
    bucket = firebase_admin.storage.bucket("cv-cam.appspot.com")
    imageBlob = bucket.blob(UID+'/fire.jpg')
    res=imageBlob.upload_from_filename(r'/home/pi/Desktop/major/fire.jpg')
    #upload_blob('profile.JPG','profile.jpg')
    
def fireCheck():
    global UID
    global fireflag
    print("firecheck")
    if(fireflag):
        ref = db.reference('devices/'+UID)  #+'/value')#.value()
        ref.child("fire").set("1")
        ref = db.reference('devices/'+UID)  #+'/value')#.value()
        ref.child("fireTS").set(str(datetime.now()))
        uploadfireImg()
    else:
        ref = db.reference('devices/'+UID)  #+'/value')#.value()
        ref.child("fire").set("0")
        ref = db.reference('devices/'+UID)  #+'/value')#.value()
        ref.child("fireTS").set("Not Applicable")
    #algo

    #on fire detect update fireTS and fire
    
    fireCheck()

def LatestTS():
    print("lastTS")
    global UID
    ref = db.reference('devices/'+UID)  #+'/value')#.value()
    ref.child("lastTS").set(str(datetime.now()))
    time.sleep(60)
    LatestTS()

def algo():
    fire_cascade = cv2.CascadeClassifier('/home/pi/Desktop/major/fire_detection.xml')
    t=0
    t1=0
    t2=0
    cap = cv2.VideoCapture(0)
    while 1:
        if(cap.isOpened()==False):
            global connflag
            connflag=1
            if((datetime.now().minute-t2)>30):
                    t2=datetime.now().minute
                    msg = "FIRE DETECTED by CV - CCTV Camera !\n\n\nNOTE: This auto system generated mail on disconnection of computer vision camera";
                    alertfun(msg)# send mail
            #mail as well
        ret, img = cap.read()
        if not ret:
            print("no image")
            continue
        if((datetime.now().minute-t)>1):
            cv2.imwrite('profile.jpg',img)
            print("image saved")
            t=datetime.now().minute

        cv2.imshow('orignal Video',img)
        gray = cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)
        fire = fire_cascade.detectMultiScale(img, 1.2, 5)
        for (x,y,w,h) in fire:
            cv2.rectangle(img,(x,y),(x+w,y+h),(0,0,255),2)
            roi_gray = gray[y:y+h, x:x+w]
            roi_color = img[y:y+h, x:x+w]
            print ('Fire is detected..!')
            cv2.imwrite('fire.jpg',img)
            time.sleep(0.2)
            global fireflag
            fireflag=1
            if((datetime.now().minute-t1)>30):
                t1=datetime.now().minute
                msg = "FIRE DETECTED by CV Camera !\n\n\nNOTE: This auto system generated mail on disconnection of computer vision camera";
                alertfun(msg)# send mail
        #cv2.imshow('img',img)
        
        
        k = cv2.waitKey(30) & 0xff
        if k == 27:
            break

    cap.release()
    cv2.destroyAllWindows()



if __name__=="__main__":
    connflag=0
    fireflag=0
    checkSetup()
    fi = open("/home/pi/Desktop/major/config.json", "r")
    Email=str(fi.readline())
    fi.close()
    print("Programm started")
    global UID
    UID=firebase_admin.auth.get_user_by_email(Email).uid
    t1=threading.Thread(target=camConnCheck)
    ts=[t1]
    t2=threading.Thread(target=UploadImg)
    ts+=[t2]
    t3=threading.Thread(target=fireCheck)
    ts+=[t3]
    t4=threading.Thread(target=LatestTS)
    ts+=[t4]
    t5=threading.Thread(target=algo)
    ts+=[t5]
    t1.start()
    t2.start()
    t3.start()
    t4.start()
    t5.start()
    for i in ts:
        i.join()
    
    #use multi threading and create a thread to show active status in firebase and other to check fire and update in DB


#execution starts from here
# if __name__=="__main__":
#     checkSetup()
#     flag=0;
#     cap = cv2.VideoCapture(1)
#     while(flag==0):
#         if(cap.isOpened()==False):
#             print("Cam disconnected!")
#             flag=1
#             msg = "CV Camera disconnected!\n\n\nNOTE: This auto system generated mail on "+
#             "disconnection of computer vision camera";
#             alertfun(msg)#to send mail
#         else:
#             (grabbed, frame) = cap.read()
#             if not grabbed:
#                 print("no image")
#                 break
#             blur = cv2.GaussianBlur(frame, (21, 21), 0)
#             hsv = cv2.cvtColor(blur, cv2.COLOR_BGR2HSV)
#             cv2.imshow("output1", frame)
#             lower = [18, 50, 50]
#             upper = [35, 255, 255]
#             lower = np.array(lower, dtype="uint8")
#             upper = np.array(upper, dtype="uint8")
#             mask = cv2.inRange(hsv, lower, upper)
#             output = cv2.bitwise_and(frame, hsv, mask=mask)
#             no_red = cv2.countNonZero(mask)
#             cv2.imshow("output",output)
#             if int(no_red) > 1000:
#                 print ('Fire detected')
                
#                 flag=1
#                 msg = "FIRE DETECTED by CV Camera !\n\n\nNOTE: "
#                 "This auto system generated mail on disconnection of computer vision camera";
#                 alertfun(msg)# send mail
#             if cv2.waitKey(1) & 0xFF == ord('q'):
#                 break
 
# cv2.destroyAllWindows()
# cap.release()

# 
# def algo1():
#     cap = cv2.VideoCapture(0)
#     t=0
#     t1=0
#     t2=0
#     print("algo")
#     while(True):
#         if(cap.isOpened()==False):
#             global connflag
#             connflag=1
#             if((datetime.now().minute-t2)>30):
#                     t2=datetime.now().minute
#                     msg = "FIRE DETECTED by CV Camera !\n\n\nNOTE: This auto system generated mail on disconnection of computer vision camera";
#                     alertfun(msg)# send mail
#             #mail as well
#         else:
#             (grabbed, frame) = cap.read()
#             cv2.imshow("original",frame)
#             if not grabbed:
#                 print("no image")
#                 continue
#             if((datetime.now().minute-t)>1):
#                 cv2.imwrite('profile.jpg',frame)
#                 print("image saved")
#                 t=datetime.now().minute
#             blur = cv2.GaussianBlur(frame, (21, 21), 0)
#             hsv = cv2.cvtColor(blur, cv2.COLOR_BGR2HSV)
#             lower = [18, 50, 50]
#             upper = [35, 255, 255]
#             lower = np.array(lower, dtype="uint8")
#             upper = np.array(upper, dtype="uint8")
#             mask = cv2.inRange(hsv, lower, upper)
#             output = cv2.bitwise_and(frame, hsv, mask=mask)
#             no_red = cv2.countNonZero(mask)
#             cv2.imshow("output",output)
#             if int(no_red) > 1000:
#                 print ('Fire detected')
#                 global fireflag
#                 fireflag=1
#                 if((datetime.now().minute-t1)>30):
#                     t1=datetime.now().minute
#                     msg = "FIRE DETECTED by CV Camera !\n\n\nNOTE: This auto system generated mail on disconnection of computer vision camera";
#                     alertfun(msg)# send mail
#                 
#             if cv2.waitKey(1) & 0xFF == ord('q'):
#                 return 
#     
#     cv2.destroyAllWindows()
#     cap.release()
