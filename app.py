from flask import Flask, render_template, request, session, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
import pandas as pd
import plotly.express as px
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'zuhoor2024'
UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:gazi706948@mysql/zuhoor_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

ROWS_PER_ROUND = 1000


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    naam = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    profession = db.Column(db.String(100), nullable=False)
    company = db.Column(db.String(100), nullable=False)
    city = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    joined_on = db.Column(db.DateTime, default=datetime.utcnow)


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


def read_file(filepath):
    ext = filepath.rsplit('.', 1)[1].lower()
    if ext == 'csv':
        return pd.read_csv(filepath)
    elif ext == 'xlsx':
        return pd.read_excel(filepath)
    elif ext == 'json':
        return pd.read_json(filepath)
    return None


def generate_charts(df):
    charts = []
    numeric_cols = df.select_dtypes(include='number').columns.tolist()
    categorical_cols = df.select_dtypes(include='object').columns.tolist()

    layout = dict(
        paper_bgcolor='#ffffff',
        plot_bgcolor='#ffffff',
        font=dict(family='Inter, Arial, sans-serif', color='#1a3d2b', size=13),
        title_font=dict(family='Inter, Arial, sans-serif', size=18, color='#1a3d2b'),
        margin=dict(l=40, r=30, t=60, b=50),
        colorway=['#2d6a4f', '#52b788', '#74c69d', '#95d5b2', '#1b4332', '#40916c'],
        legend=dict(
            bgcolor='#f0f7f0', bordercolor='#b7e4c7', borderwidth=2,
            font=dict(size=12, family='Inter', color='#1a3d2b'),
            orientation='h', yanchor='bottom', y=-0.3, xanchor='center', x=0.5
        ),
        xaxis=dict(
            showgrid=True, gridcolor='#f0f7f0', gridwidth=1,
            linecolor='#b7e4c7', linewidth=2,
            tickfont=dict(size=12, family='Inter', color='#2d6a4f'),
            title_font=dict(size=14, family='Inter', color='#1a3d2b'),
            showline=True, zeroline=False
        ),
        yaxis=dict(
            showgrid=True, gridcolor='#f0f7f0', gridwidth=1,
            linecolor='#b7e4c7', linewidth=2,
            tickfont=dict(size=12, family='Inter', color='#2d6a4f'),
            title_font=dict(size=14, family='Inter', color='#1a3d2b'),
            showline=True, zeroline=False
        )
    )

    try:
        if categorical_cols and numeric_cols:
            agg_df = df.groupby(categorical_cols[0])[numeric_cols[0]].sum().reset_index()
            agg_df = agg_df.sort_values(numeric_cols[0], ascending=False).head(15)
            fig = px.bar(agg_df, x=categorical_cols[0], y=numeric_cols[0],
                        title='Bar Chart: ' + numeric_cols[0] + ' by ' + categorical_cols[0],
                        color=numeric_cols[0],
                        color_continuous_scale=['#d8f3dc', '#52b788', '#1b4332'],
                        text=numeric_cols[0])
            fig.update_traces(texttemplate='%{text:,.0f}', textposition='outside',
                            textfont=dict(size=11, family='Inter', color='#1a3d2b'),
                            marker_line_width=0)
            fig.update_layout(**layout)
            fig.update_coloraxes(showscale=False)
            charts.append(('Bar Chart', fig.to_html(full_html=False)))
    except Exception as e:
        print('Bar chart error: ' + str(e))

    try:
        if numeric_cols:
            cols = numeric_cols[:3]
            fig = px.line(df.reset_index(), x='index', y=cols,
                         title='Trend Analysis Over Rows', markers=True,
                         color_discrete_sequence=['#2d6a4f', '#52b788', '#74c69d'])
            fig.update_traces(line=dict(width=3), marker=dict(size=6))
            fig.update_layout(**layout)
            charts.append(('Line Chart', fig.to_html(full_html=False)))
    except Exception as e:
        print('Line chart error: ' + str(e))

    try:
        if categorical_cols and numeric_cols:
            pie_df = df.groupby(categorical_cols[0])[numeric_cols[0]].sum().reset_index()
            pie_df = pie_df.sort_values(numeric_cols[0], ascending=False).head(8)
            fig = px.pie(pie_df, names=categorical_cols[0], values=numeric_cols[0],
                        title='Distribution: ' + numeric_cols[0],
                        color_discrete_sequence=['#1b4332', '#2d6a4f', '#40916c',
                                                 '#52b788', '#74c69d', '#95d5b2',
                                                 '#b7e4c7', '#d8f3dc'])
            fig.update_traces(textposition='inside', textinfo='percent+label',
                            textfont=dict(size=13, family='Inter', color='white'),
                            pull=[0.05] + [0] * 7,
                            marker=dict(line=dict(color='white', width=3)))
            pie_layout = layout.copy()
            pie_layout.pop('xaxis', None)
            pie_layout.pop('yaxis', None)
            fig.update_layout(**pie_layout)
            charts.append(('Pie Chart', fig.to_html(full_html=False)))
    except Exception as e:
        print('Pie chart error: ' + str(e))

    try:
        if len(numeric_cols) >= 2:
            sample = df.sample(min(500, len(df)))
            fig = px.scatter(sample, x=numeric_cols[0], y=numeric_cols[1],
                            title=numeric_cols[0] + ' vs ' + numeric_cols[1],
                            color_discrete_sequence=['#2d6a4f'])
            fig.update_traces(marker=dict(size=9, opacity=0.75,
                                         line=dict(width=1, color='white')))
            fig.update_layout(**layout)
            charts.append(('Scatter Plot', fig.to_html(full_html=False)))
    except Exception as e:
        print('Scatter error: ' + str(e))

    try:
        if numeric_cols:
            fig = px.histogram(df, x=numeric_cols[0],
                              title='Frequency Distribution: ' + numeric_cols[0],
                              color_discrete_sequence=['#52b788'], nbins=30)
            fig.update_traces(marker_line_color='white',
                            marker_line_width=1.5, opacity=0.85)
            fig.update_layout(**layout)
            charts.append(('Histogram', fig.to_html(full_html=False)))
    except Exception as e:
        print('Histogram error: ' + str(e))

    try:
        if len(numeric_cols) >= 2:
            corr = df[numeric_cols].corr().round(2)
            fig = px.imshow(corr, title='Correlation Heatmap',
                           color_continuous_scale=['#d8f3dc', '#52b788', '#1b4332'],
                           text_auto=True, aspect='auto')
            fig.update_traces(textfont=dict(size=13, family='Inter', color='white'))
            heatmap_layout = layout.copy()
            heatmap_layout.pop('xaxis', None)
            heatmap_layout.pop('yaxis', None)
            fig.update_layout(**heatmap_layout)
            charts.append(('Heatmap', fig.to_html(full_html=False)))
    except Exception as e:
        print('Heatmap error: ' + str(e))

    return charts


@app.route('/')
def home():
    if current_user.is_authenticated:
        return redirect(url_for('upload'))
    return redirect(url_for('login'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        naam = request.form['naam']
        email = request.form['email']
        password = bcrypt.generate_password_hash(request.form['password']).decode('utf-8')
        profession = request.form['profession']
        company = request.form['company']
        city = request.form['city']
        phone = request.form['phone']
        existing = User.query.filter_by(email=email).first()
        if existing:
            flash('Email already registered! Please login.', 'error')
            return redirect(url_for('register'))
        user = User(naam=naam, email=email, password=password,
                   profession=profession, company=company,
                   city=city, phone=phone)
        db.session.add(user)
        db.session.commit()
        flash('Account created! Please login.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()
        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('upload'))
        else:
            flash('Invalid email or password!', 'error')
    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    if request.method == 'POST' and 'file' in request.files:
        file = request.files['file']
        if file and file.filename:
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            file.save(filepath)
            df = read_file(filepath)
            session['filepath'] = filepath
            session['filename'] = file.filename
            session['total_rows'] = len(df)
            session['total_rounds'] = (len(df) + ROWS_PER_ROUND - 1) // ROWS_PER_ROUND
            session['round'] = 1
            return redirect(url_for('dashboard', round=1))
    return render_template('index.html')


@app.route('/dashboard')
@login_required
def dashboard():
    round_num = int(request.args.get('round', 1))
    filepath = session.get('filepath')
    filename = session.get('filename', '')
    total_rows = session.get('total_rows', 0)
    total_rounds = session.get('total_rounds', 1)

    if not filepath:
        return redirect(url_for('upload'))

    df = read_file(filepath)
    start = (round_num - 1) * ROWS_PER_ROUND
    end = start + ROWS_PER_ROUND
    df_round = df.iloc[start:end]
    actual_end = min(end, total_rows)

    charts = generate_charts(df_round)
    preview = df_round.head(5).to_html(classes='preview-table', index=False)

    stats = {
        'rows': len(df_round),
        'cols': df.shape[1],
        'numeric': len(df_round.select_dtypes(include='number').columns),
        'categorical': len(df_round.select_dtypes(include='object').columns)
    }

    return render_template('dashboard.html',
                           charts=charts, preview=preview, stats=stats,
                           filename=filename, round_num=round_num,
                           total_rounds=total_rounds, total_rows=total_rows,
                           start_row=start + 1, end_row=actual_end)


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
