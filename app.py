from flask import Flask, render_template, request, jsonify
from backend.db import query, update
from backend.climate import get_climate_analyzer

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

@app.route('/api/weather/texas', methods=['GET'])
def get_texas_weather():
    """GET weather data for Texas and regional climate classification"""
    try:
        analyzer = get_climate_analyzer()
        weather_data = analyzer.fetch_and_analyze_texas()
        
        return jsonify({
            'success': True,
            'data': weather_data
        })
    except Exception as e:
        return jsonify({'error': f'Error fetching Texas weather: {str(e)}'}), 500

@app.route('/api/weather/regions', methods=['GET'])
def get_region_distribution():
    """GET distribution of Texas cities by climate region"""
    try:
        analyzer = get_climate_analyzer()
        distribution = analyzer.get_region_distribution()
        
        return jsonify({
            'success': True,
            'regions': distribution
        })
    except Exception as e:
        return jsonify({'error': f'Error fetching regions: {str(e)}'}), 500

@app.route('/api/weather/city/<city>', methods=['GET'])
def get_city_weather(city):
    """GET weather data for a specific city with climate classification"""
    try:
        analyzer = get_climate_analyzer()
        city_data = analyzer.analyze_city(city)
        
        if not city_data:
            return jsonify({'error': f'Could not fetch weather for {city}'}), 404
        
        return jsonify({
            'success': True,
            'data': city_data
        })
    except Exception as e:
        return jsonify({'error': f'Error fetching city weather: {str(e)}'}), 500

@app.route('/api/climate/region/<region>', methods=['GET'])
def get_cities_in_region(region):
    """GET all Texas cities classified in a specific climate region"""
    try:
        valid_regions = ['desert', 'arctic', 'tropic', 'temperate']
        
        if region.lower() not in valid_regions:
            return jsonify({'error': f'Invalid region. Choose from: {valid_regions}'}), 400
        
        analyzer = get_climate_analyzer()
        cities = analyzer.get_region_cities(region.lower())
        
        return jsonify({
            'success': True,
            'region': region,
            'cities': cities,
            'count': len(cities)
        })
    except Exception as e:
        return jsonify({'error': f'Error fetching region data: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(debug=True)
