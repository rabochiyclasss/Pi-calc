# Pi-calc
An asynchronous Pi calculation service using Flask, Celery, and Redis

1. Clone or download all files to a directory
2. Run the following command:
   docker-compose up --build
3. Access the API at http://localhost:5000

Root Endpoint: GET / returns API documentation in JSON format
	Example:
	curl http://localhost:5000/

Calculate Pi: GET /calculate_pi
	Starts an asynchronous Pi calculation task.
	Parameters:
	n (required): Number of decimal places to calculate (1-10000)
	Example:
	curl "http://localhost:5000/calculate_pi?n=123"
	Response:
	json{
	  "task_id": "550e8400-e29b-41d4-a716-446655440000",
	  "status": "Task started",
	  "message": "Calculating Pi to 123 decimal places"		
	}

Check Progress: GET /check_progress
	Checks the progress of a running calculation task.
	Parameters:
	task_id (required): Task ID returned from /calculate_pi
	Example:
	curl "http://localhost:5000/check_progress?task_id=550e8400-e29b-41d4-a716-446655440000"
	Response (In Progress):
	json{
	  "state": "PROGRESS",
	  "progress": 0.4,
	  "result": null
	}
	Response (Completed):
	json{
	  "state": "FINISHED",
	  "progress": 1.0,
	  "result": "3.141592653589793238462643383279502884197..."
	}
