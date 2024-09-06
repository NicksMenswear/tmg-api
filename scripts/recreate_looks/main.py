import base64
import json
import logging
import os
import uuid
from typing import Dict, Any, List

import requests
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from server.database.models import Look, Attendee

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

API_DATA_BASE_URL = "https://data.prd.tmgcorp.net/"
QUERY_PARAM_SIGNATURE = os.environ["QUERY_PARAM_SIGNATURE"]
API_LOOKS_ENDPOINT = f"https://api.prd.tmgcorp.net/looks?logged_in_customer_id=6680352456746&path_prefix=/apps/prd&shop=themodern-groom.myshopify.com&signature={QUERY_PARAM_SIGNATURE}&timestamp=1718364754"
DB_HOST = "tmg-db-prd-01.cx48ra7hy3wh.us-east-1.rds.amazonaws.com"
DB_NAME = "tmg"
DB_USER = "dbadmin"
DB_PASSWORD = os.environ["DB_PASSWORD"]
DB_URI = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:5432/{DB_NAME}"

db_engine = create_engine(DB_URI)
Session = sessionmaker(bind=db_engine)
session = Session()


def get_look_by_id(look_id) -> Look:
    return session.query(Look).filter(Look.id == look_id).first()


def deactivate_look(look: Look) -> Look:
    look.is_active = False
    session.commit()
    session.refresh(look)
    logger.info(f"Look {look.id} deactivated")
    return look


def download_image_into_b64(image_path) -> str:
    response = requests.get(API_DATA_BASE_URL + image_path)

    if response.status_code == 200:
        return base64.b64encode(response.content).decode("utf-8")

    raise Exception(f"Failed to download image. Status code: {response.status_code}")


def create_new_look_from_broken_look(
    user_id: uuid.UUID, look_name: str, product_specs: Dict[str, Any], image_b64: str
) -> uuid.UUID:
    payload = json.dumps(
        {
            "user_id": str(user_id),
            "name": f"{look_name} Restored",
            "product_specs": product_specs,
            "image": image_b64,
        }
    )
    headers = {"Content-Type": "application/json"}

    response = requests.request("POST", API_LOOKS_ENDPOINT, headers=headers, data=payload)

    return uuid.UUID(response.json().get("id"))


def find_attendees_by_look_id(look_id):
    return session.query(Attendee).filter(Attendee.look_id == look_id).all()


def update_attendees_look(attendees: List[Attendee], look_id: uuid.UUID):
    if not attendees:
        return

    for attendee in attendees:
        attendee.look_id = look_id
        session.commit()
        logger.info(f"Attendee {attendee.id} updated with look_id {look_id}")


def recreate_bundle(look_id, image_path):
    broken_look = get_look_by_id(look_id)
    broken_look = deactivate_look(broken_look)
    image_b64 = download_image_into_b64(image_path)
    restored_look_id = create_new_look_from_broken_look(
        broken_look.user_id, broken_look.name, broken_look.product_specs, image_b64
    )
    attendees = find_attendees_by_look_id(look_id)
    update_attendees_look(attendees, restored_look_id)


def main():
    looks = [
        # (
        #     "174f16d4-78d8-4201-b2e4-c0e791b8e093",
        #     "looks/7ef8433a-6775-43c0-bcbe-8517e8392c2e/174f16d4-78d8-4201-b2e4-c0e791b8e093/1724959611342.png",
        # ),
        (
            "022ff0cd-0bd7-4420-b8d5-26293a14f423",
            "looks/e0ad5098-195c-45b9-af96-af800c8ecff9/022ff0cd-0bd7-4420-b8d5-26293a14f423/1725463556621.png",
        ),
        (
            "2fbe5f66-730a-4286-924e-01c7b84db8fc",
            "looks/a0217e09-2458-48b7-9e45-1f9e73802fd2/2fbe5f66-730a-4286-924e-01c7b84db8fc/1725483766507.png",
        ),
        (
            "3effca9d-83aa-4397-9220-dc652c7ec897",
            "looks/e0ad5098-195c-45b9-af96-af800c8ecff9/3effca9d-83aa-4397-9220-dc652c7ec897/1725465532728.png",
        ),
        (
            "3fef65a0-8754-4fd3-9607-d7b7dddb9b3d",
            "looks/808e607c-4f48-42f2-b014-f2c8858a629a/3fef65a0-8754-4fd3-9607-d7b7dddb9b3d/1725497786075.png",
        ),
        (
            "406bb628-53ee-411b-8043-f224397ac795",
            "looks/808e607c-4f48-42f2-b014-f2c8858a629a/406bb628-53ee-411b-8043-f224397ac795/1725498043558.png",
        ),
        (
            "7f000ddb-8107-485c-961e-dfe3ff031510",
            "looks/350f1301-f1a0-4cdc-9242-39a3cdc7d6d7/7f000ddb-8107-485c-961e-dfe3ff031510/1725501943140.png",
        ),
        (
            "bec33eca-ebb8-40d7-97fb-73bc82e64002",
            "looks/3be45dbd-73d3-4c46-ad2f-51ed5c624bd1/bec33eca-ebb8-40d7-97fb-73bc82e64002/1725468019900.png",
        ),
    ]
    for look_id, image_path in looks:
        recreate_bundle(look_id, image_path)


if __name__ == "__main__":
    main()
