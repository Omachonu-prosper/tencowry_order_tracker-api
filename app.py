import os
from flask import Flask, request, jsonify
from pymongo import MongoClient
from flask_mail import Message, Mail
from dotenv import load_dotenv

app = Flask(__name__)

load_dotenv

try:
    # Flask-Mail config
    app.config['MAIL_SERVER']='smtp.gmail.com'
    app.config['MAIL_PORT'] = 465
    app.config['MAIL_USERNAME'] = os.environ['MAIL_USERNAME']
    app.config['MAIL_PASSWORD'] = os.environ['MAIL_PASSWORD']
    app.config['MAIL_DEFAULT_SENDER'] = os.environ['MAIL_DEFAULT_SENDER']
    app.config['MAIL_USE_TLS'] = False
    app.config['MAIL_USE_SSL'] = True
    mail = Mail(app)
except KeyError as e:
    error = f"Failed to configure flask mail: {e} >>> check environment variables"
    print(error)

try:
    client = MongoClient('mongodb://localhost:27017/')
    db = client['test']
    orders = db['orders']
except Exception as e:
    print(f'Error connection to Database: {e}')


@app.route('/order/<string:order_id>/status', methods=['GET', 'PUT'])
def order_status(order_id):
    if request.method == 'GET':
        order = orders.find_one({'order_id': order_id}, {'_id': 0})
        if order:
            return jsonify({
                'message': f"Order with order id {order_id} retrieved successfully",
                'data': order,
                'status': True
            })
        else:
            return jsonify({
                'message': f"Could not find order with order id {order_id}",
                'data': None,
                'status': False
            }), 404
    elif request.method == 'PUT':
        data = request.json
        status = data.get('status')
        stage = data.get('stage')
        admin_email = data.get('admin-email')
        customer_email = data.get('customer-email')

        # The payload the client sent is incomplete 
        if not status or not stage or not admin_email or not customer_email:
            return jsonify({
                'message': 'Missing required payload',
                'data': None,
                'status': False
            }), 400

        # Update the order status in the database
        update = orders.update_one({'order_id': order_id}, {
            '$set': {
                'status': status,
                'stage': stage
            }
        })
        if update.matched_count == 0:
            return jsonify({
                'message': f"Could not find order with order id {order_id}",
                'data': None,
                'status': False
            }), 404
        
        # Send out emails to admin and customer
        subject = f"Update to order ({order_id}) - {status}"
        recipients = [admin_email, customer_email]
        body = f"The order with order id {order_id} has been updated"
        message = Message(subject=subject, recipients=recipients, body=body)
        mail.send(message)

        return jsonify({
            'message': f"Order with order id {order_id} has been successfully updated",
            'data': None,
            'status': True
        }), 200
        

if __name__ == '__main__':
    app.run(debug=True)