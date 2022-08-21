from square.client import Client
import uuid

def make_idemp_key():
    return str(uuid.uuid4())


def create_checkout_link(access_token, location_id, ticket_name, quantity, unit_price, redirect_url,currency='USD'):
    print(currency)
    if not currency:
        currency = "USD"
    client = Client(
        access_token=access_token,
        environment='sandbox')
    result = client.checkout.create_checkout(
    location_id = location_id,
    body = {
        "idempotency_key": make_idemp_key(),
        "order": {
        "order": {
            "location_id": location_id,
            "line_items": [
            {
                "name": ticket_name,
                "quantity": quantity,
                "base_price_money": {
                "amount": unit_price,
                "currency": currency
                }
            }
            ]
        },
        "idempotency_key": make_idemp_key()
        },
        "redirect_url": redirect_url
    }
    )
    return result


def obtain_oauth(access_token,own_client_id, own_secret, code, grant_type="authorization_code"):
    client = Client(
        access_token=access_token,
        environment='sandbox')


    result = client.o_auth.obtain_token(
        body = {
            "client_id": own_client_id,
            "client_secret": own_secret,
            "code": code,
            "grant_type": grant_type
        }
    )

    if result.is_success():
        print(result.body)
        return result
    elif result.is_error():
        return result
        print(result.errors)