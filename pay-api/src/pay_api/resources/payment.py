# Copyright © 2019 Province of British Columbia
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Resource for Payment endpoints."""
from http import HTTPStatus

from flask import jsonify, request
from flask_restplus import Namespace, Resource, cors

from pay_api import jwt as _jwt
from pay_api.exceptions import BusinessException
from pay_api.schemas import utils as schema_utils
from pay_api.services import PaymentService
from pay_api.utils.roles import Role
from pay_api.utils.util import cors_preflight

API = Namespace('payments', description='Payment System - Payments')


@cors_preflight('POST')
@API.route('', methods=['POST', 'OPTIONS'])
class Payment(Resource):
    """Endpoint resource to create payment."""

    @staticmethod
    @cors.crossdomain(origin='*')
    @_jwt.has_one_of_roles([Role.BASIC.value, Role.PREMIUM.value])
    def post():
        """Create the payment records."""
        request_json = request.get_json()
        # Validate the input request
        valid_format, errors = schema_utils.validate(request_json, 'payment_request')
        if not valid_format:
            return jsonify({'code': 'PAY003', 'message': schema_utils.serialize(errors)}), HTTPStatus.BAD_REQUEST

        try:
            response, status = PaymentService.create_payment(request_json), HTTPStatus.CREATED
        except BusinessException as exception:
            response, status = {'code': exception.code, 'message': exception.message}, exception.status
        return jsonify(response), status
