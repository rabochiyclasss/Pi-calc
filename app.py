from flask import Flask, request, jsonify
from celery import Celery
from celery.result import AsyncResult
from mpmath import mp, mpf
import os

app = Flask(__name__)

app.config['CELERY_BROKER_URL'] = os.getenv('CELERY_BROKER_URL', 'redis://redis:6379/0')
app.config['CELERY_RESULT_BACKEND'] = os.getenv('CELERY_RESULT_BACKEND', 'redis://redis:6379/0')

celery = Celery(
	app.name,
	broker=app.config['CELERY_BROKER_URL'],
	backend=app.config['CELERY_RESULT_BACKEND']
)
celery.conf.update(app.config)

@celery.task(bind=True)
def calculate_pi_task(self, n_digits: int) -> str:
	"""
	Args:
		n_digits: Number of decimal places to calculate
	Returns:
		String representation of Pi with n decimal places
	"""

	self.update_state(state='PROGRESS', meta={'progress': 0.0, 'result':None})
	array_size = int(10 * n_digits / 3) + 1
	digits = [2] * array_size
	result = "3."

	for i in range(n_digits):
		carry = 0

		for j in range(array_size - 1, -1, -1):
			temp = digits[j] * 10 + carry
			carry = temp //(2 * j + 1)
			digits[j] = temp % (2 * j + 1)

		digit = carry % 10
		result += str(digit)

		if i % max(1, n_digits // 10) == 0:
			progress = min(i / n_digits, 0.99)
			self.update_state(
				state='PROGRESS',
				meta={'progress': progress, 'result': None}
			)
	self.update_state(state='PROGRESS', meta={'progress': 1.0, 'result': result})
	return result

@app.route('/')
def index():
	documentation = {
		"name": "Pi Calculator API",
		"version": "1.0.0",
		"description": "Asynchronous Pi calculation using Celery",
		"endpoints": {
			"/calculate_pi": {
				"method": "GET",
				"description": "Start Pi calculation task",
				"parameters": {
					"n": {
						"type": "integer",
						"required": True,
						"description": "Number of decimal places to calculate",
						"example": 123
					}
				},
				"example": "/calculate_pi?n=123",
				"response": {
					"task_id": "uuid-string",
					"status": "Task started"
				}
			},
			"/check_progress": {
				"method": "GET",
				"description": "Check progress of a calculation task",
				"parameters": {
					"task_id": {
						"type": "string",
						"required": True,
						"description": "Task ID returned from /calculate_pi",
						"example": "810f8431-h29k-21p4-v786-246600441230"
					}
				},
				"example": "/check_progress?task_id=810f8431-h29k-21p4-v786-246600441230",
				"response": {
					"state": "PROGRESS or FINISHED",
					"progress": "float between 0 and 1",
					"result": "incomplete Pi value or complete Pi value as string"
				}
			}
		}
	}
	return jsonify(documentation)

@app.route('/calculate_pi', methods=['GET'])
def calculate_pi():
	"""
	Start an asynchronous Pi calculation.
	
	Query Parameters:
		n (int): Number of decimal places to calculate
		
	Returns:
		JSON with task_id and status
	"""
	try:
		n = request.args.get('n', type=int)
		
		if n is None:
			return jsonify({
				"error": "Missing required parameter 'n'",
				"example": "/calculate_pi?n=123"
			}), 400
			
		if n <= 0:
			return jsonify({
				"error": "Parameter 'n' must be positive",
				"provided": n
			}), 400
		
		task = calculate_pi_task.apply_async(args=[n])
		
		return jsonify({
			"task_id": task.id,
			"status": "Task started",
			"message": f"Calculating Pi to {n} decimal places"
		}), 202
		
	except Exception as e:
		return jsonify({"error": str(e)}), 500

@app.route('/check_progress', methods=['GET'])
def check_progress():

	"""
	Check the progress of a Pi calculation task.

	Query Parameters:
		The task ID returned from /calculate_pi

	Returns:
		state, progress, and result
	"""

	task_id = request.args.get('task_id')
	
	if not task_id:
		return jsonify({
			"error": "Missing required parameter 'task_id'",
			"example": "/check_progress?task_id=YOUR_TASK_ID"
		}), 400
	
	task_result = AsyncResult(task_id, app=celery)
	
	if task_result.state == 'SUCCESS':
		response = {
			"state": "FINISHED",
			"progress": 1.0,
			"result": task_result.result
		}
	else:
		response = {
			"state": "PROGRESS",
			"progress": round(task_result.info.get('progress', 0.0), 2) if task_result.info else 0.0,
			"result": None
		}
	
	return jsonify(response)

if __name__ == '__main__':
	app.run(host='0.0.0.0', port=5000, debug=True)
