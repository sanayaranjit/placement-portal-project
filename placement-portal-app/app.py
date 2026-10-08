from flask import Flask, url_for, render_template, redirect, request, session, flash, make_response
from models import db, Admin, Student, Company, Drive, Application
from datetime import datetime
from predictor import get_fit_score 
import pandas as pd 

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.secret_key = 'my_secret_key' 
db.init_app(app)

# database creation
with app.app_context():
    db.create_all()

    admin_check = Admin.query.filter_by(email='admin@portal.com').first()
    if not admin_check:
        new_admin = Admin(
            username='admin',
            name='Admin',
            email='admin@portal.com',
            password='admin123'
        )
        db.session.add(new_admin)
        db.session.commit()
        print("Default admin created.")


@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        role = request.form.get('role')

        if role == 'Student':
            user = Student.query.filter_by(email=email).first()
            if user and user.password == password:
                if user.is_active == True: 
                    session['user_id'] = user.id
                    session['role'] = 'Student'
                    return redirect('/student')
                else:
                    flash("Your account has been blacklisted.")
                    return redirect('/')
                
        elif role == 'Company':
            user = Company.query.filter_by(email=email).first()
            if user and user.password == password:
                if user.approval_status != 'approved':
                    flash("Account pending Admin approval.")
                    return redirect('/')
                session['user_id'] = user.id
                session['role'] = 'Company'
                return redirect('/company')
                
        elif role == 'Admin':
            user = Admin.query.filter_by(email=email).first()
            if user and user.password == password:
                session['user_id'] = user.id
                session['role'] = 'Admin'
                return redirect('/admin')

        flash("Incorrect email or password")

    return render_template('login.html')


@app.route('/register/company', methods=['GET', 'POST'])
def register_company():
    if request.method == 'POST':
        new_company = Company(
            username=request.form.get('username'),
            company_name=request.form.get('company_name'),
            email=request.form.get('email'),
            password=request.form.get('password'),
            description=request.form.get('description'),
            approval_status='pending'
        )
        db.session.add(new_company)
        db.session.commit()
        return redirect(url_for('login'))
        
    return render_template('register/company.html')


@app.route('/register/student', methods=['GET', 'POST'])
def register_student():
    if request.method == 'POST':
        cgpa_val = request.form.get('cgpa')
        
        new_student = Student(
            username=request.form.get('username'),
            name=request.form.get('name'),
            email=request.form.get('email'),
            password=request.form.get('password'),
            department=request.form.get('department'),
            cgpa=float(cgpa_val) if cgpa_val else None,
            skills=request.form.get('skills'),
            is_active=True,
            projects=int(request.form.get('projects') or 0),
            backlogs=int(request.form.get('backlogs') or 0),
            internships=int(request.form.get('internships') or 0)
        )
        db.session.add(new_student)
        db.session.commit()
        return redirect(url_for('login'))
        
    return render_template('register/student.html')


@app.route('/admin')
def admin_dashboard():
    if 'role' not in session or session['role'] != 'Admin':
        return redirect(url_for('login'))

    search_student = request.args.get('q_student')
    search_company = request.args.get('q_company')

    if search_student:
        students = Student.query.filter(
            (Student.name.ilike(f'%{search_student}%')) | 
            (Student.email.ilike(f'%{search_student}%')) |
            (Student.department.ilike(f'%{search_student}%'))
        ).all()
    else:
        students = Student.query.all()

    if search_company:
        companies = Company.query.filter(Company.company_name.ilike(f'%{search_company}%')).all()
    else:
        companies = Company.query.all()

    drive = Drive.query.all()
    
    pending_companies = Company.query.filter_by(approval_status='pending').all()

    pending_drives = []
    all_pending_drives = Drive.query.filter_by(status='Pending').all()
    for d in all_pending_drives:
        comp = Company.query.get(d.company_id)
        if comp:
            drive_info = {}
            drive_info['id'] = d.id
            drive_info['job_title'] = d.job_title
            drive_info['company_name'] = comp.company_name
            drive_info['deadline'] = d.deadline
            pending_drives.append(drive_info)

    all_applications = Application.query.all()
    applications = []
    for a in all_applications:
        s = Student.query.get(a.student_id)
        d = Drive.query.get(a.drive_id)
        if s and d:
            c = Company.query.get(d.company_id)
            if c:
                app_info = {}
                app_info['id'] = a.id
                app_info['student_name'] = s.name
                app_info['job_title'] = d.job_title
                app_info['company_name'] = c.company_name
                app_info['status'] = a.status
                app_info['drive_id'] = a.drive_id
                applications.append(app_info)

    total_students = Student.query.count()
    total_companies = Company.query.count()
    total_drives = Drive.query.count()
    total_applications = Application.query.count()

    return render_template('admin/admin_dashboard.html',
        total_students=total_students,
        total_companies=total_companies,
        total_drives=total_drives,
        total_applications=total_applications,
        pending_companies=pending_companies,
        pending_drives=pending_drives,
        students=students,
        companies=companies,
        applications=applications,
        drive=drive
    )


@app.route('/admin/approve-company', methods=['POST'])
def approve_company():
    if 'role' not in session or session['role'] != 'Admin':
        return redirect(url_for('login'))
        
    company_id = request.form.get('id')
    action = request.form.get('action')
    c = Company.query.get(company_id)
    
    if c:
        if action == 'approve':
            c.approval_status = 'approved'
        else:
            c.approval_status = 'rejected'
        db.session.commit()
        
    return redirect(url_for('admin_dashboard'))


@app.route('/admin/approve-drive', methods=['POST'])
def approve_drive():
    if 'role' not in session or session['role'] != 'Admin':
        return redirect(url_for('login'))
        
    drive_id = request.form.get('id')
    action = request.form.get('action')
    d = Drive.query.get(drive_id)
    
    if d:
        if action == 'approve':
            d.status = 'Approved'
        else:
            d.status = 'Rejected'
        db.session.commit()
        
    return redirect(url_for('admin_dashboard'))


@app.route('/admin/blacklist-company', methods=['POST'])
def blacklist_company():
    if 'role' not in session or session['role'] != 'Admin':
        return redirect(url_for('login'))
        
    company_id = request.form.get('id')
    c = Company.query.get(company_id)
    if c:
        c.approval_status = 'rejected'
        company_drives = Drive.query.filter_by(company_id=c.id).all()
        for d in company_drives:
            d.status = 'Closed'
            Application.query.filter_by(drive_id=d.id).delete()
        db.session.commit()
        print("--- DEBUG: Database commit successful! ---")
    return redirect(url_for('admin_dashboard'))


@app.route('/admin/blacklist-student', methods=['POST'])
def blacklist_student():
    if 'role' not in session or session['role'] != 'Admin':
        return redirect(url_for('login'))
        
    student_id = request.form.get('id')
    s = Student.query.get(student_id)
    if s:
        s.is_active = False
        db.session.commit()
    return redirect(url_for('admin_dashboard'))


@app.route('/admin/activate-student', methods=['POST'])
def activate_student():
    if 'role' not in session or session['role'] != 'Admin':
        return redirect(url_for('login'))
        
    student_id = request.form.get('id')
    s = Student.query.get(student_id)
    if s:
        s.is_active = True
        db.session.commit()
    return redirect(url_for('admin_dashboard'))


@app.route('/admin/drive/<int:id>')
def admin_drive_details(id):
    if 'role' not in session or session['role'] != 'Admin':
        return redirect(url_for('login'))
        
    d = Drive.query.get_or_404(id)
    c = Company.query.get(d.company_id)
    
    drive = {}
    drive['id'] = d.id
    drive['job_title'] = d.job_title
    drive['company_name'] = c.company_name if c else 'Unknown'
    drive['company_id'] = d.company_id
    drive['package'] = d.package
    drive['location'] = d.location
    drive['deadline'] = d.deadline
    drive['status'] = d.status
    drive['description'] = d.description
    drive['eligibility_criteria'] = d.eligibility_criteria

    applicants = []
    drive_applications = Application.query.filter_by(drive_id=id).all()
    for a in drive_applications:
        s = Student.query.get(a.student_id)
        if s:
            app_data = {}
            app_data['id'] = a.id
            app_data['student_name'] = s.name
            app_data['student_email'] = s.email
            app_data['resume'] = s.resume
            app_data['status'] = a.status
            applicants.append(app_data)

    return render_template('admin/drive_details.html', drive=drive, applicants=applicants)


@app.route('/admin/application/<int:id>')
def admin_student_application(id):
    if 'role' not in session or session['role'] != 'Admin':
        return redirect(url_for('login'))
        
    a = Application.query.get_or_404(id)
    s = Student.query.get(a.student_id)
    d = Drive.query.get(a.drive_id)
    c = Company.query.get(d.company_id) if d else None

    app = {}
    app['student_name'] = s.name if s else 'Unknown'
    app['student_email'] = s.email if s else 'Unknown'
    app['department'] = s.department if s else 'Unknown'
    app['cgpa'] = s.cgpa if s else 'Unknown'
    app['skills'] = s.skills if s else 'Unknown'
    app['resume'] = s.resume if s else None
    app['job_title'] = d.job_title if d else 'Unknown'
    app['company_name'] = c.company_name if c else 'Unknown'
    app['status'] = a.status

    return render_template('admin/student_application.html', app=app)

@app.route('/admin/export-applications')
def export_applications():
    if 'role' not in session or session['role'] != 'Admin':
        return redirect(url_for('login'))
    
    try:
        import pandas as pd
        from flask import make_response
        
        apps = Application.query.all()
        
        data = []
        for a in apps:
            s = Student.query.get(a.student_id)
            d = Drive.query.get(a.drive_id)
            c = Company.query.get(d.company_id) if d else None
            data.append({
                'Student_Name': s.name if s else 'Unknown',
                'Job_Title': d.job_title if d else 'Unknown',
                'Company': c.company_name if c else 'Unknown',
                'Status': a.status
            })
        
        if not data:
            data = [{'Student_Name': 'No Applications Found', 'Job_Title': '-', 'Company': '-', 'Status': '-'}]

        df = pd.DataFrame(data)
        csv_output = df.to_csv(index=False)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"applications_{timestamp}.csv"
        
        response = make_response(csv_output)
        response.headers["Content-Disposition"] = f"attachment; filename={filename}"
        response.headers["Content-type"] = "text/csv"
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        return response

    except Exception as e:
        print(f"CSV EXPORT ERROR: {str(e)}")
        return f"<h1>Error generating CSV:</h1><pre>{str(e)}</pre><br><a href='/admin'>Go Back</a>"


@app.route('/company')
def company_dashboard():
    if session['role'] != 'Company':
        return redirect(url_for('login'))
    
    today = datetime.today().strftime('%Y-%m-%d')
    my_drives = Drive.query.filter_by(company_id=session['user_id']).all()
    for d in my_drives:
        if d.deadline < today and d.status == 'Approved':
            d.status = 'Closed'
    db.session.commit()
        
    company = Company.query.get(session['user_id'])
    all_drives = Drive.query.filter_by(company_id=company.id).all()
    
    drives = []
    for d in all_drives:
        count = Application.query.filter_by(drive_id=d.id).count()
        drive_data = {}
        drive_data['id'] = d.id
        drive_data['job_title'] = d.job_title
        drive_data['package'] = d.package
        drive_data['deadline'] = d.deadline
        drive_data['status'] = d.status
        drive_data['applicant_count'] = count
        drives.append(drive_data)

    return render_template('company/company_dashboard.html', company=company, drives=drives)


@app.route('/company/create-drive', methods=['GET', 'POST'])
def create_drive():
    if session['role'] != 'Company':
        return redirect(url_for('login'))
        
    company = Company.query.get(session['user_id'])
    
    if request.method == 'POST':
        new_drive = Drive(
            company_id=company.id,
            job_title=request.form.get('job_title'),
            package=request.form.get('package'),
            location=request.form.get('location'),
            deadline=request.form.get('deadline'),
            description=request.form.get('description'),
            eligibility_criteria=request.form.get('eligibility_criteria'),
            status='Pending',
            min_cgpa=float(request.form.get('min_cgpa') or 6.0),
            max_backlogs=int(request.form.get('max_backlogs') or 99),
            preferred_streams=request.form.get('preferred_streams'),
            required_skills=request.form.get('required_skills'),
            min_projects=int(request.form.get('min_projects') or 0),
            min_internships=int(request.form.get('min_internships') or 0)
        )
        db.session.add(new_drive)
        db.session.commit()
        return redirect(url_for('company_dashboard'))

    return render_template('company/create_drive.html', company=company)


@app.route('/company/close-drive', methods=['POST'])
def close_drive():
    drive_id = request.form.get('id')
    d = Drive.query.get(drive_id)
    if d and d.company_id == session['user_id']:
        d.status = 'Closed'
        db.session.commit()
    return redirect(url_for('company_dashboard'))


@app.route('/delete/drive/<int:id>', methods=['POST'])
def delete_drive(id):
    if session.get('role') != 'Company':
        return redirect('/')
    
    d = db.session.get(Drive, id)
    if d and d.company_id == session['user_id']:
        Application.query.filter_by(drive_id=id).delete()
        Drive.query.filter_by(id=id).delete()
        db.session.commit()
        return redirect(url_for('company_dashboard'))


@app.route('/company/applicants')
def company_applicants():
    if session['role'] != 'Company':
        return redirect(url_for('login'))
        
    all_drives = Drive.query.filter_by(company_id=session['user_id']).all()
    drive_applications = []
    
    for d in all_drives:
        applicants = []
        for a in Application.query.filter_by(drive_id=d.id).all():
            s = Student.query.get(a.student_id)
            if s:
                app_data = {}
                app_data['id'] = a.id
                app_data['student_name'] = s.name
                app_data['department'] = s.department
                app_data['cgpa'] = s.cgpa
                app_data['resume'] = s.resume
                app_data['status'] = a.status
                applicants.append(app_data)
        
        group_data = {}
        group_data['job_title'] = d.job_title
        group_data['applicants'] = applicants
        drive_applications.append(group_data)

    return render_template('company/update_application.html', drive_applications=drive_applications)


@app.route('/company/update-status', methods=['POST'])
def update_application_status():
    app_id = request.form.get('app_id')
    new_status = request.form.get('status')
    
    a = Application.query.get(app_id)
    if a:
        d = Drive.query.get(a.drive_id)
        if d and d.company_id == session['user_id']:
            a.status = new_status
            db.session.commit()
            
    return redirect(url_for('company_applicants'))


@app.route('/student')
def student_dashboard():
    if session['role'] != 'Student':
        return redirect(url_for('login'))
        
    student = Student.query.get(session['user_id'])
    
    if not student.is_active:
        session.clear()
        return redirect('/')

    all_drives = Drive.query.filter_by(status='Approved').all()
    drives = []
    
    for d in all_drives:
        c = Company.query.get(d.company_id)
        if c:
            application_exists = Application.query.filter_by(student_id=student.id, drive_id=d.id).first()
            
            drive_data = {}
            drive_data['id'] = d.id
            drive_data['job_title'] = d.job_title
            drive_data['company_name'] = c.company_name
            drive_data['company_id'] = d.company_id
            drive_data['package'] = d.package
            drive_data['location'] = d.location
            drive_data['deadline'] = d.deadline
            drive_data['already_applied'] = application_exists is not None
            # Preserved structural dictionary keys while safely enabling ML check flag
            drive_data['has_requirements'] = bool(d.required_skills or d.preferred_streams) 
            drives.append(drive_data)

    return render_template('student/student_dashboard.html', drives=drives, student=student)


@app.route('/student/check-fit/<int:drive_id>')
def check_fit(drive_id):
    if session['role'] != 'Student':
        return redirect(url_for('login'))
    student = Student.query.get(session['user_id'])
    drive = Drive.query.get_or_404(drive_id)
    company = Company.query.get(drive.company_id)
    
    score, message, factors = get_fit_score(student, drive)
    
    return render_template('student/fit_score.html', 
                           score=score, message=message, factors=factors,
                           drive=drive, company=company, student=student)


@app.route('/student/history')
def student_history():
    if session['role'] != 'Student':
        return redirect(url_for('login'))
        
    my_applications = Application.query.filter_by(student_id=session['user_id']).all()
    applications = []
    
    for a in my_applications:
        d = Drive.query.get(a.drive_id)
        if d:
            c = Company.query.get(d.company_id)
            app_data = {}
            app_data['job_title'] = d.job_title
            app_data['company_name'] = c.company_name if c else 'Unknown'
            app_data['status'] = a.status
            applications.append(app_data)
            
    return render_template('student/history.html', applications=applications)


@app.route('/student/profile', methods=['GET', 'POST'])
def student_profile():
    if session['role'] != 'Student':
        return redirect(url_for('login'))
        
    student = Student.query.get(session['user_id'])
    
    if request.method == 'POST':
        student.name = request.form.get('name')
        student.department = request.form.get('department')
        
        cgpa_val = request.form.get('cgpa')
        if cgpa_val:
            student.cgpa = float(cgpa_val)
        else:
            student.cgpa = None
            
        student.skills = request.form.get('skills')
        
        student.projects = int(request.form.get('projects') or 0)
        student.backlogs = int(request.form.get('backlogs') or 0)
        student.aptitude_score = float(request.form.get('aptitude_score') or 50.0)
        student.internships = int(request.form.get('internships') or 0)
        
        file = request.files.get('resume')
        if file and file.filename:
            student.resume = file.filename
            file.save('static/resumes/' + file.filename)
            
        db.session.commit()
        return redirect(url_for('student_profile'))
        
    return render_template('student/profile.html', student=student)


@app.route('/student/company/<int:id>')
def student_company_overview(id):
    if session['role'] != 'Student':
        return redirect(url_for('login'))
        
    company = Company.query.get_or_404(id)
    drives = Drive.query.filter_by(company_id=id, status='Approved').all()
    return render_template('student/company_overview.html', company=company, drives=drives)


@app.route('/student/drive/<int:id>')
def student_drive_details(id):
    if session['role'] != 'Student':
        return redirect(url_for('login'))
        
    d = Drive.query.get_or_404(id)
    c = Company.query.get(d.company_id)
    
    application_exists = Application.query.filter_by(student_id=session['user_id'], drive_id=id).first()
    
    drive = {}
    drive['id'] = d.id
    drive['job_title'] = d.job_title
    drive['company_name'] = c.company_name if c else 'Unknown'
    drive['company_id'] = d.company_id
    drive['package'] = d.package
    drive['location'] = d.location
    drive['deadline'] = d.deadline
    drive['description'] = d.description
    drive['eligibility_criteria'] = d.eligibility_criteria
    drive['already_applied'] = application_exists is not None
    
    return render_template('student/student_drive_details.html', drive=drive)


@app.route('/student/apply', methods=['POST'])
def student_apply():
    if session['role'] != 'Student':
        return redirect(url_for('login'))
        
    drive_id = request.form.get('drive_id')
    student_id = session['user_id'] 

    student = Student.query.get(student_id)
    # if student.cgpa is None or student.cgpa < 8.0:
    #     return "Error: You do not meet the minimum CGPA requirement of 8.0 to apply."

    exists = Application.query.filter_by(student_id=student_id, drive_id=drive_id).first()
    
    if not exists:
        new_application = Application(student_id=student_id, drive_id=drive_id, status='Applied')
        db.session.add(new_application)
        db.session.commit()
        
    return redirect(url_for('student_dashboard'))


@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')


@app.route('/about')
def about():
    return render_template('about.html')



if __name__ == '__main__':
    app.run(debug=True)