from flask import jsonify

def response_success(data=None, message="Thành công", code=200):
    return jsonify({
        "status": "success",
        "message": message,
        "data": data
    }), code

def response_error(message="Có lỗi xảy ra", code=400):
    return jsonify({
        "status": "error",
        "message": message
    }), code
