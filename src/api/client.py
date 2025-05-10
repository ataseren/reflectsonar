"""
SonarQube API Client
Handles communication with the SonarQube API
"""
import requests
import base64
import time
from urllib.parse import urljoin
import logging
from .pagination import paginate_api_response

logger = logging.getLogger(__name__)


class SonarQubeClient:    
    def __init__(self, base_url, token=None, username=None, password=None, 
                 timeout=30, verify_ssl=True, max_retries=3, retry_delay=1):

        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.verify_ssl = verify_ssl
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.session = requests.Session()
        
        # Set authentication
        if token:
            self.session.auth = (token, '')
        elif username and password:
            auth_str = f"{username}:{password}"
            encoded_auth = base64.b64encode(auth_str.encode()).decode()
            self.session.headers.update({'Authorization': f'Basic {encoded_auth}'})
        
        # Set common headers
        self.session.headers.update({
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        })
    
    def _request(self, method, endpoint, params=None, data=None, stream=False):

        url = urljoin(self.base_url, endpoint)
        retries = 0
        
        while retries <= self.max_retries:
            try:
                response = self.session.request(
                    method=method,
                    url=url,
                    params=params,
                    json=data,
                    timeout=self.timeout,
                    verify=self.verify_ssl,
                    stream=stream
                )
                
                if response.status_code == 429:  # Rate limit exceeded
                    retry_after = int(response.headers.get('Retry-After', self.retry_delay))
                    logger.warning(f"Rate limit exceeded. Retrying after {retry_after} seconds.")
                    time.sleep(retry_after)
                    retries += 1
                    continue
                
                # Handle other potential errors
                response.raise_for_status()
                
                if stream:
                    return response
                return response.json() if response.content else {}
                
            except requests.RequestException as e:
                if retries < self.max_retries:
                    logger.warning(f"Request failed: {str(e)}. Retrying ({retries+1}/{self.max_retries})...")
                    time.sleep(self.retry_delay)
                    retries += 1
                else:
                    return handle_api_error(e, url)
    
    def get(self, endpoint, params=None, stream=False):
        return self._request('GET', endpoint, params=params, stream=stream)
    
    def post(self, endpoint, params=None, data=None):
        return self._request('POST', endpoint, params=params, data=data)
    
    def get_paginated(self, endpoint, params=None, page_size=100, max_pages=None):
        return paginate_api_response(
            self.get, 
            endpoint, 
            params=params, 
            page_size=page_size, 
            max_pages=max_pages
        )
    
    # API endpoints
    
    def get_project(self, project_key):
        return self.get('api/components/show', {'component': project_key})
    
    def get_project_issues(self, project_key, additional_params=None):
        params = {'componentKeys': project_key, 'ps': 500}
        if additional_params:
            params.update(additional_params)
        return self.get_paginated('api/issues/search', params)
    
    def get_project_measures(self, project_key, metrics):
        return self.get('api/measures/component', {
            'component': project_key,
            'metricKeys': ','.join(metrics)
        })
    
    def get_project_hotspots(self, project_key):
        return self.get_paginated('api/hotspots/search', {'projectKey': project_key})
    
    def get_quality_profiles(self, project_key):
        return self.get('api/qualityprofiles/search', {'project': project_key})
    
    def get_quality_gates(self, project_key):
        return self.get('api/qualitygates/get_by_project', {'project': project_key})