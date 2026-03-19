from flask import request
from werkzeug.utils import secure_filename
from app import app, db
from app.models import KYCDocument
from flask_login import login_required, current_user

@app.route('/kyc', methods=['GET', 'POST'])
@login_required
def kyc():
    if current_user.kyc_verified:
        flash('Your account is already KYC verified.', 'info')
        return redirect(url_for('home'))
    if request.method == 'POST':
        file = request.files['document']
        if file and documents.accept(file.filename):
            filename = secure_filename(file.filename)
            file_path = documents.save(file)
            kyc_doc = KYCDocument(user_id=current_user.id, document_type=request.form['document_type'], document_path=file_path)
            db.session.add(kyc_doc)
            db.session.commit()
            flash('KYC document uploaded successfully. Awaiting review.', 'success')
            return redirect(url_for('home'))
    return render_template('kyc.html')

@app.route('/admin/kyc/pending')
@login_required
def admin_kyc_pending():
    if not current_user.is_admin:
        return redirect(url_for('home'))
    pending_kyc = KYCDocument.query.filter_by(status='pending').all()
    return render_template('admin_kyc_pending.html', kyc_docs=pending_kyc)

@app.route('/admin/kyc/<int:doc_id>/approve', methods=['POST'])
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