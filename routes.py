from flask import render_template, redirect, url_for, flash, request,session
from flask_login import login_user, logout_user, login_required, current_user
from extensions import db, mail
from models import User, KYCDocument, Asset,Order,AdminMessage,WithdrawalRequest,SupportTicket
from forms import LoginForm, RegistrationForm,OrderForm
from werkzeug.utils import secure_filename
from flask_mail import Message
from itsdangerous import URLSafeTimedSerializer
from flask_uploads import UploadSet, configure_uploads, DOCUMENTS
from app import app
from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename
from extensions import db
from models import User, KYCDocument, Asset, WalletAddress, DepositRequest
from forms import OrderForm
import os
import requests
from pycoingecko import CoinGeckoAPI
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import URLSafeTimedSerializer

# Example utility function (ensure this exists and works)
def get_live_prices(pairs):

    cg = CoinGeckoAPI()
    result = {}

    for pair in pairs:
        try:
            base, quote = pair.lower().split('/')
            coin_id = base if base != 'usdt' else quote
            price = cg.get_price(ids=coin_id, vs_currencies=quote)['bitcoin'][quote]
            result[pair] = float(price)
        except:
            result[pair] = None
    return result




# Configure Flask-Reuploaded for documents
# Configure Flask-Uploads for documents
documents = UploadSet('documents', DOCUMENTS)
configure_uploads(app, documents)
# Email confirmation token serializer
s = URLSafeTimedSerializer(app.config['SECRET_KEY'])

import requests
from flask import render_template

@app.route('/')
def home():
    return render_template('index.html', )
'''
@app.route('/trade')
@login_required
def trade():
    return render_template('trade.html')
'''
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.check_password(form.password.data) and user.confirmed:
            login_user(user)
            flash('Login successful.', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid email, password, or unverified account.', 'warning')
    return render_template('login.html', title='Login', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('home'))

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        token = s.dumps(user.email, salt='email-confirm')
        confirm_url = url_for('confirm_email', token=token, _external=True)
        html = render_template('activate.html', confirm_url=confirm_url)
        subject = "Please confirm your email"
        msg = Message(subject, recipients=[user.email], html=html)
        mail.send(msg)
        flash('A confirmation email has been sent.', 'info')
        return redirect(url_for('login'))
    return render_template('signup.html', title='Sign Up', form=form)

@app.route('/confirm/<token>')
def confirm_email(token):
    try:
        email = s.loads(token, salt='email-confirm', max_age=3600)
    except:
        flash('The confirmation link is invalid or has expired.', 'warning')
        return redirect(url_for('index'))
    user = User.query.filter_by(email=email).first_or_404()
    if user.confirmed:
        flash('Account already confirmed.', 'success')
    else:
        user.confirmed = True
        db.session.commit()
        flash('You have confirmed your account.', 'success')
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    user = current_user
    assets = Asset.query.filter_by(user_id=user.id).all()
    kyc_doc = KYCDocument.query.filter_by(user_id=user.id).first()
    orders = Order.query.filter_by(user_id=user.id).all()
    pairs = list(set([order.pair for order in orders]))
    live_prices = get_live_prices(pairs)
    messages = AdminMessage.query.filter_by(user_id=current_user.id).order_by(AdminMessage.timestamp.desc()).all()

    return render_template('dashboard.html', user=user, assets=assets,kyc_doc=kyc_doc,orders=orders,live_prices=live_prices,messages=messages)


@app.route('/kyc', methods=['GET', 'POST'])
@login_required
def kyc():
    if current_user.kyc_verified:
        flash('Your account is already KYC verified.', 'info')
        return redirect(url_for('home'))
    if request.method == 'POST':
        file = request.files.get('document')
        if file and documents.file_allowed(file, file.filename):
            filename = secure_filename(file.filename)
            file_path = documents.save(file, name=filename)
            kyc_doc = KYCDocument(
                user_id=current_user.id,
                document_type=request.form['document_type'],
                document_path=file_path
            )
            db.session.add(kyc_doc)
            db.session.commit()
            flash('KYC document uploaded successfully. Awaiting review.', 'success')
            return redirect(url_for('home'))
        else:
            flash('Invalid file format.', 'danger')
    return render_template('kyc.html')

@app.route('/admin/kyc_pending')
#@login_required
def admin_kyc_pending():
    if not session.get('admin_logged_in'):
        flash('Access denied.', 'danger')
        return redirect(url_for('admin_login'))
    pending_kyc = KYCDocument.query.filter_by(status='pending').all()
    
    # Join with User table to display user email/info in the template
    pending_docs = [
        {
            "doc": doc,
            "user": User.query.get(doc.user_id)
        } for doc in pending_kyc
    ]

    return render_template('admin_kyc_pending.html', pending_docs=pending_docs)
'''
@login_required
def admin_kyc_approve(doc_id):
    if not current_user.is_admin:
        return redirect(url_for('home'))
    kyc_doc = KYCDocument.query.get_or_404(doc_id)
    kyc_doc.status = 'approved'
    user = User.query.get(kyc_doc.user_id)
    user.kyc_verified = True
    db.session.commit()
    flash('KYC approved.', 'success')
    return redirect(url_for('admin_kyc_pending'))

@app.route('/admin/kyc/<int:doc_id>/reject', methods=['POST'])
@login_required
def admin_kyc_reject(doc_id):
    if not current_user.is_admin:
        return redirect(url_for('home'))
    kyc_doc = KYCDocument.query.get_or_404(doc_id)
    kyc_doc.status = 'rejected'
    db.session.commit()
    flash('KYC rejected.', 'success')
    return redirect(url_for('admin_kyc_pending'))
'''
    

'''
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if current_user.is_authenticated and current_user.is_admin:
        return redirect(url_for('admin_dashboard'))

    error = None
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        # You can replace these with env/config variables or a database check
        if username == 'admin' and password == 'admin123':
            user = User.query.filter_by(email='test1@example.com').first()
            if user and user.is_admin:
                #login_user(user)
                flash('Welcome Admin!', 'success')
                return redirect(url_for('admin_dashboard'))
            else:
                error = 'Admin user not found or not set as admin.'
        else:
            error = 'Invalid admin credentials.'

    return render_template('admin_login.html', error=error, title='Admin Login')
'''

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Hardcoded admin credentials
        if username == 'admin' and password == 'admin123':
            session['admin_logged_in'] = True
            flash('Admin login successful.', 'success')
            return redirect(url_for('admin_users'))
        else:
            flash('Invalid admin credentials.', 'danger')

    return render_template('admin_login.html')



from flask import session  # Make sure this is at the top if not already

@app.route('/admin/admin_users')
def admin_users():
    if not session.get('admin_logged_in'):
        flash('Access denied.', 'danger')
        return redirect(url_for('admin_login'))  # Redirect to admin login if not admin
    users = User.query.all()
    return render_template('admin_users.html', users=users)

@app.route('/admin/users/<int:user_id>/verify_kyc', methods=['POST'])
def admin_user_verify_kyc(user_id):
    if not session.get('admin_logged_in'):
        flash('Access denied.', 'danger')
        return redirect(url_for('admin_login'))

    user = User.query.get_or_404(user_id)
    user.kyc_verified = True

    kyc_doc = KYCDocument.query.filter_by(user_id=user.id).first()
    if kyc_doc:
        kyc_doc.status = 'approved'  # <- This ensures dashboard shows it as approved

    db.session.commit()
    flash(f'KYC verified for {user.email}.', 'success')
    return redirect(url_for('admin_users'))



@app.route('/admin/users/<int:user_id>/unverify_kyc', methods=['POST'])
def admin_user_unverify_kyc(user_id):
    if not session.get('admin_logged_in'):
        flash('Access denied.', 'danger')
        return redirect(url_for('admin_login'))
    user = User.query.get_or_404(user_id)
    user.kyc_verified = False
    db.session.commit()
    flash(f'KYC unverified for {user.email}.', 'info')
    return redirect(url_for('admin_users'))


# app.py or routes.py
from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename
from extensions import db
from models import User, KYCDocument, Asset, WalletAddress, DepositRequest
import os

# app.py or routes.py



'''
@app.route('/admin/wallets', methods=['GET', 'POST'])
#@login_required
def admin_wallets():
    if not session.get('admin_logged_in'):
        flash('Access denied.', 'danger')
        return redirect(url_for('admin_login'))

    if request.method == 'POST':
        for i in range(5):
            currency = request.form.get(f'currency_{i}')
            address = request.form.get(f'address_{i}')
            if currency and address:
                wallet = WalletAddress.query.filter_by(currency=currency).first()
                if wallet:
                    wallet.address = address
                else:
                    new_wallet = WalletAddress(currency=currency, address=address)
                    db.session.add(new_wallet)
        db.session.commit()
        flash("Wallet addresses updated successfully.", "success")
        return redirect(url_for('admin_wallets'))

    wallets = WalletAddress.query.all()

    # Pad to 5 entries
    while len(wallets) < 1:
        wallets.append(WalletAddress(currency='', address=''))

    return render_template('admin_wallets.html', wallets=wallets)

@app.route('/admin/wallets/<int:wallet_id>/delete', methods=['POST'])
#@login_required
def delete_wallet(wallet_id):
    if not current_user.is_admin:
        flash('Access denied.', 'danger')
        return redirect(url_for('home'))
    wallet = WalletAddress.query.get_or_404(wallet_id)
    db.session.delete(wallet)
    db.session.commit()
    flash(f'Wallet address for {wallet.currency} deleted.', 'info')
    return redirect(url_for('admin_wallets'))
'''
# Add wallet address
@app.route('/admin/wallets/add', methods=['POST'])
#login_required
def add_wallet():
    if not session.get('admin_logged_in'):
        flash('Access denied.', 'danger')
        return redirect(url_for('admin_login'))
    currency = request.form.get('currency')
    address = request.form.get('address')
    if currency and address:
        new_wallet = WalletAddress(currency=currency, address=address)
        db.session.add(new_wallet)
        db.session.commit()
        flash("Wallet address added successfully.", "success")
    else:
        flash("Both coin and address are required.", "danger")
    return redirect(url_for('admin_wallets'))

# Edit wallet address
@app.route('/admin/wallets/<int:wallet_id>/edit', methods=['POST'])
#@login_required
def edit_wallet(wallet_id):
    if not session.get('admin_logged_in'):
        flash('Access denied.', 'danger')
        return redirect(url_for('admin_login'))
    wallet = WalletAddress.query.get_or_404(wallet_id)
    wallet.coin = request.form.get('currency')
    wallet.address = request.form.get('address')
    db.session.commit()
    flash("Wallet updated.", "success")
    return redirect(url_for('admin_wallets'))

# Delete wallet address
@app.route('/admin/wallets/<int:wallet_id>/delete', methods=['POST'])
@login_required
def delete_wallet(wallet_id):
    if not current_user.is_admin:
        flash("Access denied.", "danger")
        return redirect(url_for('home'))
    wallet = WalletAddress.query.get_or_404(wallet_id)
    db.session.delete(wallet)
    db.session.commit()
    flash("Wallet deleted.", "info")
    return redirect(url_for('admin_wallets'))

# Admin wallet management page
@app.route('/admin/wallets')
#login_required
def admin_wallets():
    if not session.get('admin_logged_in'):
        flash('Access denied.', 'danger')
        return redirect(url_for('admin_login'))
    wallets = WalletAddress.query.all()
    return render_template('admin_wallets.html', wallets=wallets)


@app.route('/deposit', methods=['GET', 'POST'])
@login_required
def deposit():
    wallet_addresses = WalletAddress.query.all()

    if request.method == 'POST':
        currency = request.form['currency']
        amount = float(request.form['amount'])
        proof = request.files['proof']

        if proof:
            filename = secure_filename(proof.filename)
            filepath = os.path.join('static/uploads', filename)
            proof.save(filepath)

            deposit = DepositRequest(
                user_id=current_user.id,
                currency=currency.upper(),
                amount=amount,
                proof_path=filename,
                status='pending'
            )
            db.session.add(deposit)
            db.session.commit()
            flash('Deposit submitted successfully. Admin will review it.', 'success')
            return redirect(url_for('deposit'))
        else:
            flash('Proof of payment is required.', 'danger')

    # Get this user’s deposits
    deposits = DepositRequest.query.filter_by(user_id=current_user.id).order_by(DepositRequest.timestamp.desc()).all()

    return render_template('deposit.html', wallet_addresses=wallet_addresses, deposits=deposits)



@app.route('/admin/deposits')
def admin_deposits():
    if not session.get('admin_logged_in'):
        flash('Access denied.', 'danger')
        return redirect(url_for('admin_login'))
    deposits = DepositRequest.query.order_by(DepositRequest.timestamp.desc()).all()
    return render_template('admin_deposit.html', deposits=deposits)

@app.route('/admin/deposits/<int:deposit_id>/approve', methods=['POST'])
def admin_approve_deposit(deposit_id):
    if not session.get('admin_logged_in'):
        flash('Access denied.', 'danger')
        return redirect(url_for('admin_login'))
    deposit = DepositRequest.query.get_or_404(deposit_id)
    deposit.status = 'approved'
    db.session.commit()
    flash('Deposit approved successfully.', 'success')
    return redirect(url_for('admin_deposits'))

@app.route('/admin/deposits/<int:deposit_id>/reject', methods=['POST'])
def admin_reject_deposit(deposit_id):
    if not session.get('admin_logged_in'):
        flash('Access denied.', 'danger')
        return redirect(url_for('admin_login'))
    deposit = DepositRequest.query.get_or_404(deposit_id)
    deposit.status = 'rejected'
    db.session.commit()
    flash('Deposit rejected.', 'info')
    return redirect(url_for('admin_deposits'))




@app.route('/admin/initial_balances', methods=['GET', 'POST'])
#@login_required
def admin_initial_balances():
    if not session.get('admin_logged_in'):
        flash('Access denied.', 'danger')
        return redirect(url_for('admin_login'))

    users = User.query.filter(User.is_admin == False).all()

    if request.method == 'POST':
        user_id = request.form['user_id']
        currency = request.form['currency']
        amount = float(request.form['amount'])

        assets = Asset.query.filter_by(user_id=user_id, currency=currency).first()
        if assets:
            assets.balance = amount
        else:
            assets = Asset(user_id=user_id, currency=currency, balance=amount)
            db.session.add(assets)

        db.session.commit()
        flash('Initial balance updated.', 'success')
        return redirect(url_for('admin_initial_balances'))

    return render_template('admin_initial_balances.html', users=users)
'''
@app.route('/admin/initial_balances', methods=['GET', 'POST'])
def admin_initial_balances():
    if not session.get('admin_logged_in'):
        flash('Access denied.', 'danger')
        return redirect(url_for('admin_login'))

    users = User.query.filter(User.is_admin == False).all()
    assets = Asset.query.all()  # ✅ Define this

    if request.method == 'POST':
        user_id = request.form['user_id']
        currency = request.form['currency']
        amount = float(request.form['amount'])

        asset = Asset.query.filter_by(user_id=user_id, currency=currency).first()
        if asset:
            asset.balance = amount
        else:
            asset = Asset(user_id=user_id, currency=currency, balance=amount)
            db.session.add(asset)

        db.session.commit()
        flash('Initial balance updated.', 'success')
        return redirect(url_for('admin_initial_balances'))

    return render_template('admin_initial_balances.html', users=users, assets=assets)
'''


# Helper to fetch live price from CoinGecko
def get_live_price(pair):
    symbol_map = {
        'BTC/USDT': ('bitcoin', 'usd'),
        'ETH/USDT': ('ethereum', 'usd'),
        'BNB/USDT': ('binancecoin', 'usd'),
    }
    if pair not in symbol_map:
        return None
    coin_id, vs_currency = symbol_map[pair]
    url = f'https://api.coingecko.com/api/v3/simple/price?ids={coin_id}&vs_currencies={vs_currency}'

    try:
        response = requests.get(url)
        data = response.json()
        return round(data[coin_id][vs_currency], 2)
    except Exception as e:
        print(f"Error fetching live price: {e}")
        return None

@app.route('/trade', methods=['GET', 'POST'])
@login_required
def trade():
    if request.method == 'POST':
        pair = request.form['pair']
        type_ = request.form['type']
        order_type = request.form['order_type']
        quantity = float(request.form['quantity'])

        if order_type == 'limit':
            price = float(request.form['price'])
        else:
            price = get_live_price(pair)
            if price is None:
                flash("Live price unavailable. Try again later.", "danger")
                return redirect(url_for('trade'))

        cost = quantity * price
        base_currency = pair.split('/')[0] if type_ == 'buy' else pair.split('/')[1]

        asset = Asset.query.filter_by(user_id=current_user.id, currency=base_currency).first()
        if not asset:
            asset = Asset(user_id=current_user.id, currency=base_currency, balance=0.0)
            db.session.add(asset)

        # Check balance
        if type_ == 'buy' and asset.balance < cost:
            flash('Insufficient balance to place buy order.', 'warning')
            return redirect(url_for('trade'))
        elif type_ == 'sell' and asset.balance < quantity:
            flash('Insufficient balance to place sell order.', 'warning')
            return redirect(url_for('trade'))

        # Update balances
        if type_ == 'buy':
            asset.balance -= cost
        else:
            asset.balance -= quantity

        # Save order
        order = Order(
            user_id=current_user.id,
            pair=pair,
            type=type_,
            order_type=order_type,
            quantity=quantity,
            price=price,
            status='executed'
        )
        db.session.add(order)

        # Credit to target asset
        target_currency = pair.split('/')[0] if type_ == 'buy' else pair.split('/')[1]
        target_amount = quantity if type_ == 'buy' else cost
        target_asset = Asset.query.filter_by(user_id=current_user.id, currency=target_currency).first()
        if not target_asset:
            target_asset = Asset(user_id=current_user.id, currency=target_currency, balance=0.0)
            db.session.add(target_asset)
        target_asset.balance += target_amount

        db.session.commit()
        flash('Order executed successfully.', 'success')
        return redirect(url_for('dashboard'))

    return render_template('trade.html')

@app.route('/place_order', methods=['POST'])
@login_required
def place_order():
    pair = request.form['pair']
    order_type = request.form['order_type']
    order_side = request.form['type']
    quantity = float(request.form['quantity'])
    price = None

    if order_type == 'limit':
        price = float(request.form['price'])

    # Create new order
    new_order = Order(
        user_id=current_user.id,
        pair=pair,
        type=order_side,
        order_type=order_type,
        quantity=quantity,
        price=price,
        status='open'
    )

    # Optionally deduct from user balance immediately (if desired)
    db.session.add(new_order)
    db.session.commit()

    flash('Order placed successfully!', 'success')
    return redirect(url_for('dashboard'))

# View all assets
@app.route('/admin/assets')
def admin_assets():
    if not session.get('admin_logged_in'):
        flash('Access denied.', 'danger')
        return redirect(url_for('admin_login'))

    assets = Asset.query.all()
    return render_template('admin_assets.html', assets=assets)

# Edit asset
@app.route('/admin/assets/edit/<int:asset_id>', methods=['GET', 'POST'])
def edit_asset(asset_id):
    if not session.get('admin_logged_in'):
        flash('Access denied.', 'danger')
        return redirect(url_for('admin_login'))

    assets = Asset.query.get_or_404(asset_id)

    if request.method == 'POST':
        assets.currency = request.form['currency'].upper()
        assets.balance = float(request.form['balance'])
        db.session.commit()
        flash('Asset updated successfully.', 'success')
        return redirect(url_for('admin_assets'))

    return render_template('edit_asset.html', assets=assets)

# Delete asset
@app.route('/admin/assets/delete/<int:asset_id>', methods=['POST'])
def delete_asset(asset_id):
    if not session.get('admin_logged_in'):
        flash('Access denied.', 'danger')
        return redirect(url_for('admin_login'))

    assets = Asset.query.get_or_404(asset_id)
    db.session.delete(assets)
    db.session.commit()
    flash('Asset deleted.', 'success')
    return redirect(url_for('admin_assets'))

@app.route('/admin/send_message', methods=['GET', 'POST'])
def send_message():
    if not session.get('admin_logged_in'):
        flash('Access denied.', 'danger')
        return redirect(url_for('admin_login'))

    users = User.query.filter_by(is_admin=False).all()

    if request.method == 'POST':
        user_id = request.form['user_id']
        subject = request.form['subject']
        body = request.form['body']

        message = AdminMessage(user_id=user_id, subject=subject, body=body)
        db.session.add(message)
        db.session.commit()

        flash('Message sent successfully!', 'success')
        return redirect(url_for('send_message'))

    return render_template('admin_send_message.html', users=users)

        
@app.route('/withdraw', methods=['GET', 'POST'])
@login_required
def withdraw():
    if request.method == 'POST':
        currency = request.form['currency']
        amount = float(request.form['amount'])
        wallet_address = request.form['wallet_address']

     
        '''
        asset = Asset.query.filter_by(user_id=current_user.id, currency=currency).first()
        if not asset or asset.balance < amount:
            flash('Insufficient balance.', 'danger')
        
            return redirect(url_for('withdraw'))
            
'''
        withdrawal = WithdrawalRequest(
            user_id=current_user.id,
            currency=currency,
            amount=amount,
            wallet_address=wallet_address,
            status='pending'
        )
        db.session.add(withdrawal)
        db.session.commit()
        flash('Withdrawal request submitted.', 'success')
        return redirect(url_for('withdraw'))

    history = WithdrawalRequest.query.filter_by(user_id=current_user.id).order_by(WithdrawalRequest.timestamp.desc()).all()
    return render_template('withdraw.html', history=history)


@app.route('/admin/withdrawals')
def admin_withdrawals():
    if not session.get('admin_logged_in'):
        flash('Access denied.', 'danger')
        return redirect(url_for('admin_login'))

    withdrawals = WithdrawalRequest.query.order_by(WithdrawalRequest.timestamp.desc()).all()
    return render_template('admin_withdrawals.html', withdrawals=withdrawals)
@app.route('/admin/withdrawals/approve/<int:withdrawal_id>', methods=['POST'])
def admin_approve_withdrawal(withdrawal_id):
    if not session.get('admin_logged_in'):
        flash('Access denied.', 'danger')
        return redirect(url_for('admin_login'))

    withdrawal = WithdrawalRequest.query.get_or_404(withdrawal_id)
    withdrawal.status = 'approved'

    # Optionally deduct from user's asset (you can also do it at request stage)
    asset = Asset.query.filter_by(user_id=withdrawal.user_id, currency=withdrawal.currency).first()
    if asset and asset.balance >= withdrawal.amount:
        asset.balance -= withdrawal.amount

    db.session.commit()
    flash(f'Withdrawal for {withdrawal.user.email} approved.', 'success')
    return redirect(url_for('admin_withdrawals'))

@app.route('/admin/withdrawals/reject/<int:withdrawal_id>', methods=['POST'])
def admin_reject_withdrawal(withdrawal_id):
    if not session.get('admin_logged_in'):
        flash('Access denied.', 'danger')
        return redirect(url_for('admin_login'))

    withdrawal = WithdrawalRequest.query.get_or_404(withdrawal_id)
    withdrawal.status = 'rejected'
    db.session.commit()
    flash(f'Withdrawal for {withdrawal.user.email} rejected.', 'info')
    return redirect(url_for('admin_withdrawals'))


@app.route('/support', methods=['GET', 'POST'])
@login_required
def support():
    if request.method == 'POST':
        subject = request.form['subject']
        message = request.form['message']
        ticket = SupportTicket(user_id=current_user.id, subject=subject, message=message)
        db.session.add(ticket)
        db.session.commit()
        flash('Your support ticket has been submitted.', 'success')
        return redirect(url_for('support'))

    tickets = SupportTicket.query.filter_by(user_id=current_user.id).order_by(SupportTicket.timestamp.desc()).all()
    return render_template('support.html', tickets=tickets)


@app.route('/admin/tickets')
def admin_tickets():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    tickets = SupportTicket.query.order_by(SupportTicket.timestamp.desc()).all()
    return render_template('admin_tickets.html', tickets=tickets)

@app.route('/admin/tickets/<int:ticket_id>', methods=['GET', 'POST'])
def respond_ticket(ticket_id):
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))

    ticket = SupportTicket.query.get_or_404(ticket_id)
    if request.method == 'POST':
        ticket.response = request.form['response']
        ticket.status = 'closed'
        db.session.commit()
        flash('Ticket response submitted.', 'success')
        return redirect(url_for('admin_tickets'))

    return render_template('respond_ticket.html', ticket=ticket)

from itsdangerous import URLSafeTimedSerializer

# Configure the serializer (you can use your app secret key)
serializer = URLSafeTimedSerializer('your-secret-key')

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email')
        user = User.query.filter_by(email=email).first()
        if user:
            token = serializer.dumps(email, salt='password-reset')
            reset_url = url_for('reset_password', token=token, _external=True)

            msg = Message('Reset Your Password', sender='noreply@astrohub.com', recipients=[email])
            msg.body = f"Hi,\n\nClick the link below to reset your password:\n{reset_url}\n\nIf you didn't request this, ignore this email."
            mail.send(msg)

            flash('A password reset link has been sent to your email.', 'success')
        else:
            flash('No account found with that email.', 'danger')
        return redirect(url_for('forgot_password'))
    
    return render_template('auth/forgot_password.html')


@app.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    try:
        email = serializer.loads(token, salt='password-reset', max_age=3600)
    except:
        flash('Invalid or expired token.', 'danger')
        return redirect(url_for('login'))

    if request.method == 'POST':
        new_password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        if user:
            user.password = generate_password_hash(new_password)
            db.session.commit()
            flash('Your password has been updated. You can now log in.', 'success')
            return redirect(url_for('login'))
        else:
            flash('User not found.', 'danger')
            return redirect(url_for('login'))
    
    return render_template('auth/reset_password.html', token=token)
