"""
    Assignment Planner
    ~~~~~~
    This code is based off of a microblog example application written as Flask tutorial with
    Flask and sqlite3.
    :copyright: (c) 2015 by Armin Ronacher.
    :license: BSD, see LICENSE for more details.
"""

import os
from datetime import datetime
from sqlite3 import dbapi2 as sqlite3
from flask import Flask, request, session, g, redirect, url_for, abort, \
    render_template, flash

# create our little application :)
app = Flask(__name__)

# Load default config and override config from an environment variable
app.config.update(dict(
    DATABASE=os.path.join(app.root_path, 'purplephages.db'),
    DEBUG=True,
    SECRET_KEY='development key',
))
app.config.from_envvar('FLASKR_SETTINGS', silent=True)


def connect_db():
    """Connects to the specific database."""
    nv = sqlite3.connect(app.config['DATABASE'])
    nv.row_factory = sqlite3.Row
    return nv


def init_db():
    """Initializes the database."""
    db = get_db()
    with app.open_resource('phageschema.sql', mode='r') as f:
        db.cursor().executescript(f.read())
    db.commit()


@app.cli.command('initdb')
def initdb_command():
    """Creates the database tables."""
    init_db()
    print('Initialized the database.')


def get_db():
    """Opens a new database connection if there is none yet for the
    current application context.
    """
    if not hasattr(g, 'sqlite_db'):
        g.sqlite_db = connect_db()
    return g.sqlite_db


@app.teardown_appcontext
def close_db(error):
    """Closes the database again at the end of the request."""
    if hasattr(g, 'sqlite_db'):
        g.sqlite_db.close()


# Creating a new account - register page

@app.route('/register')
def redirect_signup():
    if 'logged_in' in session:
        username = session['logged_in']
        homepage = True;
        return render_template('homepage.html', username=username, homepage=homepage)
    signup = True;
    return render_template('signup.html', signup=signup)


# Post method executed for creating a new account

@app.route('/create_account', methods=['POST'])
def create_account():
    db = get_db()
    validate = db.execute('SELECT username FROM accounts WHERE username=?', [request.form['username']])

    # Checks to see if there is already a similar username that exists
    # If the username exists, make the user redo the account registration
    if validate.fetchall():
        flash('The username already exists. Try with another username')
        return redirect(url_for('redirect_signup'))
    # If the username does not already exist, check to make sure the two passwords are similar
    else:
        password = request.form['password']
        re_password = request.form['password2']

        # If the passwords do not match, make the user redo the account registration
        if password != re_password:
            flash('Passwords do not match. Try again.')
            return redirect(url_for('redirect_signup'))
        else:
            # If the passwords match and the username is unique, then insert the
            # username and password into the database.
            db.execute('INSERT INTO accounts (username, password, firstName, '
                       'lastName, studentYear, email) VALUES (?, ?, ?, ?, ?, ?)',
                       [request.form['username'], password, request.form['firstName'],
                        request.form['lastName'], request.form['studentYear'], request.form['email']])
            db.commit()
        flash('Account creation successful.')
    return redirect(url_for('redirect_login'))


# Log in page

@app.route('/login')
def redirect_login():
    # Checks if a user is already logged in so that the user does not try to log in again.
    if 'logged_in' in session:
        username = session['logged_in']
        homepage = True;
        return render_template('homepage.html', username=username, homepage=homepage)
    # If the user is not in session, then it will allow the user to log in
    login = True;
    return render_template('login.html', login=login)


# Post method executed after submitting login information

@app.route('/login_account', methods=['POST'])
def login_account():
    db = get_db()
    username = request.form['username']
    validate_account = db.execute('select username, password from accounts where username=?', [username])
    data = validate_account
    data = dict(data)

    if db.execute('select username, password from accounts where username=?', [username]).fetchall():
        password = request.form['password']

        if data.get(username) == password:
            session['logged_in'] = username
            flash('Logged into ' + username)
            webpage = 'home';
            return render_template('homepage.html', username=username, webpage=webpage)

        else:
            flash('Wrong username and password. Try again.')
    else:
        flash('Username does not exist. Try again.')
    return redirect(url_for('redirect_login'))


# Logs the user out of the current session

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    flash('You were logged out')
    homepage = True;
    return render_template('homepage.html', homepage=homepage)


@app.route('/')
def redirect_home():
    homepage = True;
    if 'logged_in' in session:
        username = session['logged_in']
        return render_template('homepage.html', username=username, homepage=homepage)
    return render_template('homepage.html', homepage=homepage)


# Personal account page - view by clicking on username in top right corner

@app.route('/account')
def account_home():
    if 'logged_in' in session:
        username = session['logged_in']
        db = get_db()
        cur = db.execute('SELECT * FROM phages WHERE author=? ORDER BY phageName ASC', [username])
        phages = cur.fetchall()
        cur2 = db.execute('SELECT * FROM phages WHERE author=? ORDER BY phageName ASC', [username])
        phages2 = cur2.fetchall()
        cur3 = db.execute('SELECT * FROM accounts WHERE username=?', [username])
        userInfo = cur3.fetchall()
        account = True;
        return render_template('account.html', username=username, account=account, phages=phages,
                               userInfo=userInfo, phages2=phages2)
    homepage = True;
    return render_template('homepage.html', homepage=homepage)


@app.route('/about')
def about_home():
    about = True;
    if 'logged_in' in session:
        username = session['logged_in']
        return render_template('about.html', username=username, about=about)
    return render_template('about.html', about=about)


@app.route('/supplement')
def supplement_home():
    supplement = True;
    if 'logged_in' in session:
        username = session['logged_in']
        return render_template('supplements.html', username=username, supplement=supplement)
    return render_template('supplements.html', supplement=supplement)


# Page to enter information for new phages

@app.route('/phages/add')
def redirect_add_phage():
    if 'logged_in' in session:
        username = session['logged_in']
        return render_template('newphages.html', username=username)
    return render_template('login.html')


# Post method executed when adding a new phage to the database

@app.route('/addphage', methods=['POST'])
def add_phage():
    if not session.get('logged_in'):
        abort(401)
    db = get_db()
    time = datetime.now()
    db.execute('INSERT INTO phages (phageName, phageImage, googleDocImages, foundBy, author, yearFound, cityFound, '
               'stateFound, countryFound, gpsLat, gpsLong, soilSample, phageDiscovery, phageNaming, '
               'isoTemp, seqCompleted, seqFacility, seqMethod, genomeLength, genomeEnd, overhangLength, overhangSeq, '
               'gcContent, cluster, clusterLife, annotateStatus, phageMorph, morphType, phamerated, genBank, '
               'genBankLink, archiveStatus, freezerBoxNum, freezerBoxGridNum, fastaFile, fastqFile, rawsequenceFile,'
               'extraFile) '
               'VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, '
               '?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
               [request.form['phageName'], request.form['phageImage'], request.form['googleDocImages'],
                request.form['foundBy'], session['logged_in'], request.form['yearFound'], request.form['cityFound'],
                request.form['stateFound'], request.form['countryFound'], request.form['gpsLat'],
                request.form['gpsLong'], request.form['soilSample'],
                request.form['phageDiscovery'], request.form['phageNaming'], request.form['isoTemp'],
                request.form['seqCompleted'], request.form['seqFacility'], request.form['seqMethod'],
                request.form['genomeLength'], request.form['genomeEnd'], request.form['overhangLength'],
                request.form['overhangSeq'], request.form['gcContent'], request.form['cluster'],
                request.form['clusterLife'], request.form['annotateStatus'], request.form['phageMorph'],
                request.form['morphType'], request.form['phamerated'], request.form['genBank'],
                request.form['genBankLink'], request.form['archiveStatus'], request.form['freezerBoxNum'],
                request.form['freezerBoxGridNum'], request.form['fastaFile'], request.form['fastqFile'],
                request.form['rawsequenceFile'], request.form['extraFile']])
    # db.execute('insert into phageHost (phageName, isolationHost) values (?, ?)', [request.form['phageName'],
    #            request.form['isolationHost']]);
    # , request.form['fastaFile'], request.form['fastqFile'], request.form['rawsequenceFile'], request.form['extraFile']
    db.commit()
    db.execute('INSERT INTO activityLog (phageName, username, datetime, activity) VALUES (?, ?, ?, "Created phage");',
               [request.form['phageName'], session['logged_in'], time])
    db.commit()
    # Commits it to the database
    flash('New phage was successfully saved.')
    return redirect(url_for('phages_page'))


# Showing all phages to view

@app.route('/phages')
def phages_page():
    db = get_db()
    cur = db.execute('SELECT * FROM phages ORDER BY phageName ASC')
    phages = cur.fetchall()
    if 'logged_in' in session:
        username = session['logged_in']
        return render_template('viewphages.html', username=username, phages=phages)
    return render_template('viewphages.html', phages=phages)


# Sorting feature for viewing phages

@app.route('/ASC/Phage')
def phages_asc():
    db = get_db()
    cur = db.execute('SELECT * FROM phages ORDER BY phageName ASC')
    phages = cur.fetchall()
    if 'logged_in' in session:
        username = session['logged_in']
        return render_template('viewphages.html', username=username, phages=phages)
    return render_template('viewphages.html', phages=phages)


@app.route('/ASC/Student')
def student_asc():
    db = get_db()
    cur = db.execute('SELECT * FROM phages ORDER BY foundBy ASC')
    phages = cur.fetchall()
    if 'logged_in' in session:
        username = session['logged_in']
        return render_template('viewphages.html', username=username, phages=phages)
    return render_template('viewphages.html', phages=phages)


@app.route('/ASC/Year')
def year_asc():
    db = get_db()
    cur = db.execute('SELECT * FROM phages ORDER BY yearFound ASC')
    phages = cur.fetchall()
    if 'logged_in' in session:
        username = session['logged_in']
        return render_template('viewphages.html', username=username, phages=phages)
    return render_template('viewphages.html', phages=phages)


@app.route('/ASC/Cluster')
def cluster_asc():
    db = get_db()
    cur = db.execute('SELECT * FROM phages ORDER BY cluster ASC')
    phages = cur.fetchall()
    if 'logged_in' in session:
        username = session['logged_in']
        return render_template('viewphages.html', username=username, phages=phages)
    return render_template('viewphages.html', phages=phages)


@app.route('/DESC/Phage')
def phages_desc():
    db = get_db()
    cur = db.execute('SELECT * FROM phages ORDER BY phageName DESC')
    phages = cur.fetchall()
    if 'logged_in' in session:
        username = session['logged_in']
        return render_template('viewphages.html', username=username, phages=phages)
    return render_template('viewphages.html', phages=phages)


@app.route('/DESC/Student')
def student_desc():
    db = get_db()
    cur = db.execute('SELECT * FROM phages ORDER BY foundBy DESC')
    phages = cur.fetchall()
    if 'logged_in' in session:
        username = session['logged_in']
        return render_template('viewphages.html', username=username, phages=phages)
    return render_template('viewphages.html', phages=phages)


@app.route('/DESC/Year')
def year_desc():
    db = get_db()
    cur = db.execute('SELECT * FROM phages ORDER BY yearFound DESC')
    phages = cur.fetchall()
    if 'logged_in' in session:
        username = session['logged_in']
        return render_template('viewphages.html', username=username, phages=phages)
    return render_template('viewphages.html', phages=phages)


@app.route('/DESC/Cluster')
def cluster_desc():
    db = get_db()
    cur = db.execute('SELECT * FROM phages ORDER BY cluster DESC')
    phages = cur.fetchall()
    if 'logged_in' in session:
        username = session['logged_in']
        return render_template('viewphages.html', username=username, phages=phages)
    return render_template('viewphages.html', phages=phages)


# View specific phage - Phage Information

@app.route('/phages/view')
def full_view():
    if 'logged_in' in session:
        db = get_db()
        cur = db.execute('SELECT * FROM phages WHERE phageName = ?', [request.args['phageName']])
        phages = cur.fetchall()
        # cur2 = db.execute('SELECT * FROM phageHost WHERE phageName = ?', [request.args['phageName']])
        # phageHosts = cur2.fetchall()
        username = session['logged_in']
        return render_template('viewonephage.html', username=username, phages=phages)
    return render_template('login.html')


# View specific phage - Activity Log

@app.route('/phages/view/log')
def full_view_log():
    if 'logged_in' in session:
        db = get_db()
        cur = db.execute('SELECT * FROM phages WHERE phageName = ?', [request.args['phageName']])
        phages = cur.fetchall()
        cur2 = db.execute('SELECT * FROM activityLog WHERE phageName = ? ORDER BY datetime ASC',
                          [request.args['phageName']])
        activityLog = cur2.fetchall()
        username = session['logged_in']
        return render_template('viewphagelog.html', username=username, phages=phages, activityLog=activityLog)
    return render_template('login.html')


# Showing all phages to modify

@app.route('/phages/modify')
def redirect_modify_phage():
    db = get_db()
    cur = db.execute('SELECT * FROM phages ORDER BY phageName ASC')
    phages = cur.fetchall()
    if 'logged_in' in session:
        username = session['logged_in']
        return render_template('editphages.html', username=username, phages=phages)
    return render_template('login.html')


# Sorting feature for modifying phages

@app.route('/phages/modify/ASC/Phage')
def modify_phages_asc():
    db = get_db()
    cur = db.execute('SELECT * FROM phages ORDER BY phageName ASC')
    phages = cur.fetchall()
    if 'logged_in' in session:
        username = session['logged_in']
        return render_template('editphages.html', username=username, phages=phages)
    return render_template('login.html')


@app.route('/phages/modify/ASC/Student')
def modify_student_asc():
    db = get_db()
    cur = db.execute('SELECT * FROM phages ORDER BY foundBy ASC')
    phages = cur.fetchall()
    if 'logged_in' in session:
        username = session['logged_in']
        return render_template('editphages.html', username=username, phages=phages)
    return render_template('login.html')


@app.route('/phages/modify/ASC/Year')
def modify_year_asc():
    db = get_db()
    cur = db.execute('SELECT * FROM phages ORDER BY yearFound ASC')
    phages = cur.fetchall()
    if 'logged_in' in session:
        username = session['logged_in']
        return render_template('editphages.html', username=username, phages=phages)
    return render_template('login.html')


@app.route('/phages/modify/ASC/Cluster')
def modify_cluster_asc():
    db = get_db()
    cur = db.execute('SELECT * FROM phages ORDER BY cluster ASC')
    phages = cur.fetchall()
    if 'logged_in' in session:
        username = session['logged_in']
        return render_template('editphages.html', username=username, phages=phages)
    return render_template('login.html')


@app.route('/phages/modify/DESC/Phage')
def modify_phages_desc():
    db = get_db()
    cur = db.execute('SELECT * FROM phages ORDER BY phageName DESC')
    phages = cur.fetchall()
    if 'logged_in' in session:
        username = session['logged_in']
        return render_template('editphages.html', username=username, phages=phages)
    return render_template('login.html')


@app.route('/phages/modify/DESC/Student')
def modify_student_desc():
    db = get_db()
    cur = db.execute('SELECT * FROM phages ORDER BY foundBy DESC')
    phages = cur.fetchall()
    if 'logged_in' in session:
        username = session['logged_in']
        return render_template('editphages.html', username=username, phages=phages)
    return render_template('login.html')


@app.route('/phages/modify/DESC/Year')
def modify_year_desc():
    db = get_db()
    cur = db.execute('SELECT * FROM phages ORDER BY yearFound DESC')
    phages = cur.fetchall()
    if 'logged_in' in session:
        username = session['logged_in']
        return render_template('editphages.html', username=username, phages=phages)
    return render_template('login.html')


@app.route('/phages/modify/DESC/Cluster')
def modify_cluster_desc():
    db = get_db()
    cur = db.execute('SELECT * FROM phages ORDER BY cluster DESC')
    phages = cur.fetchall()
    if 'logged_in' in session:
        username = session['logged_in']
        return render_template('editphages.html', username=username, phages=phages)
    return render_template('login.html')


# Edit one phage

@app.route('/phages/modify/edit_phage', methods=['GET'])
def edit_a_phage():
    if 'logged_in' in session:
        username = session['logged_in']
        db = get_db()
        if username == 'mgndolan':
            cur = db.execute('SELECT * FROM phages WHERE id = ?',
                             [request.args['id']])
        else:
            cur = db.execute('SELECT * FROM phages WHERE id = ? AND author = ?',
                             [request.args['id'], username])
        phages = cur.fetchall()
        # cur2 = db.execute('SELECT * FROM phageHost WHERE id = ?', [request.args['id']])
        # phageHosts = cur2.fetchall()
        if len(phages) > 0:
            return render_template('editonephage.html', username=username, phages=phages)
        flash('You cannot edit phages you did not create.')
        return redirect(url_for('redirect_modify_phage'))
    return render_template('login.html')


# Post method executed when editing a specific phage

@app.route('/make_changes', methods=['POST'])
def update_phage():
    if 'logged_in' in session:
        db = get_db()
        theid = request.form['id']
        phageName = request.form['phageName']
        phageImage = request.form['phageImage']
        googleDocImages = request.form['googleDocImages']
        foundBy = request.form['foundBy']
        yearFound = request.form['yearFound']
        cityFound = request.form['cityFound']
        stateFound = request.form['stateFound']
        countryFound = request.form['countryFound']
        gpsLat = request.form['gpsLat']
        gpsLong = request.form['gpsLong']
        soilSample = request.form['soilSample']
        phageDiscovery = request.form['phageDiscovery']
        phageNaming = request.form['phageNaming']
        isoTemp = request.form['isoTemp']
        seqCompleted = request.form['seqCompleted']
        seqFacility = request.form['seqFacility']
        seqMethod = request.form['seqMethod']
        genomeLength = request.form['genomeLength']
        genomeEnd = request.form['genomeEnd']
        overhangLength = request.form['overhangLength']
        overhangSeq = request.form['overhangSeq']
        gcContent = request.form['gcContent']
        cluster = request.form['cluster']
        clusterLife = request.form['clusterLife']
        annotateStatus = request.form['annotateStatus']
        phageMorph = request.form['phageMorph']
        morphType = request.form['morphType']
        phamerated = request.form['phamerated']
        genBank = request.form['genBank']
        genBankLink = request.form['genBankLink']
        archiveStatus = request.form['archiveStatus']
        freezerBoxNum = request.form['freezerBoxNum']
        freezerBoxGridNum = request.form['freezerBoxGridNum']
        time = datetime.now()
        # isolationHost = request.form['isolationHost']
        fastaFile = request.form['fastaFile']
        fastqFile = request.form['fastqFile']
        rawsequenceFile = request.form['rawsequenceFile']
        extraFile = request.form['extraFile']
        db.execute('UPDATE phages SET phageName = ?, phageImage = ?, googleDocImages = ?, foundBy = ?, '
                   'yearFound = ?, cityFound = ?, stateFound = ?, countryFound = ?, gpsLat = ?, gpsLong = ?, '
                   'soilSample = ?, phageDiscovery = ?, phageNaming = ?, isoTemp = ?, seqCompleted = ?,'
                   'seqFacility = ?, seqMethod = ?, genomeLength = ?, genomeEnd = ?, overhangLength = ?, '
                   'overhangSeq = ?, gcContent = ?, cluster = ?, clusterLife = ?, annotateStatus = ?, '
                   'phageMorph = ?, morphType = ?, phamerated = ?, genBank = ?, genBankLink = ?, '
                   'archiveStatus = ?, freezerBoxNum = ?, freezerBoxGridNum = ?, fastaFile = ?, '
                   'fastqFile = ?, rawsequenceFile = ?, extraFile = ? WHERE id = ?;',
                   [phageName, phageImage, googleDocImages, foundBy, yearFound, cityFound,
                    stateFound, countryFound, gpsLat, gpsLong, soilSample,
                    phageDiscovery, phageNaming, isoTemp, seqCompleted, seqFacility, seqMethod,
                    genomeLength, genomeEnd, overhangLength, overhangSeq, gcContent, cluster,
                    clusterLife, annotateStatus, phageMorph, morphType, phamerated, genBank,
                    genBankLink, archiveStatus, freezerBoxNum, freezerBoxGridNum, fastaFile,
                    fastqFile, rawsequenceFile, extraFile, theid])
        db.commit()
        # db.execute('UPDATE phageHost SET phageName=?, isolationHost=? WHERE ', [phageName, isolationHost])
        # db.commit()
        db.execute('INSERT INTO activityLog (phageName, username, datetime, activity) VALUES (?, ?, ?, "Updated '
                   'phage information");', [phageName, session['logged_in'], time])
        db.commit()
        flash('Phage was successfully edited')
        return redirect(url_for('phages_page'))
    return redirect(url_for('login_account'))


# Showing all users to view

@app.route('/users')
def show_users():
    db = get_db()
    cur = db.execute('SELECT * FROM accounts ORDER BY firstName ASC')
    users = cur.fetchall()
    if 'logged_in' in session:
        username = session['logged_in']
        user = True;
        return render_template('viewusers.html', username=username, users=users, user=user)
    return redirect(url_for('login_account'))


@app.route('/users/view')
def full_user():
    if 'logged_in' in session:
        db = get_db()
        cur = db.execute('SELECT * FROM phages WHERE author=? ORDER BY phageName ASC', [request.args['theUser']])
        phages = cur.fetchall()
        cur2 = db.execute('SELECT * FROM phages WHERE author=? ORDER BY phageName ASC', [request.args['theUser']])
        phages2 = cur2.fetchall()
        cur3 = db.execute('SELECT * FROM accounts WHERE username=?', [request.args['theUser']])
        users = cur3.fetchall()
        username = session['logged_in']
        return render_template('viewoneuser.html', username=username, users=users, phages=phages, phages2=phages2)
    return render_template('login.html')
