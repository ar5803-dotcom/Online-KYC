from flask import Flask, render_template ,request, send_from_directory,Response,redirect,url_for,flash
import cv2
import os
import datetime
from flask import jsonify
import time
import requests
import fitz
import re
import warnings
from werkzeug.utils import secure_filename
import numpy as np
from deepface import DeepFace

import db
from flask_bootstrap import Bootstrap
from flask_wtf import FlaskForm 
from wtforms import StringField, PasswordField, BooleanField
from wtforms.validators import InputRequired, Email, Length
from flask_sqlalchemy  import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask import session

from supabase import create_client, Client
url = "Supabase URL here"
key = "Supabase API key"
supabase: Client = create_client(url, key)
from pyzbar.pyzbar import decode


app = Flask(__name__)
app.config["IMAGE_UPLOADS"] = r"D:\KYC-VERIFICATION\\"

app.config['SECRET_KEY'] = 'secretkey'


class LoginForm(FlaskForm):
    username = StringField('username', validators=[InputRequired(), Length(min=4, max=15)])
    password = PasswordField('password', validators=[InputRequired(), Length(min=6, max=80)])
    remember = BooleanField('remember me')

class RegisterForm(FlaskForm):
    email = StringField('email', validators=[InputRequired(), Email(message='Invalid email'), Length(max=50)])
    username = StringField('username', validators=[InputRequired(), Length(min=2, max=15)])
    password = PasswordField('password', validators=[InputRequired(), Length(min=6, max=80)])
    fname = StringField('first name', validators=[InputRequired(), Length(min=1)])
    lname = StringField('last name', validators=[InputRequired(), Length(min=1)])

@app.route('/')
def index():
    return render_template('home.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()

    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data

     
        data, count = supabase.table('user').select('*').eq('username', username).execute()
        user=data[1][0]
        print(user)

        if user:
            if check_password_hash(user['password'], password):
         
                session['user_id'] = user['id']
                session['username'] = user['username']
                session['email'] = user['email']
         
                session['fname'] = user['fname']
                session['lname'] = user['lname']
            
                flash('Logged in successfully!', 'success')
                return redirect(url_for('dashboard'))
            else:
                flash('Invalid username or password', 'error')
        else:
            flash('Invalid username or password', 'error')

    return render_template('login.html', form=form)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    form = RegisterForm()

    if form.validate_on_submit():
        hashed_password = generate_password_hash(form.password.data, method='pbkdf2:sha256')

        new_user_data = {
            'email': form.email.data,
            'password': hashed_password,
            'fname': form.fname.data,
            'lname': form.lname.data,
            'username': form.username.data
        }
        
        data, count = supabase.table('user').insert(new_user_data).execute()
        return redirect(url_for('login'))
            

    return render_template('signup.html', form=form)

@app.route('/dashboard')
def dashboard():
    if 'user_id' in session:

        user_id = session['user_id']
        username = session['username']
        email = session['email']
    
        fname = session['fname']
        lname = session['lname']

        return render_template('dashboard.html', fname=fname, lname=lname, uname=username, email=email)
    else:

        flash('Please log in to access the dashboard', 'error')
        return redirect(url_for('login'))




@app.route('/profile')
def profile():
    f=open(app.config["IMAGE_UPLOADS"]+'comparison_result.txt','r')
    st=f.read()
    stat='Not Verified'
    if st=='1':
        stat='Verified'
    print('status : ',stat)
    if 'user_id' in session:
        return render_template('profile.html',status=stat,password='******',fname=session['fname'],lname=session['lname'],uname=session['username'],email=session['email'])
    else:
        flash('Please log in to access the dashboard', 'error')
        return redirect(url_for('login'))

@app.route('/stp1')
def stp1():
    return render_template('stp1.html')

@app.route('/stp2')
def stp2():
    return render_template('stp2.html')

@app.route('/stp3')
def stp3():
    f=open(app.config["IMAGE_UPLOADS"]+'comparison_result.txt','r')
    res=f.read()
    print(res)
    print(type(res))
    if res=='0':
        return render_template('stp3.html',result=False,fname=session['fname'],lname=session['lname'])
    else:
        return render_template('stp3.html',result=True,fname=session['fname'],lname=session['lname'])

@app.route('/stp4')
def stp4():
    return render_template('stp4.html')

@app.route('/stp5')
def stp5():
     return render_template('stp5.html')


@app.route('/end')
def endpage():
    return render_template('end.html')


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))
   
@app.route("/upload-image", methods=["GET", "POST"])
def upload_image():
    dirname=''
    if request.method == "POST":
        if request.files:
            print("REQUEST FILES")
            image = request.files["image"]
            print("IMAGE")
            image.save(os.path.join(app.config["IMAGE_UPLOADS"]+'Uploads\\', image.filename))
            dirname=str(datetime.datetime.now())
            dirname=dirname.replace(':','')
            dirname=dirname.replace('-','')
            dirname=dirname.replace(' ','')
            newpath = r'D:\KYC-VERIFICATION\\imgdatabase'+str(dirname) +'\\Dataset'
            print(image.filename)
            if not os.path.exists(newpath):
                os.makedirs(newpath)
                print(image.filename) 
                formDirectImg(image.filename,dirname)  
    return render_template('stp2.html',dirname=dirname)


def formDirectImg(filename,dirname):
    print("OK NO PDF ONLY IMAGE")
    global count1
    count1=0
    image = cv2.imread(app.config["IMAGE_UPLOADS"] +'Uploads\\'+ filename)
    cv2.imwrite(f"D:\KYC-VERIFICATION\\imgdatabase{dirname}\\Dataset\\img0"+".png",image)
    print(filename,dirname)
    print("Image : ")

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    print(gray)

    faceCascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")

    faces = faceCascade.detectMultiScale(
            gray,
            scaleFactor=1.3,
            minNeighbors=3,
            minSize=(30, 30)
    )
    print("[INFO] Found {0} Faces.".format(len(faces)))
    padding = 30

    for (x, y, w, h) in faces:
        image = cv2.rectangle(image, (x-padding, y-padding),(x + w+padding, y + h+padding), (0, 255, 0), 2)
        roi_color = image[y-30:y + h+30, x-30:x + w+30]
        print("[INFO] Object found. Saving locally.")
 
        cv2.imwrite(f'D:\KYC-VERIFICATION\\imgdatabase{dirname}\\Dataset\\face'+str(count1)+'.jpg', roi_color)
        count1=count1+1
    status = cv2.imwrite('D:\KYC-VERIFICATION\\faces_detected.jpg', image)
    print("[INFO] Image faces_detected.jpg written to filesystem: ", status)
    return ''




@app.route('/opencamera',methods=['GET','POST'])    

def camera():
    dirname=request.form['dirname']
    t=int(1500)
    cam = cv2.VideoCapture(0)
    cv2.namedWindow("Test")
    count = 0
    while True and t:
        ret,img=cam.read()
        cv2.imshow("Test", img)
        cv2.waitKey(1)
        

        mins,secs=divmod(t,60)
		
        if(t==500 or t==1000):
            print("Image "+str(count)+" saved")
            cv2.imwrite(f'D:\KYC-VERIFICATION\\imgdatabase{dirname}\\Dataset\\cam{str(count)}.jpeg', img)
            count +=1
     
            
        time.sleep(0.01)
            
        t-=1
 
        if(t==0 and cv2.waitKey(1)):
            print("Close")
            break
    cam.release()
    cv2.destroyAllWindows() 
    compare(dirname)

    return redirect(url_for('stp3'))


def compare(dirname):
    print('Compare')
    global count1
    print('Count1 : ',count1)
    p=open('D:\KYC-VERIFICATION\\dirname.txt','w+')
    p.write(dirname)
    for j in range(2):
        print('Path1 '+str(j))
        path1=f'D:\KYC-VERIFICATION\\imgdatabase{dirname}\\Dataset\\cam'+str(j)+'.jpeg'
        for i in range(0,count1):
            print('Path2 '+str(i))
            try:
                path2=f'D:\KYC-VERIFICATION\\imgdatabase{dirname}\\Dataset\\face'+str(i)+'.jpg'
                print('Comparing image cam'+str(j)+' & face'+str(i))
                result = DeepFace.verify(img1_path =path1,img2_path =path2, model_name = "VGG-Face", distance_metric = "cosine")
                threshold = 0.10 
                print("Is verified: ", result["verified"])
                f=open('D:\KYC-VERIFICATION\\comparison_result.txt','w+')
                
                if result["verified"] == True:
                    f.write('1')
                    return ''
                else:
                    f.write('0')
            except Exception as e:
                print("An unexpected error occurred:", e)
    return ''


from pan_aadhar_ocr import Pan_Info_Extractor
import json
extractor = Pan_Info_Extractor()
@app.route('/scan-pan',methods=['GET','POST'])  
def scan_pan():
    print("HELLOO")
    f=open(app.config["IMAGE_UPLOADS"]+'dirname.txt','r')
    dirname=f.read()
    if request.method == "POST":
        print("REQUEST FILES")
        name1 = request.form["user_name"]
        uid1 = request.form["user_uid"]
    output=extractor.info_extractor(f"D:\KYC-VERIFICATION\\imgdatabase{dirname}\\Dataset\\img0.png")
    pan = json.loads(output)
    pan_no = pan["Pan_number"]
    print(f"{pan_no}=={uid1}")
    print(f"{type(pan_no)}=={type(uid1)}")
    print(f"{len(pan_no)}=={len(uid1)}")
    if uid1==pan_no:
            print("\nOCR Verifed\n")
            return render_template('stp5.html',result=True,fname=session["fname"],lname=session["lname"])
    else:
        print("\nOCR VERIFICATION NOT SUCCESSFULL\n")
  
    return render_template('stp5.html',result=False,fname=session["fname"],lname=session["lname"])



if __name__ == "__main__":
    app.run(debug=False)
