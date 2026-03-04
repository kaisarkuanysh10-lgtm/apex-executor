from flask import Flask, request

app = Flask(__name__)

@app.route('/')
def get_ip():
    # Егер хакер Proxy қолданса, шын IP 'X-Forwarded-For' ішінде болуы мүмкін
    if request.headers.getlist("X-Forwarded-For"):
        real_ip = request.headers.getlist("X-Forwarded-For")[0]
    else:
        real_ip = request.remote_addr
        
    user_agent = request.headers.get('User-Agent')
    print(f"--- ЖАҢА КЕЛУШІ АНЫҚТАЛДЫ ---")
    print(f"IP: {real_ip}")
    print(f"Құрылғы: {user_agent}")
    return f"Сенің IP-ің анықталды: {real_ip}"

if __name__ == "__main__":
    app.run(port=8080)
