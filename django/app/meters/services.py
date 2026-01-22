import requests
from django.conf import settings


class SekouApiClient:
    def __init__(self):
        self.base_url = settings.SEKOU_API_URL
        self.api_key = settings.SEKOU_API_KEY
    
    @property
    def is_configured(self):
        return bool(self.base_url and self.api_key)
    
    def get_customer(self, customer_id):
        if not self.is_configured:
            return None, 'API未設定'
        
        try:
            r = requests.get(
                f'{self.base_url}/customer/{customer_id}/',
                headers={'X-API-Key': self.api_key},
                timeout=10
            )
            if r.status_code == 200:
                return r.json(), None
            elif r.status_code == 404:
                return None, '案件が見つかりません'
            else:
                return None, f'APIエラー ({r.status_code})'
        except Exception as e:
            return None, str(e)
    
    def search_customers(self, search=''):
        if not self.is_configured:
            return [], 'API未設定'
        
        print(self.base_url)
        try:
            r = requests.get(
                f'{self.base_url}/customers/',
                headers={'X-API-Key': self.api_key},
                params={'search': search} if search else {},
                timeout=10
            )
            if r.status_code == 200:
                return r.json().get('items', []), None
            else:
                return [], f'APIエラー ({r.status_code})'
        except Exception as e:
            return [], str(e)