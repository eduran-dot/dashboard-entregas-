from flask import Flask, request, jsonify, render_template, send_from_directory
import pandas as pd
import json
import os
from datetime import datetime, date, timedelta, timezone
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max

DATA_FILE = 'data.json'
UPLOAD_DATE_FILE = 'upload_info.json'
ALLOWED_EXTENSIONS = {'xlsx', 'xls'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def parse_date_str(val):
    if pd.isna(val):
        return None
    s = str(val).strip()
    if not s or s == 'nan':
        return None
    # Try common formats
    for fmt in ('%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M', '%Y-%m-%d', '%d/%m/%Y'):
        try:
            return datetime.strptime(s[:len(fmt)], fmt).strftime('%Y-%m-%d %H:%M' if '%H' in fmt else '%Y-%m-%d')
        except:
            pass
    return s

def process_excel(filepath):
    df = pd.read_excel(filepath)
    df.columns = df.columns.str.strip()

    def find_col(*candidates):
        for c in candidates:
            match = next((k for k in df.columns if k.strip().lower() == c.lower()), None)
            if match:
                return match
        return None

    ref_col     = find_col('Reference Number', 'reference number', 'referencia')
    deliv_col   = find_col('Delivery Successful', 'delivery successful', 'delivery')
    branch_col  = find_col('Destination Branch', 'destination branch', 'hub', 'branch')
    promise_col = find_col('Initial Delivery Date', 'initial delivery date', 'fecha promesa')
    route1_col  = find_col('Order Out for Delivery', 'order out for delivery')
    route2_col  = find_col('Order Out for Delivery 2', 'order out for delivery 2')
    route3_col  = find_col('Order Out for Delivery 3', 'order out for delivery 3')
    tracking_col= find_col('Tracking Status', 'tracking status', 'status')

    if not all([ref_col, deliv_col, branch_col, promise_col]):
        raise ValueError(f'Columnas requeridas no encontradas. Detectadas: {list(df.columns)}')

    has_routes = bool(route1_col or route2_col or route3_col)

    def to_date_str(val):
        if pd.isna(val):
            return None
        if isinstance(val, (datetime, pd.Timestamp)):
            return val.strftime('%Y-%m-%d %H:%M')
        return parse_date_str(val)

    def to_date_only_str(val):
        if pd.isna(val):
            return None
        if isinstance(val, (datetime, pd.Timestamp)):
            return val.strftime('%Y-%m-%d')
        s = str(val).strip()
        if len(s) >= 10:
            return s[:10]
        return s

    rows = []
    for _, r in df.iterrows():
        ref    = str(r[ref_col] or '').strip()
        branch = str(r[branch_col] or '').strip().upper()
        deliv  = to_date_str(r[deliv_col])
        promise= to_date_only_str(r[promise_col])
        route1 = to_date_str(r[route1_col]) if route1_col else None
        route2 = to_date_str(r[route2_col]) if route2_col else None
        route3 = to_date_str(r[route3_col]) if route3_col else None
        tracking = str(r[tracking_col] or '').strip().lower() if tracking_col else ''

        rows.append({
            'ref': ref,
            'branch': branch,
            'delivery': deliv,
            'promise': promise,
            'route1': route1,
            'route2': route2,
            'route3': route3,
            'trackingStatus': tracking,
        })

    return rows, has_routes

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/admin')
def admin():
    return render_template('admin.html')

@app.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        return jsonify({'error': 'No se recibió archivo'}), 400
    file = request.files['file']
    if not file or not allowed_file(file.filename):
        return jsonify({'error': 'Formato no válido. Solo .xlsx o .xls'}), 400
    try:
        filename = secure_filename(file.filename)
        filepath = os.path.join('/tmp', filename)
        file.save(filepath)
        rows, has_routes = process_excel(filepath)
        os.remove(filepath)

        with open(DATA_FILE, 'w') as f:
            json.dump({'rows': rows, 'hasRoutes': has_routes}, f)

        mx_tz = timezone(timedelta(hours=-6))
        now = datetime.now(mx_tz).strftime('%Y-%m-%d %H:%M:%S')
        with open(UPLOAD_DATE_FILE, 'w') as f:
            json.dump({'uploaded_at': now, 'filename': filename, 'total': len(rows)}, f)

        return jsonify({'ok': True, 'total': len(rows), 'hasRoutes': has_routes})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/data')
def get_data():
    if not os.path.exists(DATA_FILE):
        return jsonify({'rows': [], 'hasRoutes': False, 'uploaded_at': None, 'filename': None})
    with open(DATA_FILE) as f:
        data = json.load(f)
    info = {}
    if os.path.exists(UPLOAD_DATE_FILE):
        with open(UPLOAD_DATE_FILE) as f:
            info = json.load(f)
    data.update(info)
    return jsonify(data)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
