import json
import logging
from bs4 import BeautifulSoup
import requests


def get_html_data(gdc_id):
    session = requests.Session()
    session.post(
        "https://services.gdc.ga.gov/GDC/OffenderQuery/jsp/OffQryForm.jsp?vDisclaimer=True",
    )
    response = session.post(
        f"https://services.gdc.ga.gov/GDC/OffenderQuery/jsp/OffQryRedirector.jsp?NextPage=2&vUnoCaseNoRadioButton=UNO_NO&vOffenderId={gdc_id}",
    )
    return response.text


def extract_incarceration_details(data):
    soup = BeautifulSoup(data, "html.parser")

    details = {
        "name": None,
        "most_recent_institution": None,
        "max_possible_release_date": None,
        "actual_release_date": None,
        "current_status": None,
    }

    for tag in soup.find_all("strong", class_="offender"):
        text = tag.text.strip()
        if text == "MOST RECENT INSTITUTION:":
            details["most_recent_institution"] = tag.next_sibling.strip()
        elif text == "MAX POSSIBLE RELEASE DATE:":
            details["max_possible_release_date"] = tag.next_sibling.strip()
        elif text == "ACTUAL RELEASE DATE:":
            details["actual_release_date"] = tag.next_sibling.strip()
        elif text == "CURRENT STATUS:":
            details["current_status"] = tag.next_sibling.strip()

    for tag in soup.find_all("h4"):
        text = tag.text.strip()
        if text.startswith("NAME:"):
            details["name"] = text.removeprefix("NAME:").strip()
            break

    return details


def handler(event, context):
    try:
        # Assuming the HTML content is passed in the body of the request
        gdc_id = event["queryStringParameters"].get("gdc_id")
        if not gdc_id:
            return {
                "statusCode": 400,
                "body": json.dumps(
                    {"error": "Must include 'gdc_id' query parameter in request"}
                ),
            }

        html_data = get_html_data(gdc_id)
        result = extract_incarceration_details(html_data)

        return {"statusCode": 200, "body": json.dumps(result)}

    except Exception as e:
        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}
