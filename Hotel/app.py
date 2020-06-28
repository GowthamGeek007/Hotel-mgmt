from flask import Flask, render_template, flash, redirect, url_for, session, logging, request
import mysql.connector
from mysql.connector import Error
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from passlib.hash import sha256_crypt
from flask_googlemaps import GoogleMaps



app = Flask(__name__)

# GoogleMaps(app)
# app.config['GOOGLEMAPS_KEY'] = "8JZ7i18MjFuM35dJHq70n3Hx4"
# GoogleMaps(app, key="8JZ7i18MjFuM35dJHq70n3Hx4")


connection = mysql.connector.connect(host='localhost',
                             database='hotel',
                             user='root',
                             password='')


@app.route('/home')
def index():
    cur=connection.cursor()
    cur.execute("SELECT * FROM room LEFT JOIN room_type ON room.type=room_type.type_id")
    data=cur.fetchall()
    print(data)
    return render_template('home.html',data=data)


@app.route('/admin_login')
@app.route('/admin_login',methods=['GET','POST'])
def admin_login():
    if request.method == 'POST':
       admin_id = request.form['admin_id']
       password_admin=request.form['password']
       cur=connection.cursor()
       cur.execute("SELECT * FROM admin WHERE admin_id= %s AND password= %s",[admin_id,password_admin])
       data = cur.fetchone()
       if not data:
          error='ADMIN ID/PASSWORD WRONG'
          return render_template('admin_login.html',error=error)
       else:
          # if sha256_crypt.verify(password_cand,data):
          session['logged_in']=True
          flash('Hi Admin,...You are now logged in','success')
          return redirect(url_for('administration'))
       cur.close()
    return render_template('admin_login.html')



@app.route('/logout')
def logout():
    session.clear()
    flash('You are now logged out','success')
    return redirect(url_for('index'))



@app.route('/administration',methods=['GET','POST'])
def administration():
    cur=connection.cursor()
    cur.execute("SELECT COUNT(*) FROM booking")
    data = cur.fetchone()
    session['booking_count']=data[0]
    cur.close()
    return render_template('administration.html')



@app.route('/addroom',methods=['GET','POST'])
def addroom():
    if request.method == 'POST':
        room_no= request.form['room_no']
        ac= request.form['ac']
        bed_count= request.form['bed']
        price= request.form['price']
        wifi= request.form['wifi']
        type=request.form['room_type']
        cur=connection.cursor()

        cur.execute("INSERT INTO room(room_no, ac, bed, price, wifi,type) VALUES(%s,%s,%s,%s,%s,%s)", (room_no, ac, bed_count, price,wifi,type))
        cur.execute("UPDATE room_type SET room_count=room_count+1,room_available=room_available+1 WHERE type_id=%s",[type])
        connection.commit()
        cur.close()

        flash('The Product has been Added','success')
    return render_template('add_room.html')



@app.route('/add_room_type',methods=['GET','POST'])
def add_room_type():
    if request.method == 'POST':
        type_id= request.form['type_id']
        type_name= request.form['type_name']
        cur=connection.cursor()
        cur.execute("INSERT INTO room_type(type_id, type) VALUES(%s,%s)", (type_id,type_name))
        connection.commit()
        cur.close()
        flash('The Room Type has been Added','success')
    return render_template('add_room_type.html')



@app.route('/search_room',methods=['GET','POST'])
def search_room():
    if request.method == 'POST':
        room_no= request.form['room_no']
        cur=connection.cursor()

        cur.execute("SELECT * FROM room WHERE room_no= %s",[room_no])
        data = cur.fetchone()
        connection.commit()
        cur.close()
        return render_template('update_room.html',data=data)
    return render_template('update_search.html')



@app.route('/update_room',methods=['GET','POST'])
def update_room():
    if request.method == 'POST':
        room_no= request.form['room_no']
        bed= request.form['bed']
        price= request.form['price']
        service= request.form['service']
        cur=connection.cursor()
        if service=="1":
            cur.execute("UPDATE room_type SET room_available = room_available-1 WHERE type_id=(SELECT type FROM room WHERE room_no=%s)",[room_no])
        if service=="0":
            cur.execute("UPDATE room_type SET room_available = room_available+1 WHERE type_id=(SELECT type FROM room WHERE room_no=%s)",[room_no])

        cur.execute("UPDATE room SET bed=%s,price=%s,under_service=%s WHERE room_no=%s", (bed,price,service,room_no))
        connection.commit()
        cur.close()

        flash('The Room Type has been Updated','success')
        return render_template('administration.html')
    return render_template('update_room.html')



@app.route('/view_request',methods=['GET','POST'])
def view_request():
    cur=connection.cursor()
    cur.execute("SELECT * FROM booking")
    book_data=cur.fetchall()
    return render_template('view_request.html',book_data=book_data)



@app.route('/approve_book',methods=['GET','POST'])
def approve_book():
    if request.method == 'POST':
        book_id= request.form['book_id']
        cur=connection.cursor()
        cur.execute("SELECT * FROM booking WHERE booking_id=%s",[book_id])
        data=cur.fetchone()
        cur.execute("INSERT INTO approved(room_no, user_id, check_in, check_out) VALUES(%s,%s,%s,%s)",(data[1],data[2],data[3],data[4]))
        cur.execute("DELETE FROM booking WHERE booking_id=%s",[book_id])
        connection.commit()
        cur.execute("SELECT * FROM booking")
        book_data=cur.fetchall()
        return render_template('view_request.html',book_data=book_data)
@app.route('/deny_book',methods=['GET','POST'])


def deny_book():
    if request.method == 'POST':
        book_id= request.form['book_id']
        cur=connection.cursor()
        cur.execute("DELETE FROM booking WHERE booking_id=%s",[book_id])
        connection.commit()
        cur.execute("SELECT * FROM booking")
        book_data=cur.fetchall()
        return render_template('view_request.html',book_data=book_data)

@app.route('/admin_home')
def admin_home():
    cur=connection.cursor()
    cur.execute("SELECT * FROM room LEFT JOIN room_type ON room.type=room_type.type_id")
    data=cur.fetchall()
    print(data)
    return render_template('admin_home.html',data=data)



#-------------------------------------------Customer-----------------------------------


class RegisterForm(Form):
    name = StringField([validators.Length(min=1, max=50)],render_kw={"placeholder":"Name"})
    password = PasswordField([validators.DataRequired(),validators.EqualTo('confirm',message='Password do not match')],render_kw={"placeholder":"Password"} )
    confirm=PasswordField(render_kw={"placeholder":"Confirm Password"})
    phno = StringField([validators.Length(min=10, max=12)],render_kw={"placeholder":"Phone"})
    email = StringField(render_kw={"placeholder":"Email"})

@app.route('/register', methods=['GET','POST'])
def register():
    form=RegisterForm(request.form)
    if request.method == 'POST' and form.validate():
        name=form.name.data
        # password=sha256_crypt.encrypt(str(form.password.data))
        password=form.password.data
        # uid=form.uid.data
        phno=form.phno.data
        email=form.email.data
        cur=connection.cursor()
        cur.execute("INSERT INTO customer(name,password,phno,email) VALUES(%s,%s,%s,%s)", (name,password,phno,email))
        connection.commit()
        cur.close()
        flash('You are Registered','success')
        return redirect(url_for('login'))
    return render_template('register.html',form=form)


@app.route('/login',methods=['GET','POST'])
def login():
    if request.method == 'POST':
       email = request.form['email']
       password=request.form['password']
       print(password)
       cur=connection.cursor()
       cur.execute("SELECT * FROM customer WHERE email= %s AND password= %s",[email,password])
       data = cur.fetchone()
       if data:
          u_id=data[0]
          u_name=data[1]
          u_phno=data[3]
          u_email=data[4]
       if not data:
          error='USERNAME/PASSWORD WRONG'
          return render_template('login.html',error=error)
       else:
          # if sha256_crypt.ver ify(password_cand,data):
          session['logged_in']=True
          session['uid']=u_id
          session['username']=u_name
          session['email']=u_email
          session['phno']=u_phno
          flash('You are now logged in','success')
          return redirect(url_for('index'))
       cur.close()
    return render_template('login.html')



@app.route('/check_room',methods=['GET','POST'])
def check_room():
    if request.method == 'POST':
        check_in = request.form['check_in']
        check_out = request.form['check_out']
        # print(check_in)
        cur=connection.cursor()
        cur.execute("SELECT * FROM room WHERE room_no NOT IN(SELECT room.room_no  FROM room INNER JOIN approved on room.room_no=approved.room_no)")
        room=cur.fetchall()
        # print(room)
        cur.execute("SELECT * from room WHERE room_no IN (SELECT room_no FROM approved WHERE ((%s>check_in AND %s > check_out) OR (%s<check_in AND %s < check_out)) AND ((%s NOT BETWEEN check_in AND check_out) AND (%s NOT BETWEEN check_in AND check_out)))",(check_in,check_out,check_in,check_out,check_in,check_out))
        room_data=cur.fetchall()
        # print(room_data)
        room_data.extend(room)
        r_data=[]
        for i in room_data:
            cur.execute("SELECT * FROM room_type WHERE type_id=%s",[i[5]])
            data=cur.fetchone()
            li=list(i)
            li.extend(data)
            i=tuple(li)
            r_data.append(i)
        print(r_data)

    return render_template('home.html',data=r_data)



@app.route('/room_book',methods=['GET','POST'])
def room_book():
    if not session.get('logged_in'):
        return render_template('login.html')
    email=session['email']
    cur=connection.cursor()
    cur.execute("SELECT * FROM customer WHERE email=%s",[email])
    user_data=cur.fetchone()
    if request.method == 'POST':
        room_no = request.form['room_no']
    cur.execute("SELECT * FROM room WHERE room_no=%s",[room_no])
    room_data=cur.fetchone()
    return render_template('room_book.html',user_data=user_data,room_data=room_data)



@app.route('/booking_room',methods=['GET','POST'])
def booking_room():
    if request.method == 'POST':
        user_id = request.form['user_id']
        room_no = request.form['room_no']
        check_in = request.form['check_in']
        check_out = request.form['check_out']
        cur=connection.cursor()
        cur.execute("INSERT INTO booking(room_no,user_id,check_in,check_out) VALUES(%s,%s,%s,%s)",(room_no,user_id,check_in,check_out))

        # cur.execute("UPDATE room_type SET room_available = room_available-1 WHERE type_id=(SELECT type FROM room WHERE room_no=%s)",[room_no])
        # cur.execute("UPDATE room SET booking=1 WHERE room_no=%s",[room_no])
        connection.commit()
        cur.close()
        flash('The Room has been booked','success')
    return redirect(url_for('index'))


@app.route('/my_booking',methods=['GET','POST'])
def my_booking():
    user_id=session['uid']
    cur=connection.cursor()
    cur.execute("SELECT * FROM approved WHERE user_id=%s",[user_id])
    approved_data=cur.fetchall()
    cur.execute("SELECT * FROM booking WHERE user_id=%s",[user_id])
    book_data=cur.fetchall()
    return render_template('my_booking.html',book_data=book_data,approved_data=approved_data)



@app.route('/cancel_book',methods=['GET','POST'])
def cancel_book():
    book_id=request.form['book_id']
    cur=connection.cursor()
    print(book_id)

    # cur.execute("SELECT room_no FROM booking WHERE booking_id=%s",[book_id])
    # room_no=cur.fetchone()
    # print(room_no)
    # cur.execute("UPDATE room_type SET room_available = room_available+1 WHERE type_id=(SELECT type FROM room WHERE room_no=%s)",[room_no[0]])

    cur.execute("DELETE FROM booking WHERE booking_id=%s",[book_id])
    connection.commit()
    flash('The Room has been cancelled','danger')
    return redirect(url_for('index'))



@app.route('/profile',methods=['GET','POST'])
def profile():
    user_id=session['uid']
    cur=connection.cursor()
    cur.execute("SELECT * FROM customer WHERE id=%s",[user_id])
    user_data=cur.fetchone()
    return render_template('profile.html',data=user_data)

@app.route('/check_room_ac',methods=['GET','POST'])
def check_room_ac():
    if request.method == 'POST':
        ac = request.form['ac']
        wifi=request.form['wifi']
        # print(check_in)
        cur=connection.cursor()
        cur.execute("SELECT * FROM room WHERE ac=%s AND wifi=%s",(ac,wifi))
        data=cur.fetchall()
        r_data=[]
        for i in data:
            cur.execute("SELECT * FROM room_type WHERE type_id=%s",[i[5]])
            data=cur.fetchone()
            li=list(i)
            li.extend(data)
            i=tuple(li)
            r_data.append(i)
        print(r_data)
    return render_template('home.html',data=r_data)

if __name__=='__main__':
    app.secret_key='secret123'
    app.run(debug=True,port='2000')
