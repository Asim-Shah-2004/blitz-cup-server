from flask import Flask, request, jsonify
import requests
import time
import threading

app = Flask(__name__)

def check_problem_solution(handle1, handle2, problem_id):
    """
    Poll Codeforces API to check which user solves a problem first.
    
    Args:
        handle1 (str): First Codeforces handle
        handle2 (str): Second Codeforces handle
        problem_id (str): Problem ID in format "contestId/index" (e.g. "1800/A")
    
    Returns:
        dict: Result containing winner and timing information
    """
    contest_id, problem_index = problem_id.split("/")
    
    
    handle1_solved = False
    handle2_solved = False
    handle1_time = None
    handle2_time = None
    
    poll_interval = 5  
    
    while True:
        
        if not handle1_solved:
            try:
                url1 = f"https://codeforces.com/api/user.status?handle={handle1}"
                response1 = requests.get(url1)
                data1 = response1.json()
                
                if data1["status"] == "OK":
                    submissions = data1["result"]
                    for submission in submissions:
                        if (str(submission["problem"].get("contestId")) == contest_id and 
                            submission["problem"].get("index") == problem_index and 
                            submission["verdict"] == "OK"):
                            handle1_solved = True
                            handle1_time = submission["creationTimeSeconds"]
                            break
            except Exception as e:
                print(f"Error checking {handle1}: {str(e)}")
        
        
        if not handle2_solved:
            try:
                url2 = f"https://codeforces.com/api/user.status?handle={handle2}"
                response2 = requests.get(url2)
                data2 = response2.json()
                
                if data2["status"] == "OK":
                    submissions = data2["result"]
                    for submission in submissions:
                        if (str(submission["problem"].get("contestId")) == contest_id and 
                            submission["problem"].get("index") == problem_index and 
                            submission["verdict"] == "OK"):
                            handle2_solved = True
                            handle2_time = submission["creationTimeSeconds"]
                            break
            except Exception as e:
                print(f"Error checking {handle2}: {str(e)}")
        
        
        if handle1_solved and handle2_solved:
            
            if handle1_time < handle2_time:
                return {
                    "winner": handle1,
                    "loser": handle2,
                    "winner_time": handle1_time,
                    "loser_time": handle2_time,
                    "time_difference": handle2_time - handle1_time
                }
            else:
                return {
                    "winner": handle2,
                    "loser": handle1,
                    "winner_time": handle2_time,
                    "loser_time": handle1_time,
                    "time_difference": handle1_time - handle2_time
                }
        elif handle1_solved:
            return {
                "winner": handle1,
                "loser": handle2,
                "winner_time": handle1_time,
                "loser_time": None,
                "status": f"{handle2} has not solved the problem yet"
            }
        elif handle2_solved:
            return {
                "winner": handle2,
                "loser": handle1,
                "winner_time": handle2_time,
                "loser_time": None,
                "status": f"{handle1} has not solved the problem yet"
            }
        
        
        time.sleep(poll_interval)


active_tracking = {}

@app.route('/start_tracking', methods=['POST'])
def start_tracking():
    data = request.json
    handle1 = data.get('handle1')
    handle2 = data.get('handle2')
    problem_id = data.get('problem_id')
    
    if not handle1 or not handle2 or not problem_id:
        return jsonify({"error": "Missing required parameters"}), 400
    
    
    tracking_id = f"{handle1}_{handle2}_{problem_id}_{int(time.time())}"
    
    
    def tracking_thread():
        result = check_problem_solution(handle1, handle2, problem_id)
        active_tracking[tracking_id] = result
    
    thread = threading.Thread(target=tracking_thread)
    thread.daemon = True
    thread.start()
    
    active_tracking[tracking_id] = {"status": "tracking"}
    
    return jsonify({
        "tracking_id": tracking_id,
        "status": "started",
        "message": f"Now tracking {handle1} vs {handle2} for problem {problem_id}"
    })

@app.route('/check_status/<tracking_id>', methods=['GET'])
def check_status(tracking_id):
    if tracking_id not in active_tracking:
        return jsonify({"error": "Invalid tracking ID"}), 404
    
    return jsonify(active_tracking[tracking_id])

@app.route('/list_tracking', methods=['GET'])
def list_tracking():
    tracking_info = {}
    for track_id, status in active_tracking.items():
        if isinstance(status, dict) and "status" in status and status["stat"] == "tracking":
            parts = track_id.split('_')
            if len(parts) >= 3:
                tracking_info[track_id] = {
                    "handle1": parts[0],
                    "handle2": parts[1],
                    "problem_id": parts[2],
                    "status": "tracking"
                }
        else:
            tracking_info[track_id] = status
    
    return jsonify(tracking_info)

if __name__ == '__main__':
    app.run(debug=True)