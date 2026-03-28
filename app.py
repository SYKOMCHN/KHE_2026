from flask import Flask, render_template, request, jsonify
from backend.db import query, update

app = Flask(__name__)

@app.route('/')
def hello_world():
    return render_template("index.html")

@app.route('/api/query', methods=['POST'])
def execute_query():
    """Execute a SQL query and return results"""
    try:
        data = request.json
        sql_query = data.get('query', '').strip()
        
        if not sql_query:
            return jsonify({'error': 'No query provided'}), 400
        
        # Safety check: prevent dangerous operations
        dangerous_keywords = ['DROP', 'DELETE', 'TRUNCATE', 'ALTER', 'TRUNCATE']
        if any(keyword in sql_query.upper() for keyword in dangerous_keywords):
            return jsonify({'error': 'Query contains dangerous operations'}), 403
        
        # Execute query
        result = query(sql_query)
        if not result:
            return jsonify({'error': 'Query execution failed'}), 400
        
        return jsonify({
            'success': True,
            'columns': result['columns'],
            'rows': result['rows'],
            'row_count': result['row_count']
        })
    
    except Exception as e:
        return jsonify({'error': f'Query error: {str(e)}'}), 400

if __name__ == '__main__':
    app.run(debug=True)
