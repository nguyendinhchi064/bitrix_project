import json
import requests
import logging
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.db import IntegrityError
from django.shortcuts import render
from datetime import timedelta
from .models import BitrixToken


def oauth_status(request):
    return HttpResponse("Bitrix24 OAuth server is running.")
# --- INSTALL APP WEBHOOK ---
@csrf_exempt
def install_app(request):
    print("[Install] Nhận request từ Bitrix24")

    if request.method == 'POST':
        try:
            domain = request.GET.get('DOMAIN') or request.POST.get('DOMAIN')
            access_token = request.POST.get('AUTH_ID')  # AUTH_ID là access_token
            refresh_token = request.POST.get('REFRESH_ID')  # REFRESH_ID là refresh_token
            expires_in = int(request.POST.get('expires_in', 3600))  

            print(f"DOMAIN: {domain}")
            print(f"ACCESS_TOKEN: {access_token}")
            print(f"REFRESH_TOKEN: {refresh_token}")

            expires_at = timezone.now() + timedelta(seconds=expires_in)

            token, created = BitrixToken.objects.update_or_create(
                domain=domain,
                defaults={
                    'access_token': access_token,
                    'refresh_token': refresh_token,
                    'expires_in': expires_in,
                    'expires_at': expires_at,
                }
            )

            print(f"Token {'created' if created else 'updated'} cho {domain}")
            return JsonResponse({"message": "Token saved", "created": created})
        except Exception as e:
            print("Lỗi khi xử lý install:", str(e))
            return JsonResponse({"error": str(e)}, status=400)

# --- REFRESH TOKEN ---
def refresh_token_for_domain(domain):
    try:
        # Retrieve token from the database
        token = BitrixToken.objects.get(domain=domain)

        # Make a request to Bitrix24 to refresh the token
        refresh_url = f"https://{domain}/oauth/token/"
        params = {
            'client_id': 'local.67ee7ef2bc7f13.87412876',  # Must match with local application
            'client_secret': 'Txp5ZfcqDz8zDv06Vv4zdeM954H5pro1ERfE3qy1UKkp66vwc6', # This too
            'refresh_token': token.refresh_token,
            'grant_type': 'refresh_token'
        }

        # Send the request to refresh the token
        response = requests.post(refresh_url, data=params)
        
        # Log the entire response for debugging
        print(f"Response status code: {response.status_code}")
        print(f"Response content: {response.text}")

        response_data = response.json()

        if response.status_code == 200:
            # If the refresh is successful, save the new access token in the database
            access_token = response_data.get('access_token')
            if not access_token:
                raise ValueError("Missing access_token in response")

            token.access_token = access_token
            token.expires_in = response_data.get('expires_in')

            # Handle 'expires_in' safely
            expires_in = response_data.get('expires_in')
            if expires_in is not None:
                token.expires_at = timezone.now() + timezone.timedelta(seconds=expires_in)
            else:
                # Set a default expiration time (e.g., 1 hour from now) if 'expires_in' is missing
                token.expires_at = timezone.now() + timezone.timedelta(hours=1)

            # Save token in the database
            token.save()
            return token  # Return the refreshed token
        else:
            # Log the error if the status code is not 200
            print(f"Error refreshing token: {response_data}")
            return None

    except BitrixToken.DoesNotExist:
        # Return None if the token doesn't exist in the database
        print(f"Token not found for domain: {domain}")
        return None
    except IntegrityError as e:
        # Handle database errors (e.g., NOT NULL constraint failure)
        print(f"Database error while saving token: {str(e)}")
        return None
    except Exception as e:
        # Catch any other exceptions (e.g., network issues, JSON parsing errors)
        print(f"An error occurred while refreshing the token: {str(e)}")
        return None


# --- GET VALID TOKEN ---
def get_valid_token(domain):
    try:
        # Retrieve token from the database
        token = BitrixToken.objects.get(domain=domain)

        # Check if the token has expired
        if token.is_expired():
            # Refresh the token if it has expired
            token = refresh_token_for_domain(domain)
            if not token:
                return None  # Token could not be refreshed

        return token

    except BitrixToken.DoesNotExist:
        return None  # Return None if the token doesn't exist


# --- CALL API --- use to check what bitrix24 send
@csrf_exempt
def call_api(request):
    if request.method != 'POST':
        return JsonResponse({"error": "Only POST allowed"}, status=405)

    try:
        data = json.loads(request.body)
        domain = data['domain']
        action = data.get('action', 'user.current')
        payload = data.get('payload', {})

        token = get_valid_token(domain)
        if not token:
            return JsonResponse({"error": "Token not found or invalid"}, status=401)

        print("Sử dụng token:", token.access_token)

        url = f"https://{domain}/rest/{action}"
        res = requests.post(url, json=payload, params={'auth': token.access_token}, timeout=10)

        if res.status_code == 401:
            print("Token có thể đã hết hạn. Đang thử refresh...")
            token = refresh_token_for_domain(domain)
            if not token:
                return JsonResponse({"error": "Token refresh failed"}, status=401)

            res = requests.post(url, json=payload, params={'auth': token.access_token}, timeout=10)

        print("Response từ Bitrix:", res.status_code, res.text)
        return JsonResponse(res.json(), safe=False)

    except requests.exceptions.Timeout:
        return JsonResponse({"error": "Request timed out"}, status=504)
    except requests.exceptions.RequestException as e:
        return JsonResponse({"error": f"Request error: {str(e)}"}, status=500)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)

# --- OPTIONAL: DUMMY WEBHOOK ---
@csrf_exempt
def webhook(request):
    return JsonResponse({"message": "Webhook received."})

# --- Contact logic --- 
import requests
from django.conf import settings


# Function to get contacts from Bitrix24
def get_bitrix_contacts(domain, access_token):
    url = f"https://{domain}/rest/crm.contact.list.json"
    
    # Set the authorization header with the access token
    headers = {
        'Authorization': f'Bearer {access_token}'  # Authorization header with token
    }

    # Remove the 'order' parameter for now to see if it works without sorting
    params = {
        'start': 0, 
        'select': ['ID', 'NAME', 'PHONE', 'EMAIL', 'ADDRESS']  # Select specific fields
    }

    # Send the GET request to the Bitrix24 API
    response = requests.get(url, headers=headers, params=params)

    print(f"Response Status Code: {response.status_code}")
    print(f"Response Body: {response.text}")  # Log the response text for debugging
    
    if response.status_code == 200:
        return response.json()  # Successfully fetched contacts
    else:
        return {"error": "Failed to fetch contacts", "status_code": response.status_code, "details": response.text}

def contact_list(request):
    domain = 'nguyendinhchi.bitrix24.vn'
    token = get_valid_token(domain)  
    if not token:
        return JsonResponse({"error": "Token not found or expired"}, status=401)
    
    access_token = token.access_token
    contacts_data = get_bitrix_contacts(domain, access_token)
    
    if 'error' in contacts_data:
        return JsonResponse(contacts_data, status=contacts_data.get('status_code', 400))
    
    contacts = contacts_data.get('result', [])
    return render(request, 'contacts/contact_list.html', {'contacts': contacts})

import requests

def contact_form(request):
    return render(request, 'contacts/contact_form.html')

logger = logging.getLogger(__name__)
@csrf_exempt  
def create_contact(request):
    if request.method == 'POST':
        name = request.POST.get('NAME')
        phone = request.POST.get('PHONE')
        email = request.POST.get('EMAIL')
        address_1 = request.POST.get('ADDRESS[ADDRESS_1]')
        city = request.POST.get('ADDRESS[CITY]')
        postal_code = request.POST.get('ADDRESS[POSTAL_CODE]')
        province = request.POST.get('ADDRESS[PROVINCE]')
        country = request.POST.get('ADDRESS[COUNTRY]')
        country_code = request.POST.get('ADDRESS[COUNTRY_CODE]')
        website = request.POST.get('WEBSITE', '')  
        bank_name = request.POST.get('BANK_NAME')
        bank_account = request.POST.get('BANK_ACCOUNT')

        phone = [{"VALUE": phone, "VALUE_TYPE": "WORK"}] if phone else []
        email = [{"VALUE": email, "VALUE_TYPE": "HOME"}] if email else []
        website = [{"VALUE": website, "VALUE_TYPE": "WORK"}] if website else [] 
        address = {
            "ADDRESS_1": address_1,
            "CITY": city,
            "POSTAL_CODE": postal_code,
            "PROVINCE": province,
            "COUNTRY": country,
            "COUNTRY_CODE": country_code
        }

        bitrix_url = "https://nguyendinhchi.bitrix24.vn/rest/1/2re84pxix0c4j70l/"
        data = {
            "FIELDS": {
                "NAME": name,
                "PHONE": phone,
                "EMAIL": email,
                "ADDRESS": address, 
                "WEBSITE": website,
                "BANK_NAME": bank_name,
                "BANK_ACCOUNT": bank_account
            }
        }

        print("Data being sent to Bitrix24: ", data)

        response = requests.post(f'{bitrix_url}crm.contact.add.json', json=data) 

        try:
            json_response = response.json()
            contact_id = json_response.get('data')
            if contact_id:
                return JsonResponse({"message": "Contact added successfully", "contact_id": contact_id})
            else:
                return JsonResponse({"error": "No contact ID returned"})
        except ValueError:
            return JsonResponse({"error": "Failed to decode JSON response from Bitrix24"})

@csrf_exempt
def update_contact(request, pk):
    if request.method == 'POST':
        # Retrieve data from the form
        name = request.POST.get('NAME') 
        phone = request.POST.get('PHONE')
        email = request.POST.get('EMAIL')
        address_1 = request.POST.get('ADDRESS[ADDRESS_1]')
        city = request.POST.get('ADDRESS[CITY]')
        postal_code = request.POST.get('ADDRESS[POSTAL_CODE]')
        website = request.POST.get('WEBSITE', '')  # Get website if provided
        bank_name = request.POST.get('BANK_NAME')
        bank_account = request.POST.get('BANK_ACCOUNT')
        contact_id = pk
        if not contact_id:
            return JsonResponse({"error": "Missing contact_id"}, status=400)
        
        # Format phone and email for Bitrix24 API
        phone = [{"VALUE": phone, "VALUE_TYPE": "WORK"}] if phone else []
        email = [{"VALUE": email, "VALUE_TYPE": "HOME"}] if email else []
        website = [{"VALUE": website, "VALUE_TYPE": "WORK"}] if website else []
        address = {
            "ADDRESS_1": address_1,
            "CITY": city,
            "POSTAL_CODE": postal_code
        }

        # Bitrix24 API URL for updating contact
        bitrix_url = "https://nguyendinhchi.bitrix24.vn/rest/1/qsu15u6m9cs7nsmx/"
        data = {
            "FIELDS": {
                "NAME": name,
                "PHONE": phone,
                "EMAIL": email,
                "ADDRESS": address,
                "WEBSITE": website,
                "BANK_NAME": bank_name,
                "BANK_ACCOUNT": bank_account
            },
            "ID": contact_id  # ID of the contact to update
        }

        # Send PUT request (update) to Bitrix24 API
        response = requests.post(f'{bitrix_url}crm.contact.update.json', json=data)

        # Check and return the response from Bitrix24
        try:
            json_response = response.json()
            if json_response.get('data'):
                return JsonResponse({"message": "Contact updated successfully", "contact_id": contact_id})
            else:
                return JsonResponse({"error": "Failed to update contact"})
        except ValueError:
            return JsonResponse({"error": "Failed to decode JSON response from Bitrix24"})
    return JsonResponse({"error": "Invalid request method. Only POST allowed."}, status=405)

def contact_update_form(request):
    return render(request, 'contacts/update_contact_form.html')

@csrf_exempt
def contact_delete(request, pk):
    if request.method == 'POST':
        contact_id = pk  # The contact ID is already part of the URL
        
        if not contact_id:
            return JsonResponse({"error": "Missing contact_id"}, status=400)

        # Prepare the request to delete the contact from Bitrix24
        bitrix_url = f"https://nguyendinhchi.bitrix24.vn/rest/1/ikmt7yhx6ird0s9x/"  # Ensure your Bitrix24 client_id is correct

        # Make the request to delete the contact
        response = requests.post(f'{bitrix_url}crm.contact.delete.json', json={"ID": contact_id})

        if response.status_code == 200:
            return JsonResponse({"message": "Contact deleted successfully!"})
        else:
            error_message = response.json().get("error_description", "Unknown error")
            return JsonResponse({"error": f"Failed to delete contact from Bitrix24. Error: {error_message}"}, status=400)

    return JsonResponse({"error": "Invalid request method. Only POST allowed."}, status=405)

def contact_delete_form(request):
    return render(request, 'contacts/contact_confirm_delete.html')