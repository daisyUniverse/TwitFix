from twitfix import app

if __name__ == "__main__":
    # listen on 0.0.0.0 to facilitate testing with real services
    app.run(host='0.0.0.0')