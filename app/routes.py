from flask import render_template, request, redirect, url_for, flash, abort
from app import app, db
import secrets
import os
from PIL import Image
from flask_login import login_user, logout_user, current_user, login_required
from .forms import LoginForm, RegisterForm, ProductForm
from .models import User, Product, Cart

@app.route("/", methods=["GET"])
def index():
    products = Product.query.all()
    return render_template('index.html.j2', products = products)


@app.route('/register', methods=['GET','POST'])
def register():
    form = RegisterForm()
    if request.method == 'POST' and form.validate_on_submit():
        try:
            new_user_data={
                "first_name": form.first_name.data.title(),
                "last_name": form.last_name.data.title(),
                "email": form.email.data.lower(),
                "password": form.password.data
            }
            new_user_object = User()
            new_user_object.from_dict(new_user_data)
        except:
            error_string="There was a problem creating your account. Please try again"
            return render_template('register.html.j2',form=form, error=error_string)
        # Give the user some feedback that says registered successfully 
        return redirect(url_for('login'))

    return render_template('register.html.j2',form=form)

@app.route('/login', methods=['GET','POST'])
def login():
    form = LoginForm()
    if request.method == 'POST':
        email = form.email.data.lower()
        password = form.password.data
        u = User.query.filter_by(email=email).first()
        print(u)
        if u is not None and u.check_hashed_password(password):
            login_user(u)
            # Give User feeedback of success
            flash(f'Welcome {u.first_name}', 'success')
            return redirect(url_for('index'))
        else:
            # Give user Invalid Password Combo error
            return redirect(url_for('login'))
    return render_template("login.html.j2", form=form)

# Resize the product image and return the file
def save_picture(form_picture):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(app.root_path, 'static/product_pics', picture_fn)
    
    output_size = (300, 300)
    i = Image.open(form_picture)
    i.thumbnail(output_size)
    i.save(picture_path)

    return picture_fn

# A route to create product 

@app.route('/createproduct', methods=['GET','POST'])
def create_product():
    form = ProductForm()
    if form.validate_on_submit():
        print("Yes")
        print("Picture is", form.picture.data)
        image_file = save_picture(form.picture.data)

        product_data = {
            'name' : form.name.data,
            'description' : form.description.data,
            'user_id' : current_user.id,
            'image_file' : image_file,
            'price' : form.price.data
        }

        Product().from_dict(product_data)
        print("It has been saved!")
        return redirect(url_for("index"))

    return render_template("create_product.html.j2", form=form)

@app.route("/product/<int:product_id>")
def product(product_id):
    product = Product.query.get_or_404(product_id)
    return render_template('product.html.j2', product=product)

@app.route('/logout', methods=['GET'])
@login_required
def logout():
    if current_user is not None:
        logout_user()
        return redirect(url_for('index'))

@app.route('/addtocart/<int:product_id>', methods=['GET'])
@login_required
def addtocart(product_id):
    product_data = {
        'user_id' : current_user.id,
        'product_id' : product_id
    }
    check_product_in_cart = bool(Cart.query.filter_by(user_id = product_data['user_id'], product_id = product_data['product_id']).first())
    
    if check_product_in_cart == True:
        flash(f'Product already in your cart', 'danger')
        return redirect(url_for('cart'))
    else:
        Cart().from_dict(product_data)
        flash(f'Product has been added to your cart', 'success')
        return redirect(url_for('cart'))


@app.route('/cart', methods=['GET'])
@login_required
def cart():
    user_cart = Cart.query.filter_by(user_id = current_user.id).all()
    cart_products = (Product.query.filter_by(id = product.product_id).first() for product in user_cart)
    products = list(cart_products)
    total = Product().total_price(user_id= current_user.id)
    return render_template("cart.html.j2", products = products, total = total)


@app.route('/deletefromcart/<int:product_id>', methods=['GET'])
@login_required
def deletefromcart(product_id):
    product = Cart.query.filter_by(product_id = product_id, user_id = current_user.id).first()
    db.session.delete(product)
    db.session.commit()
    flash('Product has been removed', 'success')
    return redirect(url_for('cart'))


@app.route('/deleteallfromcart', methods=['GET'])
@login_required
def deleteallfromcart():
    db.session.query(Cart).filter(Cart.user_id == current_user.id).delete()
    db.session.commit()
    flash('All products have been removed', 'success')
    return redirect(url_for('index'))