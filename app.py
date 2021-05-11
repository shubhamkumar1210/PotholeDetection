# python app.py --model model/yolov3.weights --config model/yolov3_custom.cfg --names model/obj.names


from flask import Flask, render_template, request, url_for, redirect, make_response, session
import cv2
import numpy as np
from detect import detect, resize
import argparse
import os
from PIL import Image
import sqlite3
from base64 import b64encode

parser = argparse.ArgumentParser()
parser.add_argument("-m", "--model", required=True, help="Path To Model")
parser.add_argument("-cf", "--config", required=True, help="Path To Config File")
parser.add_argument("-n", "--names", required=True, help="Path To Names of Object")
parser.add_argument("-c", "--confidence", default=0.5, help="Minimum confidence", type=float)
parser.add_argument("-t", "--thresh", default=0.3, help="Threshold", type=float)
args = vars(parser.parse_args())

sq = '''DROP TABLE user'''
sq3 = '''DROP TABLE pothole_table'''

sql = '''CREATE TABLE IF NOT EXISTS pothole_table(
        FLAG TEXT NOT NULL,
        IDS TEXT NOT NULL,
	NAME TEXT NOT NULL,
	LOCATION TEXT NOT NULL,
	DESCRIPTION TEXT NOT NULL,
	PHOTO BLOB NOT NULL
)'''

sql2 = '''CREATE TABLE IF NOT EXISTS user(
	username TEXT NOT NULL,
	email TEXT NOT NULL,
	password TEXT NOT NULL,
    mobile TEXT NOT NULL
)'''

conn = sqlite3.connect("records/pothole.db")
cursor = conn.cursor()
# cursor.execute(sq)
# cursor.execute(sq3)
cursor.execute(sql)
cursor.execute(sql2)
conn.commit()
cursor.close()
conn.close()


labelPaths = args["names"]


def convertToBinaryData(filename):
    # Convert digital data to binary format
    with open(filename, 'rb') as file:
        blobData = file.read()
    return blobData


Labels = open(labelPaths).read().strip().split("\n")
np.random.seed(15)
colors = np.random.randint(0, 255, size=(len(Labels), 3), dtype="uint8")

weightsPath = args["model"]
configPath = args["config"]

net = cv2.dnn.readNetFromDarknet(configPath, weightsPath)

ln = net.getLayerNames()
ln = [ln[i[0] - 1] for i in net.getUnconnectedOutLayers()]

app = Flask(__name__)
app.config["CACHE_TYPE"] = "null"
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 1

app.config['imgdir'] = os.path.sep.join(['static', 'upload', 'images'])

# app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0 


# prevent cached responses
@app.after_request
def add_header(response):
    """
    Add headers to both force latest IE rendering engine or Chrome Frame,
    and also to cache the rendered page for 10 minutes.
    """
    response.headers['X-UA-Compatible'] = 'IE=Edge,chrome=1'
    response.headers['Cache-Control'] = 'public, max-age=0'
    return response


@app.route("/")
def charts():
    return render_template("charts.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        passw = request.form["passw"]

        conn = sqlite3.connect("records/pothole.db")
        cursor = conn.cursor()
        params = (email, passw)
        cursor.execute(
            "SELECT * FROM user WHERE email=? and password=?", params)
        login = cursor.fetchall()
        if email == "admin@mail.com" and passw == "admin123":
            session['email'] = email
            return redirect(url_for("adminprofile"))
        elif not login:
            return render_template("login.html", invalidMsg="Invalid Credentials.")
        else:
            session['email'] = email
            return redirect(url_for("profile"))
    else:
        return render_template("login.html")


@app.route("/adminprofile", methods=["GET", "POST"])
def adminprofile():
    conn = sqlite3.connect("records/pothole.db")
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM pothole_table")
    my_list = cursor.fetchall()

    data1 = []
    for i in range(len(my_list)):
        a = []
        for j in range(len(my_list[0])):
            a.append(my_list[i][j])
        data1.append(a)
        
        cursor.execute("SELECT COUNT(*) FROM pothole_table WHERE FLAG = 1")
        my_list1 = cursor.fetchall()

        data3 = []
        for i in range(len(my_list1)):
            a = []
            for j in range(len(my_list1[0])):
                a.append(my_list1[i][j])
            data3.append(a)
            
        cursor.close()
        conn.close()        
    return render_template("adminprofile.html",data1=data1,data3=data3)


@app.route("/profile", methods=["GET", "POST"])
def profile():
    if 'email' in session:
        name = session['email']
        conn = sqlite3.connect("records/pothole.db")
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM pothole_table WHERE NAME =(?)",[name])
        my_list = cursor.fetchall()

        data1 = []
        for i in range(len(my_list)):
            a = []
            for j in range(len(my_list[0])):
                a.append(my_list[i][j])
            data1.append(a)

        cursor.execute("SELECT COUNT(*) FROM pothole_table WHERE NAME =(?) AND FLAG = 1",[name])
        my_list1 = cursor.fetchall()

        data3 = []
        for i in range(len(my_list1)):
            a = []
            for j in range(len(my_list1[0])):
                a.append(my_list1[i][j])
            data3.append(a)
            
        cursor.close()
        conn.close()
        
        conn = sqlite3.connect("records/pothole.db")
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM user WHERE email =(?)",[name])
        my_lists = cursor.fetchall()
        
        data2 = []
        for i in range(len(my_lists)):
            a = []
            for j in range(len(my_lists[0])):
                a.append(my_lists[i][j])
            data2.append(a)    
        cursor.close()
        conn.close()
        
        return render_template("profile.html",data1=data1[0][0],data2=data2, data3=data3[0][0])
    else:
        return redirect(url_for("charts"))



@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        uname = request.form['uname'] 
        email = request.form['email']
        passw = request.form['passw']
        mobile = request.form['mobile']
        
        conn = sqlite3.connect("records/pothole.db")
        cursor = conn.cursor()
        params = (uname, email, passw, mobile)
        cursor.execute("SELECT COUNT(*) FROM user WHERE email = (?) AND mobile = (?)", [email, mobile])
        my_list = cursor.fetchall()
        
        list1 = list(my_list[0])
        
        conn.commit()
        cursor.close()
        conn.close()
        
        if int(list1[0]) >= 1:
            
            return render_template("register.html", msg="Email or Phone already exists. Use another email or phone.")
        
        else:

            conn = sqlite3.connect("records/pothole.db")
            cursor = conn.cursor()
            params = (uname, email, passw, mobile)
            cursor.execute("INSERT INTO user VALUES(?, ?, ?, ?)", params)

            conn.commit()
            cursor.close()
            conn.close()

            return render_template("login.html", msg="Successfully Registered.")
    return render_template("register.html")


@app.route('/admin', methods=['POST', "GET"])
def admin():
    if 'email' in session:
        try:
            conn = sqlite3.connect("records/pothole.db")
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM pothole_table")
            my_list = cursor.fetchall()

            data1 = []
            for i in range(len(my_list)):
                a = []
                for j in range(len(my_list[0])):
                    a.append(my_list[i][j])
                data1.append(a)

            for i in range(len(data1)):
                data1[i][-1] = b64encode(data1[i][-1]).decode("utf-8")

        except Exception as e:
            print(e)
        return render_template('adminDashboard.html', data1=data1, len=len(data1))
    else:
        return redirect(url_for("login"))


@app.route('/repair')
def repair():
    if 'email' in session:
        ids = request.args['id']
        ids = str(ids)
        conn = sqlite3.connect("records/pothole.db")
        cursor = conn.cursor()
        cursor.execute("UPDATE pothole_table SET FLAG = 1 WHERE IDS = (?)", [ids])
        conn.commit()
        cursor.close()
        conn.close()
        return redirect(url_for("admin"))
    else:
        return redirect(url_for("charts"))


@app.route('/delete')
def delete():
    if 'email' in session:
        ids = request.args['id']
        ids = str(ids)
        print(ids)
        conn = sqlite3.connect("records/pothole.db")
        cursor = conn.cursor()
        cursor.execute("DELETE FROM pothole_table WHERE IDS = (?)", [ids])
        conn.commit()
        cursor.close()
        conn.close()
        return redirect(url_for("admin"))
    else:
        return redirect(url_for("charts"))


@app.route('/revert')
def revert():
    if 'email' in session:
        ids = request.args['id']
        ids = str(ids)
        conn = sqlite3.connect("records/pothole.db")
        cursor = conn.cursor()
        cursor.execute("UPDATE pothole_table SET FLAG = 0 WHERE IDS = (?)", [ids])
        conn.commit()
        cursor.close()
        conn.close()
        return redirect(url_for("admin"))
    else:
        return redirect(url_for("charts"))


@app.route('/dashboard')
def index():
    if 'email' in session:
        return render_template('index.html')
    else:
        return redirect(url_for("charts"))


@app.route('/main', methods=['POST', "GET"])
def main():
    if 'email' in session:
        if request.method == 'POST':
            try:
                file = request.files.get("img","")
                file.save(os.path.join(app.config["imgdir"], file.filename))

                image = cv2.imread(os.path.join(app.config["imgdir"],file.filename))

                image = resize(image, width=600)
                drawed, coords = detect(image.copy(), net, ln, Labels, colors, return_cords=True)
                store = True
                no_of_pothole = str(len(coords))+" Problem(s) Found"
                if len(coords) == 0:
                    store = False
                    msg = "No Problem(s) Found.Please upload a proper picture."
                file_path = os.path.join("static", "img.png")
                if os.path.isfile(file_path):
                    os.remove(file_path)
                cv2.imwrite(file_path, drawed.copy())
                if len(coords) == 0:
                    return render_template("index.html", msg=msg, file=file_path, no_of_pothole=no_of_pothole)
                else:
                    return render_template("index.html", file=file_path, no_of_pothole=no_of_pothole)
            except Exception as e:
                print(e)
                result = ('Please pass proper input :'+ str(e) , 2 )
                return render_template('index.html', msg= result)
        return render_template("index.html")
    else:
        return redirect(url_for("charts"))


@app.route("/store", methods=['POST', 'GET'])
def store():
    if 'email' in session:
        conn = sqlite3.connect("records/pothole.db")
        name = session['email']
        desc = request.form['desc']
        location = request.form['location']
        print(location)
        blobData = convertToBinaryData("static/img.png")

        conn = sqlite3.connect("records/pothole.db")
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM pothole_table")
        my_list = cursor.fetchall()
        data1 = []
        for i in range(len(my_list)):
            a = []
            for j in range(len(my_list[0])):
                a.append(my_list[i][j])
            data1.append(a)

        for i in range(len(data1)):
            data1[i][-1] = b64encode(data1[i][-1]).decode("utf-8")

        ids = len(data1)+1
        flag = 0

        sqlite_insert_blob_query = "INSERT INTO pothole_table (FLAG, IDS, NAME, LOCATION, DESCRIPTION, PHOTO) VALUES (?, ?, ?, ?, ?, ?)"
        data_tuple = (flag, ids, name, location, desc, blobData)
        cursor.execute(sqlite_insert_blob_query, data_tuple)

        conn.commit()
        cursor.close()
        conn.close()

        file_path = os.path.join("static", "img.png")
        return render_template("index.html", file=file_path, msg='Stored Successfully')
    else:
        return redirect(url_for("charts"))


@app.route('/show', methods=['POST', "GET"])
def show():
    if 'email' in session:
        try:
            conn = sqlite3.connect("records/pothole.db")
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM pothole_table")
            my_list = cursor.fetchall()

            data1 = []
            for i in range(len(my_list)):
                a = []
                for j in range(len(my_list[0])):
                    a.append(my_list[i][j])
                data1.append(a)

            for i in range(len(data1)):
                data1[i][-1] = b64encode(data1[i][-1]).decode("utf-8")

        except Exception as e:
            print(e)
        return render_template('show.html', data1=data1, len=len(data1))
    else:
        return redirect(url_for("charts"))
        

@app.route('/showMyComplaint', methods=['POST', "GET"])
def showMyComplaint():
    if 'email' in session:
        data1 = []
        try:
            name = session['email']
            conn = sqlite3.connect("records/pothole.db")
            cursor = conn.cursor()
            name = str(name)
            cursor.execute("SELECT * FROM pothole_table WHERE NAME= (?)",[name])
            my_list = cursor.fetchall()
            
            print(my_list)

            data1 = []
            for i in range(len(my_list)):
                a = []
                for j in range(len(my_list[0])):
                    a.append(my_list[i][j])
                data1.append(a)

            for i in range(len(data1)):
                data1[i][-1] = b64encode(data1[i][-1]).decode("utf-8")
                
            return render_template('showMyComplaint.html', data1=data1, len=len(data1))

        except Exception as e:
            print(e)
            return render_template('showMyComplaint.html', data1=data1, len=len(data1))
    else:
        return redirect(url_for("charts"))


@app.route('/logout', methods=['POST', "GET"])
def logout():
    if 'email' in session:
        session.pop('email', None)
        return redirect(url_for("login"))
    else:
        return redirect(url_for("charts"))


if __name__ == "__main__":
    app.secret_key = 'A0Zr98j/3yX R~XHH!jmN]LWX/,?RT'
    app.run(debug=True)
