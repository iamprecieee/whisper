#!/bin/bash

# Exit on error
set -e

# Load .env file
if [ -f .env ]; then
    export $(cat .env | xargs)
fi
 
# Check 'debug' value
DEBUG_VALUE=${DEBUG_VALUE}
SSL_KEYFILE=${SSL_KEYFILE}
SSL_CERTFILE=${SSL_CERTFILE}

collect_static() {
    echo "collecting static files..."
    python manage.py collectstatic --noinput
}

generate_ssl_files() {
    echo "creating ssl files..."
    python ssl_generator.py
}

echo "making and applying migrations..."
python manage.py makemigrations
python manage.py migrate

DEBUG_VALUE_LOWER=$(echo "$DEBUG_VALUE" | tr '[:upper:]' '[:lower:]')

if [ "$DEBUG_VALUE_LOWER" = "false" ]; then
    collect_static
elif [ "$DEBUG_VALUE_LOWER" = "true" ]; then
    generate_ssl_files
fi

# Start appropriate server
case $SERVER_TYPE in
    "daphne")
        echo "starting daphne server..."
        daphne -e ssl:443:privateKey=$SSL_KEYFILE:certKey=$SSL_CERTFILE portal.asgi:application
        ;;
    "gunicorn")
        echo "starting gunicorn server..."
        gunicorn portal.asgi:application -k uvicorn.workers.UvicornWorker -b 0.0.0.0:443 --keyfile $SSL_KEYFILE --certfile $SSL_CERTFILE
        ;;
    "uvicorn")
        echo "starting uvicorn server..."
        uvicorn portal.asgi:application --host 0.0.0.0 --port 443 --reload --ssl-keyfile $SSL_KEYFILE --ssl-certfile $SSL_CERTFILE
        ;;
    "test")
        echo "starting tests..."
        python manage.py test
esac