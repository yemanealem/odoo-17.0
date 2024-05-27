import requests
from odoo import http
from werkzeug.exceptions import InternalServerError
from odoo.tools.misc import html_escape
from odoo.http import Controller, request, route, Response  # Add this import
import json

class product(Controller):
    print('welcome')

    @route('/product_list/', website=False, type='http', csrf=False, auth='public')
    def school_profile(self, **kw):
        products = request.env['product.template'].search([])
        products_data = []
        try:

           for product in products:
               products_data.append({
               'id': product.id,
               'dosage_form': product.dosage_form,
               'drug_code': product.drug_code})

           return Response(json.dumps(products_data), content_type='application/json')


        except Exception as e:
            se = http.serialize_exception(e)
            error = {
                'code': 500,
                'message': 'Odoo Server Error',
                'data': se
            }
            res = request.make_response(html_escape(json.dumps(error)))
            raise InternalServerError(response=res) from e

    @route('/check_availability/', website=False, type='http', csrf=False, auth='public')
    def check_if_medecine_exist(self, **kw):
        url = 'http://192.168.137.190:8190/api/electronic/prescription/drug/import'
        data = {'count': '0'}
        try:
            response = requests.post(url, json=data)
            if response.status_code == 200:

                print("Request sent successfully")
            else:

                print("Request failed with status code:", response.status_code)
        except Exception as e:
            print("An error occurred:", e)
