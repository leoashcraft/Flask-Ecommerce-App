from os import name
from app import db
from flask_login import UserMixin
from datetime import datetime as dt 
from werkzeug.security import generate_password_hash, check_password_hash
from app import login


class User(UserMixin, db.Model):
    __tablename__ = "user"
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(150))
    last_name = db.Column(db.String(150))
    email =  db.Column(db.String(200), unique=True)
    password = db.Column(db.String(200))
    created_on = db.Column(db.DateTime, default=dt.utcnow)
    products = db.relationship("Product", backref="author", lazy=True)
    cart = db.relationship("Cart", backref="user", lazy=True)


    def __repr__(self):
        return f'<User: {self.id} | {self.email}>'

    def from_dict(self, data):
        self.first_name = data['first_name']
        self.last_name = data['last_name']
        self.email = data['email']
        self.password = self.hash_password(data['password'])
        self.save()

    def hash_password(self, original_password):
        return generate_password_hash(original_password)

    def check_hashed_password(self, login_password):
        return check_password_hash(self.password,login_password)

    def save(self):
        db.session.add(self)
        db.session.commit() 

@login.user_loader
def load_user(id):
    return User.query.get(int(id))

    
class Product(db.Model):
    __tablename__ = "product"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200))
    image_file = db.Column(db.String(20), nullable=False, default='default.jpg')
    description = db.Column(db.String(500))
    date_posted = db.Column(db.DateTime, nullable=False, default=dt.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    cart = db.relationship("Cart", backref="products", lazy=True)
    price = db.Column(db.Float(), nullable=False, default=1.0)

    def __repr__(self):
        return f"{self.name}"

    def from_dict(self, data):
        self.name = data['name']
        self.image_file = data['image_file']
        self.description = data['description']
        self.user_id = data['user_id']
        self.price = data['price']
        self.save()

    def total_price(self, user_id):
        price_list = []
        cart_product = Cart.query.filter_by(user_id = user_id).all()
        for product in cart_product:
            product_price =  Product.query.filter_by(id = product.product_id).first().price 
            price_list.append(product_price)
        return sum(price_list)
    
    def save(self):
        db.session.add(self)
        db.session.commit()


class Cart(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id  = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    def __repr__(self):
        product = Product.query.filter_by(id = self.product_id).first()
        return f'{product.name}'

    def from_dict(self, data):
        self.user_id = data['user_id']
        self.product_id = data['product_id']
        self.save()

    def save(self):
        db.session.add(self) 
        db.session.commit() 