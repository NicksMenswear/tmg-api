.PHONY: help run db api api-py down deploy tail

#
# Local Stack
#
run:
	docker-compose up --build

db:
	docker-compose up -d db

api:
	docker-compose up --build api

py:
	cd server && python openapi_server/app.py

clean:
	docker-compose down -v

#
# AWS Stack
#
deploy:
	sls deploy

tail:
	sls logs --function api --tail
