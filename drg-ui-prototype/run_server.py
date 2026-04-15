import webbrowser

HOST = "127.0.0.1"
PORT = 5000


if __name__ == "__main__":
    try:
        from app import app
    except ModuleNotFoundError as error:
        if error.name == "flask":
            print("缺少依赖 Flask，请先执行: pip install -r requirements.txt")
            raise
        raise

    url = f"http://{HOST}:{PORT}"
    print(f"Flask app running at {url}")
    webbrowser.open(url)
    app.run(host=HOST, port=PORT, debug=True)
