import os

# AST 2.0
from ast_python.ast_selection import *
from ast_python.ast_heatstress import *
from ast_python.ast_pluvflood import *

# FLASK
from flask import Flask
from flask import request, jsonify

# FLASK app
application = Flask(__name__)

# /
@application.route('/')
def empty_view(self):
    content = {'please move along': 'nothing to see here, perhaps looking for /api?'}
    return content, 404

# /api/selection
@application.route('/api/selection', methods=['GET', 'POST'])
def ast_calc_selection():
	try:
	    json_data = request.get_json()
	    res = selection_dict(json_data)
	    status = 200
	except:
		res = { 'error': 'Invalid JSON request', 'code': 400 }
		status = 400
	return jsonify(res), status

# /api/pluvflood
@application.route('/api/pluvflood', methods=['GET', 'POST'])
def ast_calc_pluvflood():
	try:
	    json_data = request.get_json()
	    res = pluvflood_dict(json_data)
	    status = 200
	except:
		res = { 'error': 'Invalid JSON request', 'code': 400 }
		status = 400
	return jsonify({'result': res}), status

# /api/heatstress/temperature
@application.route('/api/heatstress/temperature', methods=['GET', 'POST'])
def ast_calc_heatstress_temperature():
	try:
	    json_data = request.get_json()
	    res = temperature_dict(json_data)
	    status = 200
	except:
		res = { 'error': 'Invalid JSON request', 'code': 400 }
		status = 400
	return jsonify({'result': res}), status

# /api/heatstress/waterquality
@application.route('/api/heatstress/waterquality', methods=['GET', 'POST'])
def ast_calc_heatstress_waterquality():
	try:
	    json_data = request.get_json()
	    res = waterquality_dict(json_data)
	    status = 200
	except:
		res = { 'error': 'Invalid JSON request', 'code': 400 }
		status = 400
	return jsonify({'result': res}), status

# /api/heatstress/cost
@application.route('/api/heatstress/cost', methods=['GET', 'POST'])
def ast_calc_heatstress_cost():
	try:
	    json_data = request.get_json()
	    res = cost_dict(json_data)
	    status = 200
	except:
		res = { 'error': 'Invalid JSON request', 'code': 400 }
		status = 400
	return jsonify({'result': res}), status	

# Measures
@application.route('/api/measures', methods=['GET'])
def ast_calc_measures():
	try:
		res = {}
		ast_dir = os.path.dirname(os.path.realpath(__file__))

		with open(os.path.join(ast_dir, 'tables/ast_measures.json')) as f:
			res['measures'] = json.load(f)			
		with open(os.path.join(ast_dir, 'tables/ast_measures_cost.json')) as f:
			res['measures_cost'] = json.load(f)		
		with open(os.path.join(ast_dir, 'tables/ast_measures_pluvflood.json')) as f:
			res['measures_pluvflood'] = json.load(f)		
		with open(os.path.join(ast_dir, 'tables/ast_measures_temperature.json')) as f:
			res['measures_temperature'] = json.load(f)		
		with open(os.path.join(ast_dir, 'tables/ast_measures_wq.json')) as f:
			res['measures_wq'] = json.load(f)
		
		status = 200
	except:
		res = { 'error': 'Internal server error, check measures files', 'code': 500 }
		status = 500
	return jsonify({'result': res}), status

# Main
if __name__ == "__main__":
    application.run(host='0.0.0.0', debug=True)
