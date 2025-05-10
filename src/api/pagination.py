"""
Pagination handling for SonarQube API responses
"""
import logging
from typing import Callable, Dict, List, Any, Optional, Union
import time

logger = logging.getLogger(__name__)


def paginate_api_response(
    get_method: Callable,
    endpoint: str,
    params: Optional[Dict[str, Any]] = None,
    page_size: int = 100,
    max_pages: Optional[int] = None,
    data_field: str = 'components'
) -> List[Dict[str, Any]]:
    """
    Handle pagination for SonarQube API responses
    
    Args:
        get_method: Function to call for getting data
        endpoint: API endpoint
        params: Additional query parameters
        page_size: Number of items per page
        max_pages: Maximum number of pages to fetch
        data_field: Field in response containing the data array
        
    Returns:
        List of all items from all pages
    """
    if params is None:
        params = {}
    
    # Determine the appropriate pagination fields based on the endpoint
    if 'issues/search' in endpoint:
        data_field = 'issues'
        total_field = 'total'
        page_param = 'p'
        page_size_param = 'ps'
    elif 'hotspots/search' in endpoint:
        data_field = 'hotspots'
        total_field = 'paging.total'
        page_param = 'p'
        page_size_param = 'ps'
    else:
        # Default pagination fields
        total_field = 'paging.total'
        page_param = 'p'
        page_size_param = 'ps'
    
    # Set page size in params
    params[page_size_param] = page_size
    
    all_items = []
    page = 1
    total_items = None
    
    while True:
        # Update page parameter
        params[page_param] = page
        
        # Add a delay to avoid hitting rate limits
        if page > 1:
            time.sleep(0.5)
        
        # Make the API request
        logger.debug(f"Fetching page {page} from {endpoint}")
        response = get_method(endpoint, params)
        
        # Extract items from the response
        if isinstance(data_field, str) and '.' in data_field:
            # Handle nested data fields like 'paging.total'
            parts = data_field.split('.')
            items = response
            for part in parts:
                if items and part in items:
                    items = items[part]
                else:
                    items = []
                    break
        else:
            # Handle simple data fields
            items = response.get(data_field, [])
        
        # Add items to the result
        if isinstance(items, list):
            all_items.extend(items)
        
        # Determine total number of items if not known yet
        if total_items is None:
            if '.' in total_field:
                parts = total_field.split('.')
                temp = response
                for part in parts:
                    if temp and part in temp:
                        temp = temp[part]
                    else:
                        temp = None
                        break
                total_items = temp
            else:
                total_items = response.get(total_field, 0)
            
            logger.debug(f"Total items: {total_items}")
        
        # Break if we've reached the maximum number of pages
        if max_pages and page >= max_pages:
            logger.info(f"Reached maximum pages limit ({max_pages}), stopping pagination")
            break
        
        # Determine if there are more pages
        items_count = len(all_items)
        if items_count >= total_items or not items:
            break
        
        # Go to the next page
        page += 1
    
    logger.info(f"Retrieved {len(all_items)} items from {endpoint}")
    return all_items


def chunk_large_response(items: List[Any], chunk_size: int = 1000) -> List[List[Any]]:
    """
    Split a large list of items into smaller chunks for processing
    
    Args:
        items: List of items to chunk
        chunk_size: Size of each chunk
        
    Returns:
        List of chunks
    """
    return [items[i:i + chunk_size] for i in range(0, len(items), chunk_size)]