import os

from app import create_app

app = create_app()

if __name__ == '__main__':
    port = int(os.getenv('PORT', '').strip() or 5000)
    app.run(debug=app.config['DEBUG'], port=port)
