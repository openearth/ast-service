import os

# AST 2.0
from ast_python.ast_selection import *
from ast_python.ast_heatstress import *
from ast_python.ast_pluvflood import *
from ast_python.ast_groundwater_recharge import *
from ast_python.ast_evapotranspiration import *
from ast_python.web_map import *
from errors import error_handler

# FLASK
from apispec import APISpec
from apispec.ext.marshmallow import MarshmallowPlugin
from flask_apispec.extension import FlaskApiSpec
from flask_apispec import use_kwargs, marshal_with
from webargs import fields
from flask import Flask
from flask import request, jsonify
from flask_cors import CORS
from marshmallow import validate

# FLASK app
application = Flask(__name__)
application.config.update({
    'APISPEC_SPEC': APISpec(
        title='AST2.0 Backend',
        version='v1',
        openapi_version="2.0.0",
        plugins=[MarshmallowPlugin()],
    ),
    'APISPEC_SWAGGER_URL': '/api/swagger/',
    'APISPEC_SWAGGER_UI_URL': '/api/swagger-ui/',
})
docs = FlaskApiSpec(application)
CORS(application)

application.register_blueprint(error_handler)

# /
@application.route('/')
def empty_view():
    0/0
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
        res = {'name': 'Invalid JSON request', 'code': 400, 'description': str(e)}
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
        res = {'name': 'Invalid JSON request', 'code': 400, 'description': str(e)}
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
        res = {'name': 'Invalid JSON request', 'code': 400, 'description': str(e)}
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
        res = {'name': 'Invalid JSON request', 'code': 400, 'description': str(e)}
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
        res = {'name': 'Invalid JSON request', 'code': 400, 'description': str(e)}
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
        res = {'name': 'Invalid JSON request', 'code': 400, 'description': str(e)}
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
        res = {'name': 'Invalid JSON request', 'code': 400, 'description': str(e)}
        status = 400
    return jsonify({'result': res}), status


# /api/measures
@application.route('/api/measures', methods=['GET'])
@use_kwargs({"scenarioName": fields.Str(required=True, default="city_center")})
def _ast_calc_measures(scenarioName):
    """Replaced by DATO store."""
    try:
        # Depending on scenario name
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
        res = {'name': 'Invalid JSON request', 'code': 400, 'description': str(e)}
        status = 400
    return jsonify({'result': res}), status


# /api/scores
@application.route('/api/scores', methods=['GET'])
def ast_calc_scores():

    res = {}
    ast_dir = os.path.dirname(os.path.realpath(__file__))
    with open(os.path.join(ast_dir, 'tables/ast_scores.json')) as f:
        res['scores'] = json.load(f)
    with open(os.path.join(ast_dir, 'tables/ast_selection_scores.json')) as f:
        res['selection_scores'] = json.load(f)

    return jsonify({'result': res}), status


@application.route("/api/maplayers", methods=['GET', 'POST'])
@use_kwargs({"url": fields.Str(required=True), "type": fields.Str()})
def maplayers(url, **kwargs):
    """Parse given url as a possible map layer
    and returns Mapbox compatible url."""
    type = kwargs.get("type", "GUESS")
    return jsonify(layerurl(url, type))

@application.route("/api/mapsetup", methods=['GET', 'POST'])
@use_kwargs({"url": fields.Str(required=True),
             "layer": fields.Str(required=True),
             "area": fields.Dict(required=True),
             "field": fields.Str(required=True),
             "srs": fields.Int(default=28992)})
def mapsetup(url, layer, area, field, **kwargs):
    """Parse WFS layer for given bounding box."""
    return jsonify(wfs_area_parser(url, layer, area, field))


# Register documentation endpoints
docs.register(maplayers)
docs.register(ast_calc_scores)
docs.register(_ast_calc_measures)


# Main
if __name__ == "__main__":
    application.run(host='0.0.0.0', debug=True)
