import os

# AST 2.0
from ast_python.ast_selection import *
from ast_python.ast_heatstress import *
from ast_python.ast_pluvflood import *
from ast_python.ast_groundwater_recharge import *
from ast_python.ast_evapotranspiration import *
from ast_python.web_map import *

# FLASK
from flask import Flask
from flask import request, jsonify
from flask_cors import CORS

# FLASK app
application = Flask(__name__)
CORS(application)


# /
@application.route('/')
def empty_view():
    content = {'please move along': 'nothing to see here, perhaps looking for /api?'}
    return jsonify(content)

# /api/selection
@application.route('/api/selection', methods=['GET', 'POST'])
def ast_calc_selection():
    try:
        json_data = request.get_json()
        res = selection_dict(json_data)
        status = 200
    except Exception as e:
        res = {'error': 'Invalid JSON request', 'code': 400, 'msg': str(e)}
        status = 400
    return jsonify({'result': res}), status

# /api/pluvflood
@application.route('/api/pluvflood', methods=['GET', 'POST'])
def ast_calc_pluvflood():
    try:
        json_data = request.get_json()
        res = pluvflood_dict(json_data)
        status = 200
    except Exception as e:
        res = {'error': 'Invalid JSON request', 'code': 400, 'msg': str(e)}
        status = 400
    return jsonify({'result': res}), status

# /api/evapotranspiration
@application.route('/api/evapotranspiration', methods=['GET', 'POST'])
def ast_calc_evapotranspiration():
    try:
        json_data = request.get_json()
        res = evapotranspiration_dict(json_data)
        status = 200
    except Exception as e:
        res = {'error': 'Invalid JSON request', 'code': 400, 'msg': str(e)}
        status = 400
    return jsonify({'result': res}), status

# /api/groundwater_recharge
@application.route('/api/groundwater_recharge', methods=['GET', 'POST'])
def ast_calc_groundwater_recharge():
    try:
        json_data = request.get_json()
        res = groundwater_recharge_dict(json_data)
        status = 200
    except Exception as e:
        res = {'error': 'Invalid JSON request', 'code': 400, 'msg': str(e)}
        status = 400
    return jsonify({'result': res}), status

# /api/heatstress/temperature
@application.route('/api/heatstress/temperature', methods=['GET', 'POST'])
def ast_calc_heatstress_temperature():
    try:
        json_data = request.get_json()
        res = temperature_dict(json_data)
        status = 200
    except Exception as e:
        res = {'error': 'Invalid JSON request', 'code': 400, 'msg': str(e)}
        status = 400
    return jsonify({'result': res}), status

# /api/heatstress/waterquality
@application.route('/api/heatstress/waterquality', methods=['GET', 'POST'])
def ast_calc_heatstress_waterquality():
    try:
        json_data = request.get_json()
        res = waterquality_dict(json_data)
        status = 200
    except Exception as e:
        res = {'error': 'Invalid JSON request', 'code': 400, 'msg': str(e)}
        status = 400
    return jsonify({'result': res}), status

# /api/heatstress/cost
@application.route('/api/heatstress/cost', methods=['GET', 'POST'])
def ast_calc_heatstress_cost():
    try:
        json_data = request.get_json()
        res = cost_dict(json_data)
        status = 200
    except Exception as e:
        res = {'error': 'Invalid JSON request', 'code': 400, 'msg': str(e)}
        status = 400
    return jsonify({'result': res}), status


# /api/measures
@application.route('/api/measures', methods=['GET'])
def _ast_calc_measures():
    """Replaced by DATO store."""
    try:
        # Depending on scenario name
        scenarioName = request.args.get('scenarioName')
        if scenarioName == None:
            scenarioName = 'city_center'  # default

        res = {}
        ast_dir = os.path.dirname(os.path.realpath(__file__))

        with open(os.path.join(ast_dir, 'tables/ast_measures.json')) as f:
            res['measures'] = json.load(f)
        with open(os.path.join(ast_dir, 'tables/' + scenarioName + '/ast_measures_cost.json')) as f:
            res['measures_cost'] = json.load(f)
        with open(os.path.join(ast_dir, 'tables/' + scenarioName + '/ast_measures_pluvflood.json')) as f:
            res['measures_pluvflood'] = json.load(f)
        with open(os.path.join(ast_dir, 'tables/' + scenarioName + '/ast_measures_temperature.json')) as f:
            res['measures_temperature'] = json.load(f)
        with open(os.path.join(ast_dir, 'tables/' + scenarioName + '/ast_measures_wq.json')) as f:
            res['measures_wq'] = json.load(f)

        status = 200
    except Exception as e:
        res = {'error': 'Invalid JSON request', 'code': 400, 'msg': str(e)}
        status = 400
    return jsonify({'result': res}), status

# /api/scores
@application.route('/api/scores', methods=['GET'])
def ast_calc_scores():
    try:
        res = {}
        ast_dir = os.path.dirname(os.path.realpath(__file__))

        with open(os.path.join(ast_dir, 'tables/ast_scores.json')) as f:
            res['scores'] = json.load(f)
        with open(os.path.join(ast_dir, 'tables/ast_selection_scores.json')) as f:
            res['selection_scores'] = json.load(f)

        status = 200
    except Exception as e:
        res = {'error': 'Invalid JSON request', 'code': 400, 'msg': str(e)}
        status = 400
    return jsonify({'result': res}), status


@application.route('/api/maplayers', methods=['GET', 'POST'])
def maplayers():
    url = request.args.get("url", None)
    type = request.args.get("type", "GUESS")
    if url is not None:
        return jsonify(layerurl(url, type))
    else:
        logging.error("400")
        return jsonify({}), 400


# Main
if __name__ == "__main__":
    application.run(host='0.0.0.0', debug=True)
