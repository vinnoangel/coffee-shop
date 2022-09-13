import os
from flask import Flask, request, jsonify
import json
from flask_cors import CORS

from .database.models import db_drop_and_create_all, setup_db, Drink
from .auth.auth import AuthError, requires_auth
from .constants.http_status_codes import *
from .error_handler import http_error_handler

app = Flask(__name__)
setup_db(app)
CORS(app)

'''
@TODO uncomment the following line to initialize the datbase
!! NOTE THIS WILL DROP ALL RECORDS AND START YOUR DB FROM SCRATCH
!! NOTE THIS MUST BE UNCOMMENTED ON FIRST RUN
!! Running this funciton will add one
'''

# db_drop_and_create_all()

# ROUTES
'''
@TODO implement endpoint
    GET /drinks
        it should be a public endpoint
        it should contain only the drink.short() data representation
    returns status code 200 and json {"success": True, "drinks": drinks} where drinks is the list of drinks
        or appropriate status code indicating reason for failure
'''

@app.route('/drinks', methods=['GET'])
def get_drinks():
    drinks = Drink.query.all()
    drinks_formatted = [drink.short() for drink in drinks]

    return jsonify({
        "success": True, 
        "drinks": drinks_formatted
    })

'''
@TODO implement endpoint
    GET /drinks-detail
        it should require the 'get:drinks-detail' permission
        it should contain the drink.long() data representation
    returns status code 200 and json {"success": True, "drinks": drinks} where drinks is the list of drinks
        or appropriate status code indicating reason for failure
'''

@app.route('/drinks-detail', methods=['GET'])
@requires_auth('get:drinks-detail')
def get_drinks_detail(payload):
    drinks = Drink.query.all()
    drinks_formatted = [drink.long() for drink in drinks]

    return jsonify({
        "success": True, 
        "drinks": drinks_formatted
    })

'''
@TODO implement endpoint
    POST /drinks
        it should create a new row in the drinks table
        it should require the 'post:drinks' permission
        it should contain the drink.long() data representation
    returns status code 200 and json {"success": True, "drinks": drink} where drink an array containing only the newly created drink
        or appropriate status code indicating reason for failure
'''

@app.route('/drinks', methods=['POST'])
@requires_auth('post:drinks')
def new_drinks(payload):
    # get post requests
    body = request.get_json()
    title = body.get("title")
    recipe = json.dumps(body.get('recipe'))

    if not title:
        return http_error_handler(error=HTTP_400_BAD_REQUEST, message="Drink title is empty")

    if not recipe:
        return http_error_handler(error=HTTP_400_BAD_REQUEST, message="Drink recipe is empty")
    
    # if not color:
    #     return http_error_handler(error=HTTP_400_BAD_REQUEST, message="Drink recipe color is empty")

    # if not part:
    #     return http_error_handler(error=HTTP_400_BAD_REQUEST, message="Drink recipe part is empty")
    # elif type(part) != int:
    #     return http_error_handler(error=HTTP_400_BAD_REQUEST, message="Drink recipe part must be a number")

    drink = Drink.query.filter(Drink.title==title).one_or_none()
    if drink:
        return http_error_handler(error=HTTP_409_CONFLICT, message="Drink already exist")

    # insert new drink and persist drink in the database
    drink = Drink(title=title, recipe=recipe)
    drink.insert()

    return jsonify({
        "success": True, 
        "drinks": drink.long()
    })

'''
@TODO implement endpoint
    PATCH /drinks/<id>
        where <id> is the existing model id
        it should respond with a 404 error if <id> is not found
        it should update the corresponding row for <id>
        it should require the 'patch:drinks' permission
        it should contain the drink.long() data representation
    returns status code 200 and json {"success": True, "drinks": drink} where drink an array containing only the updated drink
        or appropriate status code indicating reason for failure
'''

@app.route('/drinks/<int:id>', methods=['PATCH'])
@requires_auth('patch:drinks')
def update_drinks(payload, id):
    
    drink_to_update = Drink.query.filter(Drink.id==id).one_or_none()
    if not drink_to_update:
        return http_error_handler(error=HTTP_404_NOT_FOUND, message="Drink ID of "+ str(id) +" does not exist")
    
    # get post requests
    body = request.get_json()

    if 'title' in body:
        title = body.get('title')
        drink = Drink.query.filter(Drink.title==title).one_or_none()
        if drink:
            if drink.id != id:
                return http_error_handler(error=HTTP_409_CONFLICT, message="Drink already exist")
        drink_to_update.title = title
    
    if 'recipe' in body:
        drink_to_update.recipe = json.dumps(body.get('recipe'))

    # update drink and persist drink in the database
    drink_to_update.update()

    drinks_formatted = [drink.long() for drink in Drink.query.all()]

    return jsonify({
        "success": True, 
        "drinks": drinks_formatted
    })

'''
@TODO implement endpoint
    DELETE /drinks/<id>
        where <id> is the existing model id
        it should respond with a 404 error if <id> is not found
        it should delete the corresponding row for <id>
        it should require the 'delete:drinks' permission
    returns status code 200 and json {"success": True, "delete": id} where id is the id of the deleted record
        or appropriate status code indicating reason for failure
'''

@app.route('/drinks/<int:id>', methods=['DELETE'])
@requires_auth('delete:drinks')
def delete_drinks(payload, id):

    drink = Drink.query.filter(Drink.id==id).one_or_none()
    if not drink:
        return http_error_handler(error=HTTP_404_NOT_FOUND, message="Drink ID of "+ str(id) +" does not exist")

    drink.delete()

    return jsonify({
        "success": True, 
        "delete": id
    })

# Error Handling
'''
@TODO implement error handlers using the @app.errorhandler(error) decorator
    each error handler should return (with approprate messages):
             jsonify({
                    "success": False,
                    "error": 404,
                    "message": "resource not found"
                    }), 404

'''

'''
@TODO implement error handler for 404
    error handler should conform to general task above
'''
@app.errorhandler(HTTP_400_BAD_REQUEST)
def bad_request(error):
    return http_error_handler(HTTP_400_BAD_REQUEST, "bad request")

@app.errorhandler(HTTP_401_UNAUTHORIZED)
def unauthorized(error):
    return http_error_handler(HTTP_401_UNAUTHORIZED, "unauthorized")

@app.errorhandler(HTTP_403_FORBIDDEN)
def forbidden(error):
    return http_error_handler(HTTP_403_FORBIDDEN, "forbidden")

@app.errorhandler(HTTP_404_NOT_FOUND)
def not_found(error):
    return http_error_handler(HTTP_404_NOT_FOUND, "resource not found")
    
@app.errorhandler(HTTP_405_METHOD_NOT_ALLOWED)
def method_not_allowed(error):
    return http_error_handler(HTTP_405_METHOD_NOT_ALLOWED, "method not allowed")
    
@app.errorhandler(HTTP_408_REQUEST_TIMEOUT)
def request_timeout(error):
    return http_error_handler(HTTP_408_REQUEST_TIMEOUT, "request timeout")
    
@app.errorhandler(HTTP_409_CONFLICT)
def conflict(error):
    return http_error_handler(HTTP_409_CONFLICT, "request conflicts")
    
@app.errorhandler(HTTP_422_UNPROCESSABLE_ENTITY)
def unprocessable(error):
    return http_error_handler(HTTP_422_UNPROCESSABLE_ENTITY, "unprocessable")
    
@app.errorhandler(HTTP_500_INTERNAL_SERVER_ERROR)
def internal_server_error(error):
    return http_error_handler(HTTP_500_INTERNAL_SERVER_ERROR, "internal server error")


'''
@TODO implement error handler for AuthError
    error handler should conform to general task above
'''

@app.errorhandler(AuthError)
def process_AuthError(error):
    response = jsonify(error.error)
    response.status_code = error.status_code

    return response
