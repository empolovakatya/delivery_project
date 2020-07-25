from flask import Flask, render_template, redirect, session, request
from flask_sqlalchemy import SQLAlchemy
import os
from sqlalchemy.dialects.postgresql import JSON
from flask_migrate import Migrate
import json
import requests
from sqlalchemy.sql import func
from flask_wtf import FlaskForm
from wtforms import SubmitField, StringField, PasswordField
from wtforms.validators import InputRequired, Email, DataRequired, EqualTo, Length
from werkzeug.security import generate_password_hash, check_password_hash
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView

app = Flask(__name__)
app.secret_key = 'Karinazadnitsa1569#'
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DATABASE_URL")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
migrate = Migrate(app, db)


def get_data():
    res = requests.get('https://sheetdb.io/api/v1/459o1nx4znd0i')
    data = json.loads(res.text)
    res1 = requests.get('https://sheetdb.io/api/v1/7jyvbxk665v5j')
    data1 = json.loads(res1.text)
    for item in data:
        meal = Meal(
            title=str(item['title']),
            price=int(item['price']),
            description=str(item['description']),
            picture=str(item['picture']),
            category_id=int(item['category_id'])
        )
        db.session.add(meal)
    for i in data1:
        category = Category(
            title=str(i['title'])
        )
        db.session.add(category)
    db.session.commit()


orders_meals_association = db.Table('orders_meals', db.Column('order_id', db.Integer, db.ForeignKey('orders.id')),
                                    db.Column('meal_id', db.Integer, db.ForeignKey('meals.id')))


class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    mail = db.Column(db.String, unique=True, nullable=False)
    password_hash = db.Column(db.String)
    orders = db.relationship('Order', back_populates='mail')
    result_all = db.Column(JSON)
    result_no_stop_words = db.Column(JSON)

    @property
    def password(self):
        raise AttributeError('Вам не нужно знать пароль!')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def password_valid(self, password):
        return check_password_hash(self.password_hash, password)


class Meal(db.Model):
    __tablename__ = 'meals'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String, unique=True, nullable=False)
    price = db.Column(db.Integer, nullable=False)
    description = db.Column(db.String, nullable=False)
    picture = db.Column(db.String, nullable=False)
    category = db.relationship('Category', back_populates='meals')
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'))
    orders = db.relationship('Order', secondary=orders_meals_association, back_populates='meals')
    result_all = db.Column(JSON)
    result_no_stop_words = db.Column(JSON)


class Category(db.Model):
    __tablename__ = 'categories'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String, unique=True, nullable=False)
    meals = db.relationship('Meal', back_populates='category')
    result_all = db.Column(JSON)
    result_no_stop_words = db.Column(JSON)


class Order(db.Model):
    __tablename__ = 'orders'
    id = db.Column(db.Integer, primary_key=True)
    datetime = db.Column(db.DateTime(), nullable=False, server_default=db.func.now())
    summ = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String)
    mail = db.relationship('User', back_populates='orders')
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    name = db.Column(db.String)
    phone = db.Column(db.String, nullable=False)
    address = db.Column(db.String, nullable=False)
    meals = db.relationship('Meal', secondary=orders_meals_association, back_populates='orders')
    # meals = db.Column(db.String)
    result_all = db.Column(JSON)
    result_no_stop_words = db.Column(JSON)


class OrderForm(FlaskForm):
    name = StringField('Ваше имя', [InputRequired()])
    address = StringField('Адрес', [InputRequired()])
    mail = StringField('Электропочта', [InputRequired()])
    phone = StringField('Телефон', [InputRequired()])
    submit = SubmitField('Оформить заказ')


class LoginForm(FlaskForm):
    mail = StringField('Электропочта',
                       [DataRequired()])
    password = PasswordField('Пароль', [DataRequired()])


class RegisterForm(FlaskForm):
    mail = StringField('Электропочта', [DataRequired(), Email(message='Введите корректный e-mail')])
    password = PasswordField('Пароль', [DataRequired(), Length(min=5),
                                        EqualTo('confirm_password', message='Пароли не совпадают!')])
    confirm_password = PasswordField('Пароль еще раз')

# meals_check = Meal.query.all()
# print(meals_check)
if len(db.session.query(Meal).all()) == 0:
    get_data()


@app.route('/')
def main():
    categories_query = db.session.query(Category).all()
    categories = []
    for i in categories_query:
        categories.append(i.title)
    mealsdict = {}
    for j in range(len(categories)):
        mealsdict[categories[j]] = db.session.query(Meal).filter(Meal.category_id == j + 1).order_by(
            func.random()).limit(3)
    summ = 0
    cart = session.get("cart", [])
    for item in cart:
        meal = db.session.query(Meal).filter(Meal.id == item).first()
        summ += meal.price
    return render_template('main.html', mealsdict=mealsdict, cart=cart, length=len(cart), summ=summ)


@app.route('/addtocart/<id>/')
def add_to_cart(id):
    cart = session.get("cart", [])
    cart.append(id)
    session["cart"] = cart
    return redirect('/cart/')


@app.route('/pop/<id>/')
def pop_from_cart(id):
    cart = session.get("cart", [])
    cart.remove(id)
    session["cart"] = cart
    return redirect('/cart/')


@app.route('/cart/', methods=['GET', 'POST'])
def cart_page():
    summ = 0
    cart = session.get("cart", [])
    meals = []
    meals_dict = {}
    for item in cart:
        meal_query = db.session.query(Meal).filter(Meal.id == item).all()
        for i in meal_query:
            summ += i.price
            meals.append(i)
            quantity = meals.count(i)
            meals_dict[i] = quantity
    form = OrderForm()
    if request.method == 'POST':
        # if not form.validate_on_submit():
        user = User.query.filter(User.mail == form.mail.data).first()
        order = Order(
            summ=summ, status='Принят', mail=user, name=form.name.data, phone=form.phone.data,
            address=form.address.data
        )
        db.session.add(order)
        for i in meals:
            order.meals.append(i)
        db.session.commit()
        session.pop("cart")
        return render_template('ordered.html')
    else:
        print(summ, form.mail.data, form.phone.data, form.name.data, form.address.data, meals)
    return render_template('cart.html', cart=cart, length=len(cart), summ=summ, form=form, meals_dict=meals_dict)


@app.route('/account/')
def account():
    summ = 0
    cart = session.get("cart", [])
    for item in cart:
        meal = db.session.query(Meal).filter(Meal.id == item).first()
        summ += meal.price
    user = session.get("user")
    mail = user["mail"]
    orders = Order.query.filter(User.mail == mail).all()
    sum1 = 0
    dictorders = {}
    for order in orders:
        for item in order.meals:
            sum1 += item.price
            n = order.meals.count(item)
        dictorders[order] = sum1
        sum1 = 0
    return render_template('account.html', cart=cart, length=len(cart), summ=summ, orders=orders, dictorders=dictorders)


@app.route('/login/', methods=['GET', 'POST'])
def login():
    if session.get("user"):
        return redirect('/account/')
    form = LoginForm()
    if request.method == "POST":
        if not form.validate_on_submit():
            return render_template('login.html', form=form)
        user = User.query.filter(User.mail == form.mail.data).first()
        if user and user.password_valid(form.password.data):
            session["user"] = {"id": user.id, "mail": user.mail}
            return redirect('/account/')
        else:
            form.mail.errors.append("Неверное имя или пароль")
    return render_template('login.html', form=form)


@app.route('/register/', methods=["GET", "POST"])
def register():
    if session.get("user"):
        return redirect('/account/')
    form = RegisterForm()
    if request.method == "POST":
        if not form.validate_on_submit():
            return render_template('register.html', form=form)
        user = User.query.filter(User.mail == form.mail.data).first()
        if not user:
            newuser = User(mail=form.mail.data, password_hash=generate_password_hash(form.password.data))
            db.session.add(newuser)
            db.session.commit()
            session["user"] = {"id": newuser.id, "mail": newuser.mail}
            return redirect('/account/')
        else:
            form.mail.errors.append("Пользователь с таким e-mail уже существует!")
            return render_template('register.html', form=form)
    return render_template('register.html', form=form)


@app.route('/logout/')
def logout():
    if session.get("user"):
        session.pop("user")
    return redirect("/login/")


@app.route('/ordered/')
def ordered():
    return render_template('ordered.html')


admin = Admin(app)
admin.add_view(ModelView(User, db.session))
admin.add_view(ModelView(Category, db.session))
admin.add_view(ModelView(Meal, db.session))
admin.add_view(ModelView(Order, db.session))

if __name__ == '__main__':
    app.run()
