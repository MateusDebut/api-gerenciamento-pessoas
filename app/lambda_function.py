from flask import Flask, request, jsonify
import boto3
import pymysql
from mangum import Mangum

app = Flask(__name__)
handler = Mangum(app)

def get_db_credentials():
    """Retrieve the database credentials from AWS Secrets Manager"""
    secret_name = "db_secret"
    region_name = "us-east-1"

    # Create a Secrets Manager client
    client = boto3.client('secretsmanager', region_name=region_name)

    try:
        response = client.get_secret_value(SecretId=secret_name)
        secret = response['SecretString']

        # Se o segredo estiver em formato JSON, parse para um dict
        import json
        secret_dict = json.loads(secret)
        return secret_dict

    except Exception as e:
        print(f"Erro ao recuperar secret: {e}")
        return None

def create_connection():
    """Create a connection to the MySQL database using the retrieved credentials"""
    creds = get_db_credentials()
    if creds is None:
        raise Exception("Failed to retrieve database credentials.")

    connection = pymysql.connect(
        host=creds['host'],
        port=creds['port'],
        user=creds['username'],
        password=creds['password'],
        database=creds['dbname'],
        cursorclass=pymysql.cursors.DictCursor
    )

    return connection

@app.route('/create-user', methods=['POST'])
def create_user():
    data = request.get_json()
    username = data.get('username')
    email = data.get('email')

    if not username or not email:
        return jsonify({"error": "Missing required parameters"}), 400

    try:
        connection = create_connection()
        with connection.cursor() as cursor:
            sql = "INSERT INTO users (username, email) VALUES (%s, %s)"
            cursor.execute(sql, (username, email))
        connection.commit()

        return jsonify({"message": "User created successfully"}), 201

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": "Failed to create user"}), 500

    finally:
        connection.close()

def lambda_handler(event, context):
    return handler(event, context)
