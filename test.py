from FlaskMetrics import FlaskMetrics
from flask import Flask,render_template,jsonify,request

app = Flask(__name__)

fm = FlaskMetrics()


def bd(request):
    
    r = {}
    
    r["URL"] = request.path
    r["BROWSER"] = request.user_agent.browser
    r["ACCEPT_LANGUAGES"] = request.accept_languages
    r["IP_ADDR"] = request.remote_addr
    
    
    return r

fm.build_dict = bd


@app.route("/")
def home():
    
    try:
        fm.store_visit(request)
    except Exception as e:
        return jsonify({"error":str(e)})
    
    
    return jsonify({"visits_count":fm.get_visits_count(days=4,distinct=True)})







if __name__ == "__main__":
      
    app.run(host="0.0.0.0",debug=True)

