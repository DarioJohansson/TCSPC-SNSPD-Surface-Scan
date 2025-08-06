from flask import Blueprint, request, jsonify
from devices.idq_tc1000_photon_counter import *
from devices.idq_tc1000_photon_tol import *


idq_bp = Blueprint('idq_bp', __name__)

# ⬇️ Example endpoint: Get status
@idq_bp.route("/status", methods=["GET"])
def get_status():
    # Example: call your device control module here
    # status = idq.get_status()
    return jsonify({"message": "Status endpoint hit."})

# ⬇️ Example endpoint: Trigger operation
@idq_bp.route("/start_acquisition", methods=["POST"])
def start_acquisition():
    # payload = request.json
    # result = idq.start_acquisition(**payload)
    return jsonify({"message": "Acquisition started."})
